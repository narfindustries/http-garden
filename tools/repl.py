""" The Garden repl """

import functools
import itertools
import importlib
import shlex
import sys

from typing import Sequence

import tqdm

import targets  # This gets reloaded, so we import the whole module
from targets import Service  # This won't change across reloads
from http1 import HTTPRequest, HTTPResponse
from fanout import fanout, transducer_roundtrip, adjust_host_header, server_roundtrip
from util import stream_t, fingerprint_t, eager_pmap
from diff_fuzz import run_one_generation, categorize_discrepancy, SEEDS, DiscrepancyType
from mutations import mutate

INTERESTING_DISCREPANCY_TYPES = [
    DiscrepancyType.STREAM_DISCREPANCY,
    DiscrepancyType.SUBTLE_DISCREPANCY,
    DiscrepancyType.STATUS_DISCREPANCY,
]


def print_fanout(
    payload: stream_t,
    servers: list[Service],
) -> None:
    for s, (pts, _) in zip(servers, fanout(payload, servers, traced=False)):
        print(f"{s.name}: [")
        for r in pts:
            if isinstance(r, HTTPRequest):
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
            elif isinstance(r, HTTPResponse):
                print(
                    f"    \x1b[0;31mHTTPResponse\x1b[0m(version={r.version!r}, method={r.code!r}, reason={r.reason!r}),"  # Red
                )

        print("]")


def try_transducer_roundtrip(payload: stream_t, transducer: Service) -> stream_t:
    try:
        return transducer_roundtrip(payload, transducer)
    except ValueError:
        return []


def transducer_fanout(payload: stream_t, transducers: list[Service], adjusting_host: bool) -> list[stream_t]:
    return eager_pmap(
        lambda t: try_transducer_roundtrip(adjust_host_header(payload, t) if adjusting_host else payload, t),
        transducers,
    )


def print_transducer_fanout(payload: stream_t, transducers: list[Service], adjusting_host: bool) -> None:
    for t, result in zip(transducers, transducer_fanout(payload, transducers, adjusting_host)):
        print(f"\x1b[0;34m{t.name}\x1b[0m:")  # Blue
        print(" ".join(repr(b)[1:] for b in result))


def print_raw_fanout(payload: stream_t, servers: list[Service]) -> None:
    for server, result in zip(servers, eager_pmap(functools.partial(server_roundtrip, payload), servers)):
        print(f"\x1b[0;34m{server.name}\x1b[0m:")  # Blue
        for r in result:
            print(repr(r))


def compute_grid(payload: stream_t, servers: list[Service]) -> list[list[bool | None]]:
    pts: list[list[HTTPRequest | HTTPResponse]] = [pt for pt, _ in fanout(payload, servers, traced=False)]
    result = []
    for i, (s1, pt1) in enumerate(zip(servers, pts)):
        row: list[bool | None] = []
        for j, (s2, pt2) in enumerate(zip(servers, pts)):
            if j <= i:
                row.append(None)
            else:
                row.append(categorize_discrepancy([pt1, pt2], [s1, s2]) in INTERESTING_DISCREPANCY_TYPES)
        result.append(row)
    return result


def print_grid(grid: Sequence[Sequence[bool | None]], labels: list[str]) -> None:
    first_column_width: int = max(map(len, labels))
    labels = [label.ljust(first_column_width) for label in labels]

    result: str = (
        "".join(
            f'{" " * first_column_width}{" ".join(row)}\n'
            for row in itertools.zip_longest(
                *map(lambda s: s.strip().rjust(len(s)), [" " * len(labels[0])] + labels[1:])
            )
        )
        + f"{' ' * first_column_width}+{'-' * ((len(labels) - 1) * 2)}\n"
    )

    for label, row in zip(labels[:-1], grid[:-1]):
        result += label.ljust(first_column_width) + "|"
        for j, entry in enumerate(row):
            result += (" " if entry is None else "\x1b[0;31mX\x1b[0m" if entry else "\x1b[0;32m✔️\x1b[0m") + (
                " " * (j != 0)
            )
        result += "\n"

    print(result, end="")


def print_stream(stream: stream_t, id_no: int) -> None:
    print(f"[{id_no}]:", " ".join(repr(b)[1:] for b in stream))


_HELP_MESSAGES: dict[str, str] = {
    "help": "Shows this message.",
    "env": "Shows the current state of the repl (selected servers, payload, etc.)",
    "exit": "Exits the HTTP Garden repl.",
    "payload": "Shows the current payload",
    "payload <datum> [datum]*": "Sets the payload.",
    "history": "Shows the payload history.",
    "history <n>": "Selects the nth item in the history",
    "history pop": "Removes the last item in the history",
    "history clear": "Clears the history, except for the last item",
    "servers [server]*": "Selects the specified server(s).",
    "add [server]*": "Adds the specified server(s) to the selection.",
    "del [server]*": "Removes the specified server(s) from the selection.",
    "mutate": "Mutates the current payload using a random choice of the mutation operations.",
    "fuzz <gen_size> <gen_count>": "Runs the differential fuzzer with the specified generation size for the specified number of generations on the selected servers, then reports the results.",
    "grid": "Sends the payload to the selected servers, then shows whether each pair agrees on its interpretation.",
    "fanout": "Sends the payload to the selected servers, then shows each server's interpretation of the payload.",
    "raw_fanout": "Sends the payload to the selected servers, then shows each server's raw response to the payload. This is useful when debugging new targets, and otherwise useless.",
    "transducer_fanout": "Sends the payload to all the transducers simultaneously, then shows each transducer's output.",
    "transduce [transducer]*": "Sends the payload through the specified transducers in sequence, saving the intermediate and final results in the payload history.",
    "adjust_host <on|off>": "Changes whether the host header is automatically adjusted before sending requests to transducers. Some transducers, especially CDNs, will require this.",
    "reload": "Reloads the server list. Run this after restarting the Garden.",
}


def print_all_help_messages() -> None:
    print("This is the HTTP Garden repl. It is best run within rlwrap(1).")
    for k in _HELP_MESSAGES:
        print_help_message(k)


def print_help_message(command: str) -> None:
    if command not in _HELP_MESSAGES:
        print(f"Command {command} not found.")
    print(command)
    print(f"    {_HELP_MESSAGES[command]}")
    print()


def invalid_syntax() -> None:
    print("Invalid syntax. Try `help`.")


_INITIAL_PAYLOAD: stream_t = [b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"]


def main() -> None:
    servers: list[Service] = list(targets.SERVER_DICT.values())
    payload_history: list[stream_t] = [_INITIAL_PAYLOAD]
    adjusting_host: bool = False
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
            payload: stream_t = payload_history[-1]
            match command:
                case []:
                    pass
                case ["help"]:
                    print_all_help_messages()
                case ["help", word]:
                    print_help_message(word)
                case ["env"]:
                    print(f"All servers:      {' '.join(targets.SERVER_DICT)}")
                    print()
                    print(f"Selected servers: {' '.join(s.name for s in servers)}")
                    print()
                    print(f"All transducers:  {' '.join(targets.TRANSDUCER_DICT)}")
                    print()
                    print(f'Payload:          {" ".join(repr(p)[1:] for p in payload)}')
                    print()
                    print(
                        f"The host header is {'not ' if not adjusting_host else ""}currently being adjusted."
                    )
                case ["payload"]:
                    print_stream(payload, len(payload_history) - 1)
                case ["payload", *symbols]:
                    try:
                        payload_history.append(
                            [s.encode("latin1").decode("unicode-escape").encode("latin1") for s in symbols]
                        )
                    except UnicodeEncodeError:
                        print(
                            "Couldn't encode the payload to latin1. If you're using multibyte characters, please use escape sequences (e.g. `\\xff`) instead."
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
                        if symbol not in targets.SERVER_DICT:
                            print(f"Server {symbol!r} not found")
                            break
                    else:
                        servers = [targets.SERVER_DICT[s] for s in symbols]
                case ["transducers"]:
                    print(*targets.TRANSDUCER_DICT)
                case ["add", *symbols]:
                    for symbol in symbols:
                        if symbol not in targets.SERVER_DICT:
                            print(f"Server {symbol!r} not found")
                            break
                    else:
                        for symbol in symbols:
                            if symbol in targets.SERVER_DICT and targets.SERVER_DICT[symbol] not in servers:
                                servers.append(targets.SERVER_DICT[symbol])
                case ["del", *symbols]:
                    for symbol in symbols:
                        if symbol not in targets.SERVER_DICT:
                            print(f"Server {symbol!r} not found")
                            break
                    else:
                        for symbol in symbols:
                            if symbol in targets.SERVER_DICT:
                                try:
                                    servers.remove(targets.SERVER_DICT[symbol])
                                except ValueError:  # Not found
                                    pass
                case ["grid"]:
                    print_grid(compute_grid(payload, servers), [s.name for s in servers])
                case ["fanout"]:
                    print_fanout(payload, servers)
                case ["raw_fanout"]:
                    print_raw_fanout(payload, servers)
                case ["transducer_fanout"]:
                    print_transducer_fanout(payload, list(targets.TRANSDUCER_DICT.values()), adjusting_host)
                case ["transduce", *symbols]:
                    try:
                        transducers = [targets.TRANSDUCER_DICT[t_name] for t_name in symbols]
                    except KeyError:
                        t_name = next(name for name in symbols if name not in targets.TRANSDUCER_DICT)
                        print(f"Transducer {t_name!r} not found")
                        continue
                    tmp: stream_t = payload
                    for transducer in transducers:
                        if adjusting_host:
                            tmp = adjust_host_header(tmp, transducer)
                        print_stream(tmp, len(payload_history) - 1)
                        try:
                            tmp = transducer_roundtrip(tmp, transducer)
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
                case ["adjust_host", "on"]:
                    adjusting_host = True
                case ["adjusting_host", "off"]:
                    adjusting_host = False
                case ["reload"]:
                    importlib.reload(targets)
                    new_servers: list[Service] = []
                    for server in servers:
                        if server.name not in targets.SERVER_DICT:
                            print(f"{server.name} no longer available. Removing it from selection.")
                        else:
                            new_servers.append(targets.SERVER_DICT[server.name])
                    servers = new_servers
                case ["fuzz", arg1, arg2] if all(a.isascii() and a.isdigit() for a in (arg1, arg2)):
                    seeds: list[stream_t] = SEEDS
                    min_generation_size: int = int(command[1])
                    num_generations: int = int(command[2])
                    inputs: list[stream_t] = list(seeds)
                    seen: set[fingerprint_t] = set()
                    results: list[stream_t] = []
                    for i in range(num_generations + 1):  # +1 because there's a zeroth generation: the seeds
                        try:
                            new_results, interesting = run_one_generation(
                                servers, inputs, seen, progress_bar_description=f"Generation {i}"
                            )
                        except AssertionError:
                            print(
                                "The fuzzer exited early. This happens sometimes when the servers and fuzzer get out of sync."
                            )
                            print(
                                "Try running `reload` and it will probably work. This bug is being tracked here:"
                            )
                            print("    https://github.com/narfindustries/http-garden/issues/8")
                            break
                        except KeyboardInterrupt:
                            break
                        results += new_results
                        print(
                            f"{len(new_results)} discrepancies and {len(interesting)} new coverage tuples encountered."
                        )
                        if len(interesting) == 0:
                            interesting = inputs
                        # Generate new inputs
                        new_inputs: list[stream_t] = []
                        while len(new_inputs) < min_generation_size:
                            new_inputs.extend(map(mutate, interesting))
                        inputs = new_inputs
                    durable_results: list[stream_t] = []
                    for result in tqdm.tqdm(results, desc="Testing durability"):
                        for transduced in transducer_fanout(
                            result, list(targets.TRANSDUCER_DICT.values()), adjusting_host
                        ):
                            pts: list[list[HTTPRequest | HTTPResponse]] = [
                                pt for pt, _ in fanout(transduced, servers, traced=False)
                            ]
                            if categorize_discrepancy(pts, servers) in INTERESTING_DISCREPANCY_TYPES:
                                durable_results.append(result)
                                break

                    categorized_results: dict[tuple[tuple[bool | None, ...], ...], list[stream_t]] = {}
                    for result in durable_results:
                        grid: tuple[tuple[bool | None, ...], ...] = tuple(
                            map(tuple, compute_grid(result, servers))
                        )
                        if grid not in categorized_results:
                            categorized_results[grid] = []
                        categorized_results[grid].append(result)
                    for grid, result_list in categorized_results.items():
                        for result in result_list:
                            payload_history.append(result)
                            print_stream(result, len(payload_history) - 1)
                        print_grid(grid, [s.name for s in servers])
                case ["exit"]:
                    sys.exit(0)
                case _:
                    invalid_syntax()


if __name__ == "__main__":
    main()
