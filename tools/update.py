"""This script runs through docker-compose.yml and checks if any of the commit hashes
are out of date.
"""

import os
import re
import subprocess

import tqdm
import yaml


def main() -> None:
    with open(f"{os.path.dirname(__file__)}/../docker-compose.yml", "r", encoding="ascii") as f:
        services: dict = yaml.safe_load(f).get("services")

    for name, service in tqdm.tqdm(services.items()):
        build: dict = service["build"]
        if "args" in build:
            if "x-props" in service and service["x-props"].get("version_frozen"):
                continue
            args: dict = build["args"]
            for key, val in list(args.items()):
                if key.endswith("_REPO"):
                    key_prefix: str = key[: -len("_REPO")]
                    output: str = subprocess.run(
                        ["git", "ls-remote", val],
                        capture_output=True,
                        check=True,
                    ).stdout.decode("latin1")
                    pattern: str = rf"(?:\A|\n)([0-9a-fA-F]+)\s+refs/heads/{service['build']['args'][f'{key_prefix}_BRANCH']}\n"
                    matches: list[str] = re.findall(pattern, output)
                    if len(matches) != 1:
                        raise ValueError(f"{name}'s repo doesn't have any matching branches!")
                    the_hash: str = matches[0]
                    args[f"{key_prefix}_VERSION"] = the_hash

    print(yaml.dump({"services": services}), end="")


if __name__ == "__main__":
    main()
