"""The Garden repl"""

import itertools
import shlex
import sys
from typing import TypeGuard, Any, Iterable

from diff import ErrorType
from fanout import (
    fanout,
    unparsed_fanout,
)
from grid import generate_grid, Grid, generate_clusters, Clusters
from http1 import HTTPRequest, HTTPResponse
from http2 import H2FrameType, H2Flags, H2GenericFrame, H2Frame
from targets import ORIGIN_DICT, TRANSDUCER_DICT, Server
from util import list_split, safe_next

def print_request(r: HTTPRequest) -> None:
    print("    \x1b[0;34mHTTPRequest\x1b[0m(")  # Blue
    print(f"        method={r.method!r}, uri={r.uri!r}, version={r.version!r},")
    if len(r.headers) == 0:
        print("        headers=[],")
    else:
        print("        headers=[")
        for name, value in r.headers:
            print(f"            ({name!r}, {value!r}),")
        print("        ],")
    print(f"        body={r.body!r},")
    print("    ),")


def print_response(r: HTTPResponse) -> None:
    print(
        f"    \x1b[0;31mHTTPResponse\x1b[0m(version={r.version!r}, method={r.code!r}, reason={r.reason!r}),",  # Red
    )


def print_fanout(
    fanout_result: list[list[HTTPRequest | HTTPResponse]],
    server_names: list[str],
) -> None:
    for name, pts in zip(server_names, fanout_result):
        print(f"{name}: [")
        for r in pts:
            if isinstance(r, HTTPRequest):
                print_request(r)
            elif isinstance(r, HTTPResponse):
                print_response(r)
        print("]")


def print_unparsed_fanout(payload: list[bytes], servers: list[Server]) -> None:
    for server, result in zip(servers, unparsed_fanout(payload, servers)):
        print(f"\x1b[0;34m{server.name}\x1b[0m:")  # Blue
        for r in result:
            is_response: bool = r.startswith(b"HTTP/")
            if is_response:
                if len(r) > 80:
                    r = r[:80] + b"..."
                print("\x1b[0;31m", end="")  # Red
            print(repr(r) + "\x1b[0m")


def print_grid(grid: Grid, labels: list[str]) -> None:
    first_column_width: int = max(map(len, labels))
    labels = [label.ljust(first_column_width) for label in labels]

    # Vertical labels
    result: str = (
        "".join(
            f'{"".ljust(first_column_width - 1)}{" ".join(row)}\n'
            for row in itertools.zip_longest(
                *(s.strip().rjust(len(s)) for s in [" " * len(labels[0]), *labels]),
            )
        )
        + f"{''.ljust(first_column_width)}+{'-' * (len(labels) * 2 - 1)}\n"
    )

    # Horizontal labels; checks and exes.
    for label, row in zip(labels, grid):
        result += label.ljust(first_column_width) + "|"
        for entry in row:
            symbol: str
            if entry is None:
                symbol = " "
            elif entry in (ErrorType.OK, ErrorType.RESPONSE_DISCREPANCY):
                symbol = "\x1b[0;32m✓\x1b[0m"
            elif entry in (
                ErrorType.DISCREPANCY,
                ErrorType.REQUEST_DISCREPANCY,
                ErrorType.TYPE_DISCREPANCY,
                ErrorType.STREAM_DISCREPANCY,
            ):
                symbol = "\x1b[0;31mX\x1b[0m"
            elif entry in (ErrorType.INVALID,):
                symbol = "\x1b[37;41mX\x1b[0m"
            result += symbol + " "
        result += "\n"

    print(result, end="")


def print_frames(frames: list[H2Frame]) -> None:
    print("[")
    for frame in frames:
        print(f"    {frame},")
    print("]")


def print_clusters(clusters: Clusters) -> None:
    for i, cluster in enumerate(clusters):
        print(f"    {i}.", *(s.name for s in cluster))


def print_stream(stream: list[bytes]) -> None:
    print(" ".join(repr(b)[1:] for b in stream))


def invalid_syntax() -> None:
    print("Invalid syntax.")


def validate_server_names(server_names: list[str]) -> bool:
    for s in server_names:
        if s not in ORIGIN_DICT and s not in TRANSDUCER_DICT:
            print(f"Invalid server name: {s}")
            return False
    return True


def validate_transducer_names(transducer_names: list[str]) -> bool:
    for s in transducer_names:
        if s not in TRANSDUCER_DICT:
            print(f"Invalid transducer name: {s}")
            return False
    return True


def validate_origin_names(origin_names: list[str]) -> bool:
    for s in origin_names:
        if s not in ORIGIN_DICT:
            print(f"Invalid origin name: {s}")
            return False
    return True


def is_request_response_stream(l: Any) -> TypeGuard[list[list[HTTPRequest | HTTPResponse]]]:
    result: bool = isinstance(l, list) and all(isinstance(inner_l, list) for inner_l in l) and all(all(isinstance(item, (HTTPRequest, HTTPResponse)) for item in inner_l) for inner_l in l)
    if not result:
        print("This command expects to have its input piped in from `fanout`.")
    return result


class REPLParseError(Exception):
    pass


def parse_h2frametype_statement(it: Iterable[str]) -> H2FrameType:
    it = iter(it)
    token: str | None = safe_next(it)
    if token is None:
        raise REPLParseError("Unexpected start of type statement")
    match token.lower():
        case "data":
            return H2FrameType.DATA
        case "headers":
            return H2FrameType.HEADERS
        case "priority":
            return H2FrameType.PRIORITY
        case "rst_stream":
            return H2FrameType.RST_STREAM
        case "settings":
            return H2FrameType.SETTINGS
        case "push_promise":
            return H2FrameType.PUSH_PROMISE
        case "ping":
            return H2FrameType.PING
        case "goaway":
            return H2FrameType.GOAWAY
        case "window_update":
            return H2FrameType.WINDOW_UPDATE
        case "continuation":
            return H2FrameType.CONTINUATION
    try:
        int_token: int = int(token)
    except ValueError:
        raise REPLParseError("Unexpected value of type statement")
    if int_token not in range(0, 256):
        raise REPLParseError("type out of range!")
    return H2FrameType(int_token)


def parse_h2flags_statement(it: Iterable[str]) -> H2Flags:
    it = iter(it)
    initial_token: str | None = safe_next(it)
    if initial_token is None or initial_token.lower() != "{":
        raise REPLParseError("Unexpected start of flags statement (should begin with '{')!")
    result: int = 0
    while True:
        token: str | None = safe_next(it)
        if token is None:
            raise REPLParseError("Unexpected end of flags statement!")
        token = token.lower()
        match token:
            case "0" | "end_stream" | "ack":
                result |= (1 << 0)
            case "1":
                result |= (1 << 1)
            case "2" | "end_headers":
                result |= (1 << 2)
            case "3" | "padded":
                result |= (1 << 3)
            case "4":
                result |= (1 << 4)
            case "5" | "priority":
                result |= (1 << 5)
            case "6":
                result |= (1 << 6)
            case "7":
                result |= (1 << 7)
            case "}":
                break
            case _:
                raise REPLParseError("Unexpected value of flags statement")
    return H2Flags.parse(result)


def parse_h2frames_statement(it: Iterable[str]) -> list[bytes]:
    it = iter(it)
    result: list[bytes] = []
    while True:
        typ: H2FrameType | None = None
        flags: H2Flags = H2Flags()
        reserved: bool = False
        stream_id: int = 0
        payload: bytes = b""
    
        initial_token: str | None = safe_next(it)
        if initial_token is None:
            break
        if initial_token.lower() == "pri":
            result.append(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
            continue
        elif initial_token.lower() != "[":
            raise REPLParseError("Unexpected start of frame statement (should begin with '[')!")
    
        while True:
            token: str | None = safe_next(it)
            if token is None:
                raise REPLParseError("Unexpected end of frame statement!")
            token = token.lower()
            match token:
                case "type":
                    typ = parse_h2frametype_statement(it)
                case "flags":
                    flags = parse_h2flags_statement(it)
                case "id" | "stream_id":
                    try:
                        tmp_stream_id: str | None = safe_next(it)
                        if tmp_stream_id is None:
                            raise REPLParseError("Premature end of stream_id statement!")
                        stream_id = int(tmp_stream_id)
                    except ValueError:
                        raise REPLParseError("Invalid stream_id")
                case "reserved":
                    reserved = True
                case "payload":
                    try:
                        tmp_payload: str | None = safe_next(it)
                        if tmp_payload is None:
                            raise REPLParseError("Premature end of payload statement!")
                        payload = tmp_payload.encode("latin1").decode("unicode-escape").encode("latin1")
                    except UnicodeEncodeError:
                        raise REPLParseError("Couldn't encode the frame payload to latin1. If you're using multibyte characters, please use escape sequences (e.g. `\\xff`) instead.")
                    except UnicodeDecodeError:
                        raise REPLParseError("Couldn't Unicode escape the frame payload. Did you forget to quote it?")
                case "]":
                    break
        if typ is None:
            raise REPLParseError("No valid H2FrameType found!")
        result.append(H2GenericFrame(typ, flags, reserved, stream_id, payload).to_bytes())
    return result

def is_byte_stream(l: Any) -> TypeGuard[list[bytes]]:
    result: bool = isinstance(l, list) and all(isinstance(item, bytes) for item in l)
    return result


def main() -> None:
    while True:
        try:
            line: str = input("\x1b[0;32mgarden>\x1b[0m ")  # Green
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue

        try:
            tokens: list[str] = [t[1:-1] if t[0] == t[-1] and t[0] in "\"'" else t for t in shlex.shlex(line)]
        except ValueError:
            print("Couldn't lex the line! Are your quotes matched?")
            continue

        unparsed_pipelines: list[list[str]] = list_split(tokens, ";")
        pipelines: list[list[list[str]]] = [list_split(unparsed_pipeline, "|") for unparsed_pipeline in unparsed_pipelines]

        for pipeline in pipelines:
            cwd: None | list[bytes] | list[list[HTTPRequest | HTTPResponse]] = None
            for command in pipeline:
                match command:
                    case []:
                        pass
                    case ["payload"]:
                        print(cwd)
                    case ["payload", *symbols]:
                        try:
                            cwd = [s.encode("latin1").decode("unicode-escape").encode("latin1") for s in symbols]
                        except UnicodeEncodeError:
                            print(
                                "Couldn't encode the payload to latin1. If you're using multibyte characters, please use escape sequences (e.g. `\\xff`) instead.",
                            )
                        except UnicodeDecodeError:
                            print("Couldn't Unicode escape the payload. Did you forget to quote it?")
                    case ["grid", *symbols]:
                        if is_request_response_stream(cwd):
                            if not symbols:
                                symbols = list(ORIGIN_DICT.keys())
                            if validate_server_names(symbols) and symbols:
                                print_grid(generate_grid(cwd, [ORIGIN_DICT[s] for s in symbols]), symbols)
                            cwd = None
                    case ["cluster", *symbols]:
                        if is_request_response_stream(cwd):
                            if not symbols:
                                symbols = list(ORIGIN_DICT.keys())
                            if validate_server_names(symbols) and symbols:
                                print_clusters(generate_clusters(cwd, [ORIGIN_DICT[s] for s in symbols]))
                            cwd = None
                    case ["transduce", *symbols]:
                        if symbols and validate_transducer_names(symbols):
                            if is_byte_stream(cwd):
                                print_stream(cwd)
                                for transducer in (TRANSDUCER_DICT[name] for name in symbols):
                                    cwd = transducer.unparsed_roundtrip(cwd)
                                    print(f"⬇️ \x1b[0;34m{transducer.name}\x1b[0m")  # Blue
                                    print_stream(cwd)
                            else:
                                print("This command expects to have its input piped in from `payload` or `transduce`.")
                    case ["fanout", *symbols]:
                        if is_byte_stream(cwd):
                            if not symbols:
                                symbols = list(ORIGIN_DICT.keys())
                            if validate_server_names(symbols):
                                cwd = fanout(cwd, [ORIGIN_DICT[s] for s in symbols])
                                print_fanout(cwd, symbols)
                        else:
                            print("This command expects to have its input piped in from `payload` or `transduce`.")
                    case ["unparsed_fanout" | "uf", *symbols]:
                        if is_byte_stream(cwd):
                            if len(symbols) == 0:
                                symbols = list(ORIGIN_DICT.keys())
                            if validate_server_names(symbols):
                                print_unparsed_fanout(cwd, [ORIGIN_DICT[s] for s in symbols])
                        else:
                            print("This command expects to have its input piped in from `payload` or `transduce`.")
                    case ["unparsed_transducer_fanout" | "utf", *symbols]:
                        if is_byte_stream(cwd):
                            if len(symbols) == 0:
                                symbols = list(TRANSDUCER_DICT.keys())
                            if validate_transducer_names(symbols):
                                print_unparsed_fanout(cwd, [TRANSDUCER_DICT[s] for s in symbols])
                        else:
                            print("This command expects to have its input piped in from `payload` or `transduce`.")
                    case ["h2frames", *symbols]:
                        try:
                            frame_bytes: bytes = b"".join(parse_h2frames_statement(symbols))
                            if is_byte_stream(cwd):
                                cwd.append(frame_bytes)
                            else:
                                cwd = [frame_bytes]
                        except REPLParseError as e:
                            print(f"repl parse error: {e}")
                    case ["exit" | "quit"]:
                        print("Next time, just press Ctrl-D :)")
                        sys.exit(0)
                    case _:
                        invalid_syntax()


if __name__ == "__main__":
    main()
