import functools
import shlex
import pprint
import re
import shutil

from targets import SERVER_DICT, TRANSDUCER_DICT, Service
from http1 import HTTPRequest, HTTPResponse
from fanout import fanout, transducer_roundtrip, adjust_host_header, eager_pmap
from diff_fuzz import is_result
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
) -> str:  # You may want to consider using re.Pattern[bytes]
    r: str = repr(b)
    return r[:2] + highlight_pattern(r[2:-1], pattern) + r[-1:]


def print_fanout(
    payload: list[bytes],
    servers: list[Service],
    name_pattern: re.Pattern[str] | None,
    value_pattern: re.Pattern[str] | None,
    body_pattern: re.Pattern[str] | None,
) -> None:
    for s, (pts, _) in zip(servers, fanout(payload, servers, traced=False)):
        print(f"{s.name}: [")
        for r in pts:
            if isinstance(r, HTTPRequest):
                print("    \x1b[0;34mHTTPRequest\x1b[0m(")
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
                    f"    \x1b[0;31mHTTPResponse\x1b[0m(version={r.version!r}, method={r.code!r}, reason={r.reason!r}),"
                )

        print("]")


def try_transducer_roundtrip(payload: list[bytes], transducer: Service) -> list[bytes]:
    try:
        return transducer_roundtrip(payload, transducer)
    except ValueError as e:
        print(e)
        return []


def print_tfanout(payload: list[bytes], transducers: list[Service]) -> None:
    for t, result in zip(
        transducers, eager_pmap(functools.partial(try_transducer_roundtrip, payload), transducers)
    ):
        if len(result) == 0:
            print(f"{t.name}: []")
        else:
            print(f"{t.name}: [")
            for b in result:
                print(f"    {b!r},")
            print("]")


def grid(payload: list[bytes], servers: list[Service]) -> None:
    pts: list[list[HTTPRequest | HTTPResponse]] = [pt for pt, _ in fanout(payload, servers, traced=False)]
    column_width: int = max(map(len, (s.name for s in servers)))
    print("".ljust(column_width), *(server.name.ljust(column_width) for server in servers), sep=" ")
    for s1, pt1 in zip(servers, pts):
        print(s1.name.ljust(column_width), end=" ")
        for s2, pt2 in zip(servers, pts):
            if is_result([pt1, pt2], [s1, s2]):
                print("❌".ljust(column_width), end="")
            else:
                print("✅".ljust(column_width), end="")
        print()


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
    print("swap")
    print("    Swaps the current and previous payload.")

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

    print()

    print("grid")
    print(
        "    Sends the payload to the selected servers, then shows whether each pair\n    agrees on its interpretation."
    )
    print("fanout")
    print(
        "    Sends the payload to the selected servers, then shows each server's\n    interpretation of the payload."
    )
    print("tfanout")
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


def invalid_syntax() -> None:
    print("Invalid syntax. Try `help`.")


def main() -> None:
    servers: list[Service] = list(SERVER_DICT.values())
    transducers: list[Service] = []
    prev_payload: list[bytes] = []
    payload: list[bytes] = [b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"]
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
                print(f"All servers:     {' '.join(SERVER_DICT)}")
                print(f"All transducers: {' '.join(TRANSDUCER_DICT)}")
                print()
                print(f"Selected servers:     {' '.join(s.name for s in servers)}")
                print(f"Selected transducers: {' '.join(t.name for t in transducers)}")
                print()
                print(f'Previous payload: {" ".join(repr(p)[1:] for p in prev_payload)}')
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
                    if symbol not in SERVER_DICT | TRANSDUCER_DICT:
                        print(f"Server/transducer {symbol!r} not found")
                        break
                else:
                    for symbol in command[1:]:
                        pprint.pp((SERVER_DICT | TRANSDUCER_DICT)[symbol])

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
                    prev_payload = payload
                    payload = [
                        s.encode("latin1").decode("unicode-escape").encode("latin1") for s in command[1:]
                    ]
                except UnicodeEncodeError:
                    print("Unicode strings are not supported.")

            elif command[0] == "swap":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                prev_payload, payload = payload, prev_payload

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

            elif command[0] == "servers":
                if len(command) == 1:
                    print(*(s.name for s in servers))
                    continue
                for symbol in command[1:]:
                    if symbol not in SERVER_DICT:
                        print(f"Server {symbol!r} not found")
                        break
                else:
                    servers = [SERVER_DICT[s] for s in command[1:]]

            elif command[0] == "transducers":
                if len(command) == 1:
                    print(*(t.name for t in transducers))
                    continue
                for symbol in command[1:]:
                    if symbol not in TRANSDUCER_DICT:
                        print(f"Transducer {symbol!r} not found")
                        break
                else:
                    transducers = [TRANSDUCER_DICT[s] for s in command[1:]]

            elif command[0] == "add":
                for symbol in command[1:]:
                    if symbol not in SERVER_DICT | TRANSDUCER_DICT:
                        print(f"Server {symbol!r} not found")
                        break
                else:
                    for symbol in command[1:]:
                        if symbol in SERVER_DICT and SERVER_DICT[symbol] not in servers:
                            servers.append(SERVER_DICT[symbol])
                        elif symbol in TRANSDUCER_DICT and TRANSDUCER_DICT[symbol] not in transducers:
                            transducers.append(TRANSDUCER_DICT[symbol])

            elif command[0] == "del":
                for symbol in command[1:]:
                    if symbol not in SERVER_DICT | TRANSDUCER_DICT:
                        print(f"Server {symbol!r} not found")
                        break
                else:
                    for symbol in command[1:]:
                        if symbol in SERVER_DICT:
                            try:
                                servers.remove(SERVER_DICT[symbol])
                            except ValueError:  # Not found
                                pass
                        elif symbol in TRANSDUCER_DICT:
                            try:
                                transducers.remove(TRANSDUCER_DICT[symbol])
                            except ValueError:  # Not found
                                pass

            elif command[0] == "grid":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                grid(payload, servers)

            elif command[0] == "fanout":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print_fanout(payload, servers, name_pattern, value_pattern, body_pattern)

            elif command[0] == "tfanout":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                print_tfanout(payload, transducers)

            elif command[0] == "transduce":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                if len(transducers) == 0:
                    print("No transducer(s) selected!")
                    continue
                tmp = payload
                print(repr(tmp)[2:-1])
                for transducer in transducers:
                    try:
                        if adjusting_host:
                            tmp = adjust_host_header(tmp, transducer)
                        tmp = transducer_roundtrip(tmp, transducer)
                    except ValueError as e:
                        print(e)
                        break
                    if len(tmp) == 0:
                        print(f"{transducer.name} didn't respond")
                        break
                    else:
                        print(f"    ⬇️ \x1b[0;34m{transducer.name}\x1b[0m")
                        print(repr(tmp)[2:-1])
                else:
                    prev_payload = payload
                    payload = tmp

            elif command[0] == "adjust_host":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                adjusting_host = not adjusting_host

            elif command[0] == "mutate":
                if len(command) != 1:
                    invalid_syntax()
                    continue
                prev_payload, payload = payload, mutate(payload)
                print(payload)
            else:
                invalid_syntax()
                continue


if __name__ == "__main__":
    main()
