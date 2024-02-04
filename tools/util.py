""" This is where the extra random junk lives. """
import multiprocessing.pool

from typing import TypeVar, Iterable, Callable, Sequence

stream_t = list[bytes]
fingerprint_t = tuple[frozenset[int], ...]  # You might want to make this a hash.


_T = TypeVar("_T")
_U = TypeVar("_U")


def unzip(collection: Iterable[tuple[_T, _U]]) -> tuple[list[_T], list[_U]]:
    return ([p[0] for p in collection], [p[1] for p in collection])


def eager_pmap(f: Callable[[_U], _T], s: Sequence[_U]) -> list[_T]:
    with multiprocessing.pool.ThreadPool(32) as pool:
        return list(pool.map(f, s))


def translate(b: bytes, tr: dict[bytes, bytes]) -> bytes:
    result: bytes = b
    for old, new in tr.items():
        result = result.replace(old, new)
    return result
