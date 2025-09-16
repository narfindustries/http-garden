from diff import ErrorType, categorize_discrepancy
from targets import Server
from http1 import HTTPRequest, HTTPResponse

Grid = tuple[tuple[ErrorType | None, ...], ...]
Clusters = tuple[tuple[Server, ...], ...]


def generate_grid(pts: list[list[HTTPRequest | HTTPResponse]], servers: list[Server]) -> Grid:
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


def generate_clusters(pts: list[list[HTTPRequest | HTTPResponse]], servers: list[Server]) -> Clusters:
    result: list[list[tuple[Server, list[HTTPRequest | HTTPResponse]]]] = []
    for pt, s in zip(pts, servers):
        for group in result:
            if all(categorize_discrepancy(pt, pt2, s, s2) == ErrorType.OK for s2, pt2 in group) or all(
                categorize_discrepancy(pt, pt2, s, s2) == ErrorType.INVALID for s2, pt2 in group
            ):
                group.append((s, pt))
                break
        else:
            result.append([(s, pt)])
    return tuple(tuple(map(lambda t: t[0], group)) for group in result)


def normalize_grid(grid: Grid) -> Grid:
    result: list[list[ErrorType | None]] = []
    for row in grid:
        result.append([])
        for entry in row:
            if entry in (ErrorType.RESPONSE_DISCREPANCY,):
                result[-1].append(ErrorType.OK)
            elif entry in (
                ErrorType.REQUEST_DISCREPANCY,
                ErrorType.TYPE_DISCREPANCY,
                ErrorType.STREAM_DISCREPANCY,
                ErrorType.INVALID,
            ):
                result[-1].append(ErrorType.DISCREPANCY)
            else:
                result[-1].append(entry)
    return tuple(map(tuple, result))
