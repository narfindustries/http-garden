import copy
import random
import sys

import tqdm

from targets import Server, Transducer
from grid import Grid, generate_grid, normalize_grid
from mutations import mutate
from util import eager_pmap

SEEDS: list[list[bytes]] = [
    [b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"],
    [b"POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\r\n"],
    [b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n", b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"],
]

def parallel_try_transduce(payload: list[bytes], transducers: list[Transducer]) -> list[list[bytes]]:
    return eager_pmap(lambda t: t.transduce(payload), transducers)

def fuzz(servers: list[Server], transducers: list[Transducer], num_goal_categories: int) -> dict[Grid, tuple[list[bytes], list[bytes]]]:
    seeds: list[list[bytes]] = copy.deepcopy(SEEDS)
    ignored_grids: frozenset[Grid] = frozenset(normalize_grid(generate_grid(seed, servers)) for seed in seeds)
    results: dict[Grid, list[bytes]] = {}
    try:
        for _ in tqdm.tqdm(range(num_goal_categories), desc="Fuzzing"):
            while True:
                payload_idx: int = random.randint(0, len(seeds) - 1)
                payload: list[bytes] = mutate(seeds[payload_idx])
                grid: Grid = normalize_grid(generate_grid(payload, servers))
                if grid not in ignored_grids:
                    if grid not in results: # Found a result
                        results[grid] = payload
                        break
                else:
                    seeds.pop(payload_idx)
                    seeds.append(payload)
                    seeds.append(payload)
    except KeyboardInterrupt:
        pass

    durable_results: dict[Grid, tuple[list[bytes], list[bytes]]] = {}
    transduced_grids: set[Grid] = set()
    for result in tqdm.tqdm(results.values(), desc="Durability testing"):
        for transducer, transduced_payload in zip(transducers, parallel_try_transduce(result, transducers)):
            if len(transduced_payload) > 0:
                transduced_grid: Grid = normalize_grid(generate_grid(transduced_payload, servers))
                if transduced_grid not in transduced_grids:
                    durable_results[transduced_grid] = (result, transduced_payload)
                    transduced_grids.add(transduced_grid)
                    break

    print(f"{len(durable_results)}/{len(results)} durable results found.", file=sys.stderr)

    return durable_results
