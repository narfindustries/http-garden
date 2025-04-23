from diff import ErrorType, categorize_discrepancy
from targets import Server
from fanout import fanout
from http1 import HTTPRequest, HTTPResponse

Grid = tuple[tuple[ErrorType | None, ...], ...]


def generate_grid(payload: list[bytes], servers: list[Server]) -> Grid:
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

def normalize_grid(grid: Grid) -> Grid:
    result: list[list[ErrorType | None]] = []
    for row in grid:
        result.append([])
        for entry in row:
            if entry in (ErrorType.RESPONSE_DISCREPANCY,):
                result[-1].append(ErrorType.OK)
            elif entry in (ErrorType.REQUEST_DISCREPANCY, ErrorType.TYPE_DISCREPANCY, ErrorType.STREAM_DISCREPANCY, ErrorType.INVALID):
                result[-1].append(ErrorType.DISCREPANCY)
            else:
                result[-1].append(entry)
    return tuple(map(tuple, result))
