import socket
import ssl
import sys
import threading

from ssl import SSLContext
from typing import Final

import http2

from hpack import HPACKString, HPACKLiteralHeaderField
from http2 import H2Frame, H2GenericFrame, H2DataFrame, H2HeadersFrame, H2SettingsFrame, H2PingFrame, H2FrameType
from util import recvall, sendall

SOCKET_TIMEOUT = 0.1


def send_frames(frames: list[H2Frame], sock: socket.socket) -> None:
    sendall(sock, b"".join(frame.to_bytes() for frame in frames))

def handle_h1_connection(client_sock: socket.socket, bytes_recved: bytes) -> None:
    while True:
        if len(bytes_recved) == 0:
            break
        sendall(
            client_sock,
            f"HTTP/1.1 200 OK\r\nCache-Control: public, max-age=2592000\r\nServer: echo-python\r\nContent-Length: {len(bytes_recved)}\r\n\r\n".encode("ascii") + bytes_recved
        )
        bytes_recved = recvall(client_sock)
    client_sock.close()


frame_counter: int = 0
def collect_frame(collected_frames: dict[int, list[tuple[int, H2GenericFrame]]], frame: H2GenericFrame) -> None:
    global frame_counter
    if frame.stream_id not in collected_frames:
        collected_frames[frame.stream_id] = []
    collected_frames[frame.stream_id].append((frame_counter, frame))
    frame_counter += 1

def close_stream(stream_id: int, collected_frames: dict[int, list[tuple[int, H2GenericFrame]]], streams_ending: set[int]) -> None:
    del collected_frames[stream_id]
    if stream_id in streams_ending:
        streams_ending.remove(stream_id)


def respond_and_close_stream(client_sock: socket.socket, stream_id: int, collected_frames: dict[int, list[tuple[int, H2GenericFrame]]], streams_ending: set[int]) -> None:
    assert stream_id in collected_frames
    relevant_frames: list[tuple[int, H2GenericFrame]] = collected_frames[stream_id].copy()
    if 0 in collected_frames:
        relevant_frames.extend(collected_frames[0])
    relevant_frames.sort(key=lambda t: t[0])

    send_frames(
        [
            H2HeadersFrame(
                end_stream=False,
                stream_id=stream_id,
                field_block_fragment=HPACKLiteralHeaderField(HPACKString(b":status"), HPACKString(b"200")).to_bytes()
            ),
            H2DataFrame(
                end_stream=True,
                stream_id=stream_id,
                data=b"".join(frame.to_bytes() for _, frame in relevant_frames)
            ),
        ],
        client_sock,
    )
    close_stream(stream_id, collected_frames, streams_ending)


def handle_h2_connection(client_sock: socket.socket, bytes_recved: bytes) -> None:
    streams_ending: set[int] = set()
    collected_frames: dict[int, list[tuple[int, H2GenericFrame]]] = {}

    sendall(client_sock, H2SettingsFrame().to_bytes())

    while True:
        if len(bytes_recved) == 0:
            break
        frames: list[H2GenericFrame] = http2.parse_generic_frames(bytes_recved)
        for frame in frames:
            stream_id: int = frame.stream_id
            match frame.typ:
                case H2FrameType.DATA:
                    collect_frame(collected_frames, frame)
                    if frame.flags.end_stream_or_ack:
                        respond_and_close_stream(client_sock, stream_id, collected_frames, streams_ending)
                case H2FrameType.HEADERS:
                    collect_frame(collected_frames, frame)
                    if frame.flags.end_headers and frame.flags.end_stream_or_ack:
                        respond_and_close_stream(client_sock, stream_id, collected_frames, streams_ending)
                    elif frame.flags.end_stream_or_ack:
                        streams_ending.add(stream_id)
                case H2FrameType.PRIORITY | H2FrameType.WINDOW_UPDATE:
                    pass
                case H2FrameType.RST_STREAM:
                    close_stream(stream_id, collected_frames, streams_ending)
                case H2FrameType.SETTINGS:
                    collect_frame(collected_frames, frame)
                    if not frame.flags.end_stream_or_ack:
                        sendall(client_sock, H2SettingsFrame(ack=True).to_bytes())
                case H2FrameType.PING:
                    if not frame.flags.end_stream_or_ack:
                        sendall(client_sock, H2PingFrame(ack=True, opaque_data=frame.payload[:8]).to_bytes())
                case H2FrameType.GOAWAY:
                    return
                case H2FrameType.CONTINUATION:
                    collect_frame(collected_frames, frame)
                    if frame.flags.end_headers and frame.stream_id in streams_ending:
                        respond_and_close_stream(client_sock, frame.stream_id, collected_frames, streams_ending)
                case _: # PUSH_PROMISE | unrecognized type
                    collect_frame(collected_frames, frame)

        bytes_recved = recvall(client_sock)


H2_PREFACE: Final[bytes] = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"

def handle_connection(client_sock: socket.socket) -> None:
    client_sock.settimeout(SOCKET_TIMEOUT)
    preamble: bytes = recvall(client_sock)
    if preamble.startswith(H2_PREFACE):
        handle_h2_connection(client_sock, preamble[len(H2_PREFACE):])
    else:
        handle_h1_connection(client_sock, preamble)


def main() -> None:
    if len(sys.argv) not in (3, 4):
        print(f"Usage: python3 {sys.argv[0]} <host> <port> [certfile]")
    host: str = sys.argv[1]
    port: int = int(sys.argv[2])
    certfile: str | None = sys.argv[3] if len(sys.argv) > 3 else None

    server_sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((host, port))
    server_sock.listen()

    context: SSLContext | None = None
    if certfile is not None:
        context = SSLContext(ssl.PROTOCOL_TLS)
        context.load_cert_chain(certfile=certfile)
        context.set_alpn_protocols(["h2"])

    while True:
        client_sock, _ = server_sock.accept()
        if certfile is not None:
            assert context is not None
            client_sock = context.wrap_socket(client_sock, server_side=True)
        t: threading.Thread = threading.Thread(target=handle_connection, args=(client_sock,))
        t.start()

if __name__ == "__main__":
    main()
