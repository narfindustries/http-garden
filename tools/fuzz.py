import copy
import random
import sys
import time

import tqdm

from targets import Server, Transducer
from grid import Grid, generate_grid, normalize_grid
from mutations import mutate
from util import eager_pmap

SEEDS: list[list[bytes]] = [
    [b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"],
    [b"POST / HTTP/1.1\r\nHost: whatever\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\r\n"],
    [b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"] * 2,
]

def parallel_try_transduce(payload: list[bytes], transducers: list[Transducer]) -> list[list[bytes]]:
    return eager_pmap(lambda t: t.transduce(payload), transducers)

def is_durable(payload: list[bytes], servers: list[Server], transducers: list[Transducer], transduced_grids: set[Grid]) -> bool:
    for transducer, transduced_payload in zip(transducers, parallel_try_transduce(payload, transducers)):
        if len(transduced_payload) > 0:
            transduced_grid: Grid = normalize_grid(generate_grid(transduced_payload, servers))
            if transduced_grid not in transduced_grids:
                transduced_grids.add(transduced_grid)
                return True
    return False

def fuzz(servers: list[Server], transducers: list[Transducer], num_goal_categories: int) -> dict[Grid, list[bytes]]:
    with open("results.txt", "w") as results_file:
        start_time: float = time.time()
        results_file.write(f"[{time.time()}] Fuzz start!\n")
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
                            results_file.write(f"[{time.time() - start_time}] New result: {payload!r}\n")
                            results[grid] = payload
                            break
                    else:
                        seeds.pop(payload_idx)
                        seeds.append(payload)
                        seeds.append(payload)
        except KeyboardInterrupt:
            pass
    
        try:
            results_file.write(f"[{time.time() - start_time}] Durability test start!\n")
            durable_results: dict[Grid, list[bytes]] = {}
            transduced_grids: set[Grid] = set()
            for grid, result in tqdm.tqdm(results.items(), desc="Durability testing"):
                for transducer, transduced_payload in zip(transducers, parallel_try_transduce(result, transducers)):
                    if len(transduced_payload) > 0:
                        transduced_grid: Grid = normalize_grid(generate_grid(transduced_payload, servers))
                        if transduced_grid not in transduced_grids:
                            results_file.write(f"[{time.time() - start_time}] Result is durable: {result!r}\n")
                            durable_results[grid] = result
                            transduced_grids.add(transduced_grid)
                            break
        except KeyboardInterrupt:
            pass

        results_file.write(f"[{time.time() - start_time}] Durability test end!\n")

    return durable_results
