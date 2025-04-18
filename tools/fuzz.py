import copy
import random

import tqdm

from targets import Server, Transducer
from grid import Grid, generate_grid
from mutations import mutate

def fuzz(servers: list[Server], transducers: list[Transducer], num_goal_categories: int, initial_seeds: list[list[bytes]]) -> dict[Grid, list[list[bytes]]]:
    seeds: list[list[bytes]] = copy.deepcopy(initial_seeds)
    ignored_grids: frozenset[Grid] = frozenset(generate_grid(seed, servers) for seed in seeds)
    result: dict[Grid, list[list[bytes]]] = {}
    for i in tqdm.tqdm(range(num_goal_categories)):
        while True:
            payload: list[bytes] = mutate(random.choice(seeds))
            grid: Grid = generate_grid(payload, servers)
            if grid not in ignored_grids:
                if grid not in result: # Found a result
                    result[grid] = [payload]
                    break
                else: # Duplicate result
                    result[grid].append(payload)
            else:
                seeds.append(payload)
    return result
