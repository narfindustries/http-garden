""" The Garden repl """

import contextlib
import importlib
import itertools
import shlex
from collections.abc import Sequence

import targets  # This gets reloaded, so we import the whole module
from diff import ErrorType, categorize_discrepancy
from fanout import (
    fanout,
    unparsed_fanout,
)
from http1 import HTTPRequest, HTTPResponse
from targets import Server, Transducer, Origin


grid_t = tuple[tuple[ErrorType | None, ...], ...]


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
                print("\x1b[0;31m", end="") # Red
            print(repr(r) + "\x1b[0m")


def compute_grid(
    payload: list[bytes],
    servers: list[Server],
) -> grid_t:
    pts: list[list[HTTPRequest | HTTPResponse]] = fanout(payload, servers)
    result = []
    for i, (s1, pt1) in enumerate(zip(servers, pts)):
        row: list[ErrorType | None] = []
        for j, (s2, pt2) in enumerate(zip(servers, pts)):
            if j < i:
                row.append(None)
            else:
                row.append(categorize_discrepancy(pt1, pt2, s1, s2))
        result.append(tuple(row))
    return tuple(result)


def print_grid(grid: grid_t, labels: list[str]) -> None:
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
            elif entry in (ErrorType.REQUEST_DISCREPANCY, ErrorType.TYPE_DISCREPANCY, ErrorType.STREAM_DISCREPANCY):
                symbol = "\x1b[0;31mX\x1b[0m"
            elif entry in (ErrorType.INVALID,):
                symbol = "\x1b[37;41mX\x1b[0m"
            result += symbol + " "
        result += "\n"

    print(result, end="")


def print_stream(stream: list[bytes], id_no: int) -> None:
    print(f"[{id_no}]:", " ".join(repr(b)[1:] for b in stream))


_HELP_MESSAGES: dict[str, str] = {
    "help": "Shows this message.",
    "env": "Shows the current state of the repl (selected servers, payload, etc.)",
    "payload": "Shows the current payload",
    "payload <datum> [datum]*": "Sets the payload.",
    "history": "Shows the payload history.",
    "history <n>": "Selects the nth item in the history",
    "history pop": "Removes the last item in the history",
    "history clear": "Clears the history, except for the last item",
    "servers [server]*": "Selects the specified server(s).",
    "add [server]*": "Adds the specified server(s) to the selection.",
    "del [server]*": "Removes the specified server(s) from the selection.",
    "grid": "Sends the payload to the selected servers, then shows whether each pair agrees on its interpretation.",
    "fanout": "Sends the payload to the selected servers, then shows each server's interpretation of the payload.",
    "unparsed_fanout": "Sends the payload to the selected servers, then shows each server's raw response to the payload. This is useful when debugging new targets, and otherwise useless.",
    "unparsed_transducer_fanout": "Sends the payload to the transducers among the selected servers, then shows each server's raw response to the payload. This is useful when debugging new targets.",
    "transduce [transducer]*": "Sends the payload through the specified transducers in sequence, saving the intermediate and final results in the payload history.",
    "reload": "Reloads the server list. Run this after restarting the Garden.",
}


def print_all_help_messages() -> None:
    print("This is the HTTP Garden repl. It is best run within rlwrap(1).")
    for k, v in _HELP_MESSAGES.items():
        print(k)
        print(f"    {v}")


def invalid_syntax() -> None:
    print("Invalid syntax. Try `help`.")


_INITIAL_PAYLOAD: list[bytes] = [b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"]


def reload_servers(servers: list[Server]) -> list[Server]:
    importlib.reload(targets)
    new_servers: list[Server] = []
    for server in servers:
        if server.name not in targets.SERVICE_DICT:
            print(f"{server.name} no longer available. Removing it from selection.")
        else:
            new_servers.append(targets.SERVICE_DICT[server.name])
    return new_servers


def main() -> None:
    servers: list[Server] = list(targets.SERVICE_DICT.values())
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
            tokens: list[str] = [t[1:-1] if t[0] == t[-1] and t[0] in "\"'" else t for t in shlex.shlex(line)]
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
                case ["help"]:
                    print_all_help_messages()
                case ["env"]:
                    print(f"Selected servers: {' '.join(s.name for s in servers)}")
                    print()
                    print(f"All servers:      {' '.join(targets.SERVICE_DICT)}")
                    print()
                    print(f"All transducers:  {' '.join(targets.TRANSDUCER_DICT)}")
                    print()
                    print(f'Payload:          {" ".join(repr(p)[1:] for p in payload)}')
                    print()
                case ["payload"]:
                    print_stream(payload, len(payload_history) - 1)
                case ["payload", *symbols]:
                    try:
                        payload_history.append(
                            [s.encode("latin1").decode("unicode-escape").encode("latin1") for s in symbols],
                        )
                    except UnicodeEncodeError:
                        print(
                            "Couldn't encode the payload to latin1. If you're using multibyte characters, please use escape sequences (e.g. `\\xff`) instead.",
                        )
                    except UnicodeDecodeError:
                        print("Couldn't Unicode escape the payload. Did you forget to quote it?")
                case ["history"]:
                    for i, p in enumerate(payload_history):
                        print_stream(p, i)
                case ["history", "pop"]:
                    payload_history = payload_history[:-1] or [_INITIAL_PAYLOAD]
                case ["history", "clear"]:
                    payload_history = payload_history[-1:]
                case ["history", index] if index.isascii() and index.isdigit():
                    payload_history.append(payload_history[int(index)])
                    print_stream(payload_history[-1], len(payload_history) - 1)
                case ["servers"]:
                    print(*(s.name for s in servers))
                case ["servers", *symbols]:
                    for symbol in symbols:
                        if symbol not in targets.SERVICE_DICT:
                            print(f"Server {symbol!r} not found")
                            break
                    else:
                        servers = [targets.SERVICE_DICT[s] for s in symbols]
                case ["add", *symbols]:
                    for symbol in symbols:
                        if symbol not in targets.SERVICE_DICT:
                            print(f"Server {symbol!r} not found")
                            break
                    else:
                        for symbol in symbols:
                            if symbol in targets.SERVICE_DICT and targets.SERVICE_DICT[symbol] not in servers:
                                servers.append(targets.SERVICE_DICT[symbol])
                case ["del", *symbols]:
                    for symbol in symbols:
                        if symbol not in targets.SERVICE_DICT:
                            print(f"Server {symbol!r} not found")
                            break
                    else:
                        for symbol in symbols:
                            if symbol in targets.SERVICE_DICT:
                                with contextlib.suppress(ValueError):
                                    servers.remove(targets.SERVICE_DICT[symbol])
                case ["grid"]:
                    print_grid(
                        compute_grid(payload, servers),
                        [s.name for s in servers],
                    )
                case ["origin_grid" | "og"]:
                    print_grid(
                        compute_grid(payload, [s for s in servers if isinstance(s, Origin)]),
                        [s.name for s in servers if isinstance(s, Origin)],
                    )
                case ["transducer_grid" | "tg"]:
                    print_grid(
                        compute_grid(payload, [s for s in servers if isinstance(s, Transducer)]),
                        [s.name for s in servers if isinstance(s, Transducer)],
                    )
                case ["fanout" | "f"]:
                    print_fanout(payload, servers)
                case [("fanout" | "f"), *symbols]:
                    try:
                        print_fanout(payload, [targets.SERVICE_DICT[s] for s in symbols])
                    except KeyError:
                        print(f"Server {symbols!r} not found")
                        continue
                case ["origin_fanout" | "of"]:
                    print_fanout(payload, [s for s in servers if isinstance(s, Origin)])
                case ["unparsed_fanout" | "uf"]:
                    print_unparsed_fanout(payload, servers)
                case ["unparsed_transducer_fanout" | "utf"]:
                    print_unparsed_fanout(payload, [s for s in servers if isinstance(s, Transducer)])
                case ["transduce", *symbols]:
                    try:
                        transducers = [targets.TRANSDUCER_DICT[t_name] for t_name in symbols]
                    except KeyError:
                        t_name = next(name for name in symbols if name not in targets.TRANSDUCER_DICT)
                        print(f"Transducer {t_name!r} not found")
                        continue
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
                case ["reload"]:
                    servers = reload_servers(servers)
                case _:
                    invalid_syntax()


if __name__ == "__main__":
    main()
