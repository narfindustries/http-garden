""" The Garden repl """

import base64
import binascii
import functools
import itertools
import importlib
import shlex
import pprint
import re

from typing import Sequence

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


def highlight_pattern(s: str, pattern: re.Pattern[str] | None) -> str:
    if pattern is None:
        return s
    for m in reversed(list(re.finditer(pattern, s))):
        start, end = m.span()
        s = s[:start] + "\x1b[0;31m" + s[start:end] + "\x1b[0m" + s[end:]  # Red
    return s


def highlight_pattern_bytes(
    b: bytes, pattern: re.Pattern[str] | None
) -> str:  # You may want to consider switching to re.Pattern[bytes]
    r: str = repr(b)
    return r[:2] + highlight_pattern(r[2:-1], pattern) + r[-1:]


def print_fanout(
    payload: stream_t,
    servers: list[Service],
    name_pattern: re.Pattern[str] | None,
    value_pattern: re.Pattern[str] | None,
    body_pattern: re.Pattern[str] | None,
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
                        print(
                            f"            ({highlight_pattern_bytes(name, name_pattern)}, {highlight_pattern_bytes(value, value_pattern)}),"
                        )
                    print("        ],")
                print(f"        body={highlight_pattern_bytes(r.body, body_pattern)},")
                print("    ),")
            elif isinstance(r, HTTPResponse):
                print(
                    f"    \x1b[0;31mHTTPResponse\x1b[0m(version={r.version!r}, method={r.code!r}, reason={r.reason!r}),"  # Red
                )

        print("]")


def try_transducer_roundtrip(payload: stream_t, transducer: Service) -> stream_t:
    try:
        return transducer_roundtrip(payload, transducer)
    except ValueError as e:
        print(e)
        return []


def transducer_fanout(payload: stream_t, transducers: list[Service]) -> list[stream_t]:
    return eager_pmap(functools.partial(try_transducer_roundtrip, payload), transducers)


def print_transducer_fanout(payload: stream_t, transducers: list[Service]) -> None:
    for t, result in zip(transducers, transducer_fanout(payload, transducers)):
        print(f"\x1b[0;34m{t.name}\x1b[0m:")  # Blue
        print(" ".join(repr(b)[1:] for b in result))


def print_raw_fanout(payload: stream_t, servers: list[Service]) -> None:
    for server, result in zip(servers, eager_pmap(functools.partial(server_roundtrip, payload), servers)):
        print(f"\x1b[0;34m{server.name}\x1b[0m:")  # Blue
        for r in result:
            print(f"    {r!r}")


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
            for row in itertools.zip_longest(*map(lambda s: s.strip().rjust(len(s)), labels))
        )
        + "\n"
    )

    for label, row in zip(labels, grid):
        result += label.ljust(first_column_width)
        for entry in row:
            result += (
                " " if entry is None else "\x1b[0;31mX\x1b[0m" if entry else "\x1b[0;32m✔️\x1b[0m"
            ) + " "
        result += "\n"

    print(result, end="")


def print_stream(stream: stream_t, id_no: int) -> None:
    print(f"[{id_no}]:", " ".join(repr(b)[1:] for b in stream))


def print_help_message() -> None:
    print("This is the HTTP Garden repl. It is best run within rlwrap(1).")

    print()

    print("help")
    print("    Shows this message.")
    print("env")
    print("    Shows the current state of the repl (selected servers, payload, etc.)")
    print("info <server|transducer> [server|transducer]*")
    print("    Provides information about specified server(s) and/or transducer(s).")

    print()

    print("exit")
    print("    Exits the HTTP Garden repl.")

    print()

    print("payload <datum> [datum]*")
    print("    Sets the payload.")

    print()

    print("history")
    print("    Shows the payload history.")
    print("history [n]")
    print("    Selects the nth item in the history")
    print("history pop")
    print("    Removes the last item in the history")
    print("history clear")
    print("    Clears the history, except for the last item")

    print()

    print("servers <server> [server]*")
    print("    Selects the specified server(s).")
    print("add [server]*")
    print("    Adds the specified server(s) to the selection.")
    print("del [server]*")
    print("    Removes the specified server(s) from the selection.")

    print()

    print("pattern name|value|body <regex>")
    print(
        "    Sets the specified pattern to the specified Python regular expression. Matches to this\n    regex in the specified portion of the request will be highlighted in fanout output."
    )

    print()

    print("mutate")
    print("    Mutates the current payload using a random choice of the mutation operations.")
    print("fuzz <gen_size> <gen_count>")
    print(
        "    Runs the differential fuzzer with the specified generation size for the specified number of\n    generations on the selected servers, then reports the results."
    )

    print()

    print("grid")
    print(
        "    Sends the payload to the selected servers, then shows whether each pair\n    agrees on its interpretation."
    )
    print("fanout")
    print(
        "    Sends the payload to the selected servers, then shows each server's\n    interpretation of the payload."
    )
    print("raw_fanout")
    print(
        "    Sends the payload to the selected servers, then shows each server's raw response\n   to the payload. This is useful when debugging new targets, and otherwise useless."
    )
    print("transducer_fanout [transducer]*")
    print(
        "    Sends the payload to the specified transducer(s) simultaneously, then shows\n    each transducer's output. If none are specified, then all are used."
    )
    print("transduce <transducer> [transducer]*")
    print(
        "    Sends the payload through the specified transducers in sequence,\n    saving the intermediate and final results in the payload history."
    )

    print()

    print("adjust_host <on|off>")
    print(
        "    Changes whether the host header is automatically adjusted before sending\n    requests to transducers. Some transducers, especially CDNs, will require this."
    )
    print("reload")
    print("    Reloads the server list. Run this after restarting the Garden.")
    print("b64decode <data>")
    print("    Base64-decodes data.")


def invalid_syntax() -> None:
    print("Invalid syntax. Try `help`.")


_INITIAL_PAYLOAD: stream_t = [b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"]


def main() -> None:
    servers: list[Service] = list(targets.SERVER_DICT.values())
    payload_history: list[stream_t] = [_INITIAL_PAYLOAD]
    adjusting_host: bool = True
    name_pattern: re.Pattern[str] | None = None
    value_pattern: re.Pattern[str] | None = None
    body_pattern: re.Pattern[str] | None = None
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
            if command == []:
                continue

            if command == ["help"]:
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print_help_message()

            elif command[0] == "env":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print(f"All servers:      {' '.join(targets.SERVER_DICT)}")
                print()
                print(f"Selected servers: {' '.join(s.name for s in servers)}")
                print()
                print(f"All transducers:  {' '.join(targets.TRANSDUCER_DICT)}")
                print()
                print(f'Payload:          {" ".join(repr(p)[1:] for p in payload)}')
                print()
                print(f"Name pattern:     {name_pattern and name_pattern.pattern!r}")
                print(f"Value pattern:    {value_pattern and value_pattern.pattern!r}")
                print(f"Body pattern:     {body_pattern and body_pattern.pattern!r}")
                if adjusting_host:
                    print()
                    print("The host header is currently being adjusted.")

            elif command[0] == "info":
                if len(command) < 2:
                    invalid_syntax()
                    continue
                for symbol in command[1:]:
                    if symbol not in targets.SERVER_DICT | targets.TRANSDUCER_DICT:
                        print(f"Server/transducer {symbol!r} not found")
                        break
                else:
                    for symbol in command[1:]:
                        pprint.pp((targets.SERVER_DICT | targets.TRANSDUCER_DICT)[symbol])

            elif command == ["exit"]:
                if len(command) != 1:
                    invalid_syntax()
                    continue
                break

            elif command[0] == "payload":
                if len(command) == 1:
                    print_stream(payload, len(payload_history) - 1)
                    continue
                try:
                    payload_history.append(
                        [s.encode("latin1").decode("unicode-escape").encode("latin1") for s in command[1:]]
                    )
                except UnicodeEncodeError:
                    print(
                        "Couldn't encode the payload to latin1. If you're using multibyte characters, please use escape sequences (e.g. `\\xff`) instead."
                    )
                except UnicodeDecodeError:
                    print("Couldn't Unicode escape the payload. Did you forget to quote it?")

            elif command[0] == "pattern":
                if len(command) > 3:
                    invalid_syntax()
                    continue
                if len(command) == 1:
                    print(f"Name pattern:  {name_pattern and name_pattern.pattern!r}")
                    print(f"Value pattern: {value_pattern and value_pattern.pattern!r}")
                    print(f"Body pattern:  {body_pattern and body_pattern.pattern!r}")
                elif len(command) == 2:
                    if command[1] == "name":
                        print(f"Name pattern:  {name_pattern and name_pattern.pattern!r}")
                    elif command[1] == "value":
                        print(f"Value pattern:  {value_pattern and value_pattern.pattern!r}")
                    elif command[1] == "body":
                        print(f"Body pattern:  {body_pattern and body_pattern.pattern!r}")
                    else:
                        invalid_syntax()
                        continue
                else:
                    try:
                        pattern = re.compile(command[2])
                    except re.error:
                        print(f"Invalid pattern: {command[2]!r}")
                    if command[1] == "name":
                        name_pattern = pattern
                    elif command[1] == "value":
                        value_pattern = pattern
                    elif command[1] == "body":
                        body_pattern = pattern

            elif command[0] == "history":
                if len(command) == 1:
                    for i, p in enumerate(payload_history):
                        print_stream(p, i)
                elif command == ["history", "clear"]:
                    payload_history = payload_history[-1:]
                elif command == ["history", "pop"]:
                    payload_history = payload_history[:-1] or [_INITIAL_PAYLOAD]
                elif len(command) == 2 and command[1].isascii() and command[1].isdigit():
                    payload_history.append(payload_history[int(command[1])])
                    print_stream(payload_history[-1], len(payload_history) - 1)
                else:
                    invalid_syntax()
                    continue

            elif command[0] == "servers":
                if len(command) == 1:
                    print(*(s.name for s in servers))
                    continue
                for symbol in command[1:]:
                    if symbol not in targets.SERVER_DICT:
                        print(f"Server {symbol!r} not found")
                        break
                else:
                    servers = [targets.SERVER_DICT[s] for s in command[1:]]

            elif command[0] == "transducers":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print(*targets.TRANSDUCER_DICT)

            elif command[0] == "add":
                for symbol in command[1:]:
                    if symbol not in targets.SERVER_DICT:
                        print(f"Server {symbol!r} not found")
                        break
                else:
                    for symbol in command[1:]:
                        if symbol in targets.SERVER_DICT and targets.SERVER_DICT[symbol] not in servers:
                            servers.append(targets.SERVER_DICT[symbol])

            elif command[0] == "del":
                for symbol in command[1:]:
                    if symbol not in targets.SERVER_DICT:
                        print(f"Server {symbol!r} not found")
                        break
                else:
                    for symbol in command[1:]:
                        if symbol in targets.SERVER_DICT:
                            try:
                                servers.remove(targets.SERVER_DICT[symbol])
                            except ValueError:  # Not found
                                pass

            elif command[0] == "grid":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print_grid(compute_grid(payload, servers), [s.name for s in servers])

            elif command[0] == "fanout":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print_fanout(payload, servers, name_pattern, value_pattern, body_pattern)

            elif command[0] == "raw_fanout":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print_raw_fanout(payload, servers)

            elif command[0] == "transducer_fanout":
                transducers: list[Service]
                if len(command) == 1:
                    transducers = list(targets.TRANSDUCER_DICT.values())
                else:
                    try:
                        transducers = [targets.TRANSDUCER_DICT[t_name] for t_name in command[1:]]
                    except KeyError:
                        t_name = next(name for name in command[1:] if name not in targets.TRANSDUCER_DICT)
                        print(f"Transducer {t_name!r} not found")
                        continue
                print_transducer_fanout(payload, transducers)

            elif command[0] == "transduce":
                if len(command) == 1:
                    print("No transducer(s) selected!")
                    continue
                try:
                    transducers = [targets.TRANSDUCER_DICT[t_name] for t_name in command[1:]]
                except KeyError:
                    t_name = next(name for name in command[1:] if name not in targets.TRANSDUCER_DICT)
                    print(f"Transducer {t_name!r} not found")
                    continue
                tmp = payload
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

            elif command[0] == "adjust_host":
                if len(command) != 2 or command[1] not in ("on", "off"):
                    invalid_syntax()
                    continue
                adjusting_host = True if command[1] == "on" else False

            elif command[0] == "reload":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                importlib.reload(targets)
                new_servers: list[Service] = []
                for server in servers:
                    if server.name not in targets.SERVER_DICT:
                        print(f"{server.name} no longer available. Removing it from selection.")
                    else:
                        new_servers.append(targets.SERVER_DICT[server.name])
                servers = new_servers

            elif command[0] == "mutate":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                mutant: stream_t = mutate(payload)
                payload_history.append(mutant)
                print_stream(mutant, len(payload_history) - 1)

            elif command[0] == "b64decode":
                if len(command) != 2:
                    invalid_syntax()
                    continue
                try:
                    print(base64.b64decode(command[1]))
                except binascii.Error:
                    print(f"Cannot base64-decode {command[1]!r}")

            elif command[0] == "fuzz":
                if (
                    len(command) != 3
                    or not (command[1].isascii() and command[1].isdigit())
                    or not (command[2].isascii() and command[2].isdigit())
                ):
                    invalid_syntax()
                    continue
                seeds: list[stream_t] = SEEDS
                min_generation_size: int = int(command[1])
                num_generations: int = int(command[2])
                inputs: list[stream_t] = list(seeds)
                seen: set[fingerprint_t] = set()
                results: list[stream_t] = []
                for i in range(num_generations + 1):  # +1 because there's a zeroth generation: the seeds
                    try:
                        new_results, interesting = run_one_generation(servers, inputs, seen)
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
                        f"Generation {i}: {len(new_results)} discrepancies and {len(interesting)} new coverage tuples encountered."
                    )
                    if len(interesting) == 0:
                        interesting = inputs
                    # Generate new inputs
                    new_inputs: list[stream_t] = []
                    while len(new_inputs) < min_generation_size:
                        new_inputs.extend(map(mutate, interesting))
                    inputs = new_inputs
                durable_results: list[stream_t] = []
                for result in results:
                    for transduced in transducer_fanout(result, list(targets.TRANSDUCER_DICT.values())):
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

            else:
                invalid_syntax()
                continue


if __name__ == "__main__":
    main()
