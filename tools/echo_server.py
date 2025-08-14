"""
This is what runs behind each transducer in the Garden.
"""

import argparse
import base64
import socket
import ssl
import threading
import urllib.parse

from queue import SimpleQueue
from ssl import SSLContext
from typing import Callable

from util import recvall, sendall, is_closed_for_reading, is_closed_for_writing, roundtrip_to_client

SOCKET_TIMEOUT = 0.1

pcap_connected: bool = False
pcap_queue: SimpleQueue[tuple[str, int, bytes]] = SimpleQueue()
h1_dummy_payload: bytes = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{}"


def recvall_and_queue(sock: socket.socket) -> bytes:
    result = recvall(sock)
    if pcap_connected:
        host, port = sock.getpeername()
        pcap_queue.put((host, port, result))
    return result


def handle_dummy_h1_connection(sock: socket.socket, _bytes_recved: bytes) -> None:
    roundtrip_to_client(sock, h1_dummy_payload, recv_callback=recvall_and_queue)
    sock.close()


def handle_dummy_h2_connection(_sock: socket.socket, _bytes_recved: bytes) -> None:
    pass


def handle_dummy_connection(client_sock: socket.socket) -> None:
    preamble: bytes = recvall_and_queue(client_sock)
    if preamble.startswith(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"):
        handle_dummy_h2_connection(client_sock, preamble)
    else:
        handle_dummy_h1_connection(client_sock, preamble)


def do_forking_server(
        url: urllib.parse.ParseResult, keyfile: str | None, certfile: str | None, alpn_list: list[str], target: Callable[[socket.socket], None]
) -> None:
    context: SSLContext | None = None
    if keyfile is not None and certfile is not None:
        context = SSLContext(ssl.PROTOCOL_TLS)
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        if alpn_list:
            context.set_alpn_protocols(alpn_list)

    server_sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((url.hostname, url.port))
    server_sock.listen()
    while True:
        client_sock, _ = server_sock.accept()
        client_sock.settimeout(SOCKET_TIMEOUT)
        if context is not None:
            client_sock = context.wrap_socket(client_sock, server_side=True)
        threading.Thread(target=target, args=(client_sock,)).start()


def handle_pcap_connection(sock: socket.socket) -> None:
    if not is_closed_for_reading(sock):
        global h1_dummy_payload
        h1_dummy_payload = base64.b64decode(recvall(sock))
        return

    global pcap_connected
    pcap_connected = True
    while True:
        if is_closed_for_writing(sock):
            break
        hostname, port, bytes_recved = pcap_queue.get()
        try:
            sendall(
                sock,
                b":".join(
                    (
                        base64.b64encode(hostname.encode("ascii")),
                        base64.b64encode(str(port).encode("ascii")),
                        base64.b64encode(bytes_recved),
                    )
                ) + b"\n",
            )
        except (ConnectionResetError, BrokenPipeError):
            break
        if pcap_queue.empty():
            break
    sock.close()
    pcap_connected = False

def main() -> None:
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="This is what runs behind each transducer in the Garden.",
    )
    arg_parser.add_argument(
        "--host-url",
        default="http://0.0.0.0:56062",
        help="bind to this address",
    )
    arg_parser.add_argument(
        "--pcap-url",
        default="http://127.0.0.1:55838",
        help="bind to this address for the pcap channel",
    )
    arg_parser.add_argument(
        "--certfile", help="the TLS certificate (only needed if using https in host-url or pcap-url)"
    )
    arg_parser.add_argument(
        "--keyfile", help="the TLS key (only needed if using https in host-url or pcap-url)"
    )
    arg_parser.add_argument(
        "--alpn-list", help="comma-separated list of protocols to be used in ALPN."
    )

    args: argparse.Namespace = arg_parser.parse_args()

    threading.Thread(
        target=do_forking_server,
        args=(
            urllib.parse.urlparse(args.host_url),
            args.keyfile,
            args.certfile,
            (args.alpn_list or "").split(","),
            handle_dummy_connection,
        ),
    ).start()
    threading.Thread(
        target=do_forking_server,
        args=(
            urllib.parse.urlparse(args.pcap_url),
            args.keyfile,
            args.certfile,
            (args.alpn_list or "").split(","),
            handle_pcap_connection,
        ),
    ).start()


if __name__ == "__main__":
    main()
