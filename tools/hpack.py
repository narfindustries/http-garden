import itertools
import functools
import dataclasses
from typing import Iterable, Self, Final


def serialize_prefix_int(i: int, prefix_len: int, preprefix: int = 0, padding: int = 0) -> bytes:
    assert 0 <= i
    assert 1 <= prefix_len <= 8
    assert 0 <= preprefix < (1 << (8 - prefix_len))

    if i < ((1 << prefix_len) - 1):
        return bytes([(preprefix << prefix_len) | i])
    result: list[int] = [(preprefix << prefix_len) | ((1 << prefix_len) - 1)]
    i -= (1 << prefix_len) - 1
    while i >= 128:
        result.append(0x80 | (i & 0x7F))
        i //= 128
    result.append(i)
    result += [0] * padding
    return bytes(result)


def parse_prefix_int(data: Iterable[int], prefix_len: int) -> int:
    assert 1 <= prefix_len <= 8
    data = iter(data)
    prefix_byte: int = next(data)
    prefix_mask: int = (1 << prefix_len) - 1
    result: int = prefix_byte & prefix_mask
    if result != prefix_mask:
        return result

    m: int = 0
    for b in data:
        result += (b & 0x7F) * (1 << m)
        m += 7
        if ((b >> 7) & 1) == 0:
            break
    else:
        assert False
    return result

# From RFC 7541, Appendix B
HUFFMAN_CODEWORDS: Final[tuple[tuple[bool, ...], ...]] = (
    (True, True, True, True, True, True, True, True, True, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True),
    (False, True, False, True, False, False),
    (True, True, True, True, True, True, True, False, False, False),
    (True, True, True, True, True, True, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, False, False, True),
    (False, True, False, True, False, True),
    (True, True, True, True, True, False, False, False),
    (True, True, True, True, True, True, True, True, False, True, False),
    (True, True, True, True, True, True, True, False, True, False),
    (True, True, True, True, True, True, True, False, True, True),
    (True, True, True, True, True, False, False, True),
    (True, True, True, True, True, True, True, True, False, True, True),
    (True, True, True, True, True, False, True, False),
    (False, True, False, True, True, False),
    (False, True, False, True, True, True),
    (False, True, True, False, False, False),
    (False, False, False, False, False),
    (False, False, False, False, True),
    (False, False, False, True, False),
    (False, True, True, False, False, True),
    (False, True, True, False, True, False),
    (False, True, True, False, True, True),
    (False, True, True, True, False, False),
    (False, True, True, True, False, True),
    (False, True, True, True, True, False),
    (False, True, True, True, True, True),
    (True, False, True, True, True, False, False),
    (True, True, True, True, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, False, False),
    (True, False, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, False, True, True),
    (True, True, True, True, True, True, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, False, True, False),
    (True, False, False, False, False, True),
    (True, False, True, True, True, False, True),
    (True, False, True, True, True, True, False),
    (True, False, True, True, True, True, True),
    (True, True, False, False, False, False, False),
    (True, True, False, False, False, False, True),
    (True, True, False, False, False, True, False),
    (True, True, False, False, False, True, True),
    (True, True, False, False, True, False, False),
    (True, True, False, False, True, False, True),
    (True, True, False, False, True, True, False),
    (True, True, False, False, True, True, True),
    (True, True, False, True, False, False, False),
    (True, True, False, True, False, False, True),
    (True, True, False, True, False, True, False),
    (True, True, False, True, False, True, True),
    (True, True, False, True, True, False, False),
    (True, True, False, True, True, False, True),
    (True, True, False, True, True, True, False),
    (True, True, False, True, True, True, True),
    (True, True, True, False, False, False, False),
    (True, True, True, False, False, False, True),
    (True, True, True, False, False, True, False),
    (True, True, True, True, True, True, False, False),
    (True, True, True, False, False, True, True),
    (True, True, True, True, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, False, False),
    (True, False, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, False, True),
    (False, False, False, True, True),
    (True, False, False, False, True, True),
    (False, False, True, False, False),
    (True, False, False, True, False, False),
    (False, False, True, False, True),
    (True, False, False, True, False, True),
    (True, False, False, True, True, False),
    (True, False, False, True, True, True),
    (False, False, True, True, False),
    (True, True, True, False, True, False, False),
    (True, True, True, False, True, False, True),
    (True, False, True, False, False, False),
    (True, False, True, False, False, True),
    (True, False, True, False, True, False),
    (False, False, True, True, True),
    (True, False, True, False, True, True),
    (True, True, True, False, True, True, False),
    (True, False, True, True, False, False),
    (False, True, False, False, False),
    (False, True, False, False, True),
    (True, False, True, True, False, True),
    (True, True, True, False, True, True, True),
    (True, True, True, True, False, False, False),
    (True, True, True, True, False, False, True),
    (True, True, True, True, False, True, False),
    (True, True, True, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, False, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, True),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, False, False, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, True, True, False),
    (True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True),
)

_huffman_tree_t = None | int | list["_huffman_tree_t"]
_huffman_tree: _huffman_tree_t = [None, None]

def _build_huffman_tree() -> None:
    for i, codeword in enumerate(HUFFMAN_CODEWORDS):
        path: _huffman_tree_t = _huffman_tree
        for bit in codeword[:-1]:
            assert isinstance(path, list)
            if path[bit] is None:
                path[bit] = [None, None]
            path = path[bit]
        last_bit: int = codeword[-1]
        assert isinstance(path, list)
        path[last_bit] = i


_build_huffman_tree()


STATIC_TABLE: Final[tuple[tuple[bytes, bytes], ...]] = (
    (b":authority", b""),
    (b":method", b"GET"),
    (b":method", b"POST"),
    (b":path", b"/"),
    (b":path", b"/index.html"),
    (b":scheme", b"http"),
    (b":scheme", b"https"),
    (b":status", b"200"),
    (b":status", b"204"),
    (b":status", b"206"),
    (b":status", b"304"),
    (b":status", b"400"),
    (b":status", b"404"),
    (b":status", b"500"),
    (b"accept-charset", b""),
    (b"accept-encoding", b"gzip, deflate"),
    (b"accept-language", b""),
    (b"accept-ranges", b""),
    (b"accept", b""),
    (b"access-control-allow-origin", b""),
    (b"age", b""),
    (b"allow", b""),
    (b"authorization", b""),
    (b"cache-control", b""),
    (b"content-disposition", b""),
    (b"content-encoding", b""),
    (b"content-language", b""),
    (b"content-length", b""),
    (b"content-location", b""),
    (b"content-range", b""),
    (b"content-type", b""),
    (b"cookie", b""),
    (b"date", b""),
    (b"etag", b""),
    (b"expect", b""),
    (b"expires", b""),
    (b"from", b""),
    (b"host", b""),
    (b"if-match", b""),
    (b"if-modified-since", b""),
    (b"if-none-match", b""),
    (b"if-range", b""),
    (b"if-unmodified-since", b""),
    (b"last-modified", b""),
    (b"link", b""),
    (b"location", b""),
    (b"max-forwards", b""),
    (b"proxy-authenticate", b""),
    (b"proxy-authorization", b""),
    (b"range", b""),
    (b"referer", b""),
    (b"refresh", b""),
    (b"retry-after", b""),
    (b"server", b""),
    (b"set-cookie", b""),
    (b"strict-transport-security", b""),
    (b"transfer-encoding", b""),
    (b"user-agent", b""),
    (b"vary", b""),
    (b"via", b""),
    (b"www-authenticate", b""),
)


@dataclasses.dataclass
class HPACKState:
    dynamic_table: list[tuple[bytes, bytes]] = dataclasses.field(default_factory=list)
    table_size: int = 4096
    max_table_size: int = 4096

    def __post_init__(self: Self) -> None:
        assert 0 <= self.max_table_size
        assert 0 <= self.table_size <= self.max_table_size
        assert len(self.dynamic_table) <= self.table_size

    def add_header(self: Self, header: tuple[bytes, bytes]) -> None:
        self.dynamic_table = [header] + self.dynamic_table
        self.dynamic_table = self.dynamic_table[: self.table_size]

    def get_header(self: Self, index: int) -> tuple[bytes, bytes]:
        assert index > 0
        index -= 1
        if index < len(STATIC_TABLE):
            return STATIC_TABLE[index]
        index -= len(STATIC_TABLE)
        return self.dynamic_table[index]

    def update_table_size(self: Self, val: int) -> None:
        self.table_size = val
        self.__post_init__()

    def update_max_table_size(self: Self, val: int) -> None:
        self.max_table_size = val
        self.__post_init__()

    def handle_entry(self: Self, data: Iterable[int]) -> tuple[bytes, bytes] | None:
        data = iter(data)
        prefix_byte: int = next(data)
        data = itertools.chain(iter([prefix_byte]), data)

        index: int
        result: tuple[bytes, bytes]
        if prefix_byte & 0b10000000 == 0b10000000:
            return self.get_header(parse_prefix_int(data, 7))
        if prefix_byte & 0b11000000 == 0b01000000:
            index = parse_prefix_int(data, 6)
            result = (self.get_header(index)[0] if index != 0 else parse_string_literal(data), parse_string_literal(data))
            self.add_header(result)
            return result
        if prefix_byte & 0b11110000 == 0b00000000 or prefix_byte & 0b11110000 == 0b00010000:
            index = parse_prefix_int(data, 6)
            result = (self.get_header(index)[0] if index != 0 else parse_string_literal(data), parse_string_literal(data))
            return result
        if prefix_byte & 0b11100000 == 0b00100000:
            size: int = parse_prefix_int(data, 5)
            self.update_table_size(size)
            return None
        assert False


def parse_string_literal(data: Iterable[int]) -> bytes:
    data = iter(data)
    prefix_byte: int = next(data)
    data = itertools.chain(iter([prefix_byte]), data)

    is_compressed: bool = bool(prefix_byte & 0x80)
    length: int = parse_prefix_int(data, 7)
    raw_result: bytes = bytes([b for _, b in zip(range(length), data)])
    if not is_compressed:
        return raw_result

    result: list[int] = []
    path: _huffman_tree_t = _huffman_tree
    codeword: list[int] = []
    for byte in raw_result:
        for bit in [(byte >> (7 - i)) & 1 for i in range(8)]:
            codeword.append(bit)
            assert isinstance(path, list)
            path = path[bit]
            if isinstance(path, int):
                # A Huffman-encoded string literal containing the EOS symbol
                # MUST be treated as a decoding error.
                assert path != 256
                result.append(path)
                path = _huffman_tree
                codeword = []
    #   As the Huffman-encoded data doesn't always end at an octet boundary,
    #   some padding is inserted after it, up to the next octet boundary.  To
    #   prevent this padding from being misinterpreted as part of the string
    #   literal, the most significant bits of the code corresponding to the
    #   EOS (end-of-string) symbol are used.
    assert all(b == 1 for b in codeword)
    return bytes(result)

def serialize_string_literal(data: Iterable[int], compressed: bool = False, length_padding: int = 0) -> bytes:
    raw_string: list[bool] = []
    for code_point in data:
        if compressed:
            assert 0 <= code_point <= 256
            raw_string.extend(HUFFMAN_CODEWORDS[code_point])
        else:
            assert 0 <= code_point < 256 # Can't have EOS in an uncompressed header
            raw_string.extend(bool(((code_point >> (7 - i)) & 1)) for i in range(8))
    while len(raw_string) % 8 != 0: # TODO: Support arbitrary padding. This is challenging because we may want more than 8 bits of it :)
        raw_string.append(True)

    string: bytes = bytes(functools.reduce(int.__or__, (raw_string[i * 8 + j] << (7 - j) for j in range(8))) for i in range(len(raw_string) // 8))
    return serialize_prefix_int(len(string), 7, preprefix=int(compressed), padding=length_padding) + string
