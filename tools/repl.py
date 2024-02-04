""" The Garden repl """

import base64
import binascii
import functools
import importlib
import shlex
import pprint
import re

import targets  # This gets reloaded, so we import the whole module
from targets import Service  # This won't change across reloads
from http1 import HTTPRequest, HTTPResponse
from fanout import fanout, transducer_roundtrip, adjust_host_header, server_roundtrip
from util import stream_t, fingerprint_t, eager_pmap
from diff_fuzz import run_one_generation, is_result, SEEDS
from mutations import mutate


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


def print_transducer_fanout(payload: stream_t, transducers: list[Service]) -> None:
    for t, result in zip(
        transducers, eager_pmap(functools.partial(try_transducer_roundtrip, payload), transducers)
    ):
        print(f"\x1b[0;34m{t.name}\x1b[0m:")  # Blue
        print(" ".join(repr(b)[1:] for b in result))


def print_raw_fanout(payload: stream_t, servers: list[Service]) -> None:
    for server, result in zip(servers, eager_pmap(functools.partial(server_roundtrip, payload), servers)):
        print(f"\x1b[0;34m{server.name}\x1b[0m:")  # Blue
        for r in result:
            print(f"    {repr(r)[1:]}")


def compute_grid(payload: stream_t, servers: list[Service]) -> tuple[tuple[bool, ...], ...]:
    pts: list[list[HTTPRequest | HTTPResponse]] = [pt for pt, _ in fanout(payload, servers, traced=False)]
    return tuple(
        tuple(is_result([pt1, pt2], [s1, s2]) for s2, pt2 in zip(servers, pts))
        for s1, pt1 in zip(servers, pts)
    )


def print_bool_grid(bool_grid: tuple[tuple[bool, ...], ...], labels: list[str]) -> None:
    column_width: int = max(map(len, labels))
    print("".ljust(column_width), *(label.ljust(column_width) for label in labels), sep=" ")
    for row_label, row in zip(labels, bool_grid):
        print(row_label.ljust(column_width), end=" ")
        for entry in row:
            print(("❌" if entry else "✅").ljust(column_width), end="")
        print()


def print_stream(stream: stream_t, id_no: int) -> None:
    print(f"[{id_no}]:", " ".join(repr(b)[1:] for b in stream))


def print_help_message() -> None:
    print("This is the HTTP Garden repl. It is best run within rlwrap(1).")

    print()

    print("help")
    print("    Shows this message.")
    print("env")
    print("    Shows the current state of the repl (selected servers/transducers, payload, etc.)")
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
    print("transducers <transducer> [transducer]*")
    print("    Selects the specified transducers.")
    print("add [server|transducer]*")
    print("    Adds the specified server(s) and/or transducer(s) to the selection.")
    print("del [server|transducer]*")
    print("    Removes the specified server(s) and/or transducer(s) from the selection.")

    print()

    print("pattern name|value|body <regex>")
    print(
        "    Sets the specified pattern to the specified Python regular expression. Matches to this\n    regex in the specified portion of the request will be highlighted in fanout output."
    )

    print()

    print("mutate")
    print("    Mutates the current payload using a random choice of the mutation operations.")
    print("fuzz <n>")
    print(
        "    Runs the differential fuzzer for n generations on the selected servers, then reports the results."
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
    print("transducer_fanout")
    print(
        "    Sends the payload to the selected transducers simultaneously, then shows\n    each transducer's output."
    )
    print("transduce")
    print(
        "    Sends the payload through all of the transducers in sequence,\n    then saves the result in payload."
    )

    print()

    print("adjust_host")
    print(
        "    Toggles whether the host header is automatically adjusted before sending\n    requests to transducers. Some transducers, especially CDNs, will require this."
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
    transducers: list[Service] = []
    payload_history: list[stream_t] = [_INITIAL_PAYLOAD]
    adjusting_host: bool = False
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

        tokens: list[str] = [t[1:-1] if t[0] == t[-1] and t[0] in "\"'" else t for t in shlex.shlex(line)]
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
                print(f"All servers:     {' '.join(targets.SERVER_DICT)}")
                print(f"All transducers: {' '.join(targets.TRANSDUCER_DICT)}")
                print()
                print(f"Selected servers:     {' '.join(s.name for s in servers)}")
                print(f"Selected transducers: {' '.join(t.name for t in transducers)}")
                print()
                print(f'Payload:          {" ".join(repr(p)[1:] for p in payload)}')
                print()
                print(f"Name pattern:  {name_pattern and name_pattern.pattern!r}")
                print(f"Value pattern: {value_pattern and value_pattern.pattern!r}")
                print(f"Body pattern:  {body_pattern and body_pattern.pattern!r}")
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
                    print(repr(payload)[2:-1])
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
                if len(command) == 1:
                    print(*(t.name for t in transducers))
                    continue
                for symbol in command[1:]:
                    if symbol not in targets.TRANSDUCER_DICT:
                        print(f"Transducer {symbol!r} not found")
                        break
                else:
                    transducers = [targets.TRANSDUCER_DICT[s] for s in command[1:]]

            elif command[0] == "add":
                for symbol in command[1:]:
                    if symbol not in targets.SERVER_DICT | targets.TRANSDUCER_DICT:
                        print(f"Server {symbol!r} not found")
                        break
                else:
                    for symbol in command[1:]:
                        if symbol in targets.SERVER_DICT and targets.SERVER_DICT[symbol] not in servers:
                            servers.append(targets.SERVER_DICT[symbol])
                        elif (
                            symbol in targets.TRANSDUCER_DICT
                            and targets.TRANSDUCER_DICT[symbol] not in transducers
                        ):
                            transducers.append(targets.TRANSDUCER_DICT[symbol])

            elif command[0] == "del":
                for symbol in command[1:]:
                    if symbol not in targets.SERVER_DICT | targets.TRANSDUCER_DICT:
                        print(f"Server {symbol!r} not found")
                        break
                else:
                    for symbol in command[1:]:
                        if symbol in targets.SERVER_DICT:
                            try:
                                servers.remove(targets.SERVER_DICT[symbol])
                            except ValueError:  # Not found
                                pass
                        elif symbol in targets.TRANSDUCER_DICT:
                            try:
                                transducers.remove(targets.TRANSDUCER_DICT[symbol])
                            except ValueError:  # Not found
                                pass

            elif command[0] == "grid":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print_bool_grid(compute_grid(payload, servers), [s.name for s in servers])

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
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print_transducer_fanout(payload, transducers)

            elif command[0] == "transduce":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                if len(transducers) == 0:
                    print("No transducer(s) selected!")
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
                if len(command) != 1:
                    invalid_syntax()
                    continue
                adjusting_host = not adjusting_host

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
                new_transducers: list[Service] = []
                for transducer in transducers:
                    if transducer.name not in targets.TRANSDUCER_DICT:
                        print(f"{transducer.name} no longer available. Removing it from selection.")
                    else:
                        new_transducers.append(targets.TRANSDUCER_DICT[transducer.name])
                transducers = new_transducers

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
                if len(command) != 2 or not (command[1].isascii() and command[1].isdigit()):
                    invalid_syntax()
                    continue
                num_generations: int = int(command[1])
                seeds: list[stream_t] = SEEDS
                min_generation_size: int = 75
                inputs: list[stream_t] = list(seeds)
                seen: set[fingerprint_t] = set()
                results: list[stream_t] = []
                for i in range(num_generations + 1):  # +1 because there's a zeroth generation: the seeds
                    new_results, interesting = run_one_generation(servers, inputs, seen)
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
                categorized_results: dict[tuple[tuple[bool, ...], ...], list[stream_t]] = {}
                for result in results:
                    grid: tuple[tuple[bool, ...], ...] = compute_grid(result, servers)
                    if grid not in categorized_results:
                        categorized_results[grid] = []
                    categorized_results[grid].append(result)
                for grid, result_list in categorized_results.items():
                    for result in result_list:
                        payload_history.append(result)
                        print_stream(result, len(payload_history) - 1)
                    print_bool_grid(grid, [s.name for s in servers])

            else:
                invalid_syntax()
                continue


if __name__ == "__main__":
    main()
