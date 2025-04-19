import copy
import random

import tqdm

from targets import Server, Transducer
from grid import Grid, generate_grid
from mutations import mutate
from util import eager_pmap

def parallel_try_transduce(payload: list[bytes], transducers: list[Transducer]) -> list[list[bytes]]:
    return eager_pmap(lambda t: t.transduce(payload), transducers)

def fuzz(servers: list[Server], transducers: list[Transducer], num_goal_categories: int, initial_seeds: list[list[bytes]]) -> dict[Grid, tuple[list[bytes], list[bytes]]]:
    seeds: list[list[bytes]] = copy.deepcopy(initial_seeds)
    ignored_grids: frozenset[Grid] = frozenset(generate_grid(seed, servers) for seed in seeds)
    results: dict[Grid, list[bytes]] = {}
    for _ in tqdm.tqdm(range(num_goal_categories), desc="Fuzzing"):
        while True:
            payload: list[bytes] = mutate(random.choice(seeds))
            grid: Grid = generate_grid(payload, servers)
            if grid not in ignored_grids:
                if grid not in results: # Found a result
                    results[grid] = payload
                    break
            else:
                seeds.append(payload)

    durable_results: dict[Grid, tuple[list[bytes], list[bytes]]] = {}
    for result in tqdm.tqdm(results.values(), desc="Durability testing"):
        for transducer, transduced_payload in zip(transducers, parallel_try_transduce(result, transducers)):
            if len(transduced_payload) > 0:
                transduced_grid: Grid = generate_grid(transduced_payload, servers)
                if transduced_grid not in ignored_grids:
                    durable_results[transduced_grid] = (result, transduced_payload)

    return durable_results
