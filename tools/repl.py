"""The Garden repl"""

import itertools
import shlex

from diff import ErrorType
from fanout import (
    fanout,
    unparsed_fanout,
)
from grid import grid, Grid
from http1 import HTTPRequest, HTTPResponse
from targets import SERVER_DICT, TRANSDUCER_DICT, Server


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
    payload: list[bytes],
    servers: list[Server],
) -> None:
    for s, pts in zip(servers, fanout(payload, servers)):
        print(f"{s.name}: [")
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
                print("\x1b[0;31m", end="")  # Red
            print(repr(r) + "\x1b[0m")


def print_grid(the_grid: Grid, labels: list[str]) -> None:
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
    for label, row in zip(labels, the_grid):
        result += label.ljust(first_column_width) + "|"
        for entry in row:
            symbol: str
            if entry is None:
                symbol = " "
            elif entry in (ErrorType.OK, ErrorType.RESPONSE_DISCREPANCY):
                symbol = "\x1b[0;32m✓\x1b[0m"
            elif entry in (
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


def print_stream(stream: list[bytes], id_no: int) -> None:
    print(f"[{id_no}]:", " ".join(repr(b)[1:] for b in stream))


def invalid_syntax() -> None:
    print("Invalid syntax.")


def is_valid_server_name(server_name: str) -> bool:
    if server_name not in SERVER_DICT:
        print(f"Server {server_name!r} not found")
        return False
    return True


def is_valid_transducer_name(transducer_name: str) -> bool:
    if transducer_name not in TRANSDUCER_DICT:
        print(f"Transducer {transducer_name!r} not found")
        return False
    return True


_INITIAL_PAYLOAD: list[bytes] = [b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"]


def main() -> None:
    payload_history: list[list[bytes]] = [_INITIAL_PAYLOAD]
    while True:
        try:
            line: str = input("\x1b[0;32mgarden>\x1b[0m ")  # Green
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue

        try:
            tokens: list[str] = [
                t[1:-1] if t[0] == t[-1] and t[0] in "\"'" else t
                for t in shlex.shlex(line)
            ]
        except ValueError:
            print("Couldn't lex the line! Are your quotes matched?")
            continue

        commands: list[list[str]] = []
        while ";" in tokens:
            commands.append(tokens[: tokens.index(";")])
            tokens = tokens[tokens.index(";") + 1 :]
        commands.append(tokens)

        for command in commands:
            payload: list[bytes] = payload_history[-1]
            match command:
                case []:
                    pass
                case ["env"]:
                    print(f"All servers:      {' '.join(SERVER_DICT)}")
                    print()
                    print(f"All transducers:  {' '.join(TRANSDUCER_DICT)}")
                    print()
                    print(f'Payload:          {" ".join(repr(p)[1:] for p in payload)}')
                    print()
                case ["payload"]:
                    print_stream(payload, len(payload_history) - 1)
                case ["payload", *symbols]:
                    try:
                        payload_history.append(
                            [
                                s.encode("latin1")
                                .decode("unicode-escape")
                                .encode("latin1")
                                for s in symbols
                            ],
                        )
                    except UnicodeEncodeError:
                        print(
                            "Couldn't encode the payload to latin1. If you're using multibyte characters, please use escape sequences (e.g. `\\xff`) instead.",
                        )
                    except UnicodeDecodeError:
                        print(
                            "Couldn't Unicode escape the payload. Did you forget to quote it?"
                        )
                case ["history"]:
                    for i, p in enumerate(payload_history):
                        print_stream(p, i)
                case ["grid", *symbols]:
                    if len(symbols) == 0:
                        symbols = list(SERVER_DICT.keys())
                    if all(is_valid_server_name(s) for s in symbols):
                        print_grid(
                            grid(payload, [SERVER_DICT[s] for s in symbols]),
                            symbols,
                        )
                case ["fanout", *symbols]:
                    if len(symbols) == 0:
                        symbols = list(SERVER_DICT.keys())
                    if all(is_valid_server_name(s) for s in symbols):
                        print_fanout(payload, [SERVER_DICT[s] for s in symbols])
                case ["unparsed_fanout" | "uf", *symbols]:
                    if len(symbols) == 0:
                        symbols = list(SERVER_DICT.keys())
                    if all(is_valid_transducer_name(s) for s in symbols):
                        print_unparsed_fanout(payload, [TRANSDUCER_DICT[s] for s in symbols])
                case ["unparsed_transducer_fanout" | "utf", *symbols]:
                    if len(symbols) == 0:
                        symbols = list(SERVER_DICT.keys())
                    if all(is_valid_transducer_name(s) for s in symbols):
                        print_unparsed_fanout(
                            payload, [TRANSDUCER_DICT[s] for s in symbols]
                        )
                case ["transduce", *symbols]:
                    if all(is_valid_transducer_name(s) for s in symbols):
                        transducers = [
                            TRANSDUCER_DICT[t_name] for t_name in symbols
                        ]
                        tmp: list[bytes] = payload
                        for transducer in transducers:
                            print_stream(tmp, len(payload_history) - 1)
                            try:
                                tmp = transducer.unparsed_roundtrip(tmp)
                            except ValueError as e:
                                print(e)
                                break
                            if len(tmp) == 0:
                                print(f"{transducer.name} didn't respond")
                                break
                            print(f"    ⬇️ \x1b[0;34m{transducer.name}\x1b[0m")  # Blue
                            payload_history.append(tmp)
                        else:
                            print_stream(tmp, len(payload_history) - 1)
                case _:
                    invalid_syntax()


if __name__ == "__main__":
    main()
