import yaml


def main() -> None:
    print("### HTTP Servers")
    print("|-|")
    with open("../docker-compose.yml", encoding="utf-8") as f:
        for service_name, service_props in yaml.safe_load(f)["services"].items():
            if "x-props" not in service_props:
                continue
            x_props = service_props["x-props"]
            if x_props["role"] == "origin":
                print(f"| [{service_name}]({service_props['build']['args'].get('APP_REPO')}) |")
    print()

    print("### HTTP Transducers")
    print("|-|")
    with open("../docker-compose.yml", encoding="utf-8") as f:
        for service_name, service_props in yaml.safe_load(f)["services"].items():
            if "x-props" not in service_props:
                continue
            x_props = service_props["x-props"]
            if x_props["role"] == "transducer":
                print(f"| [{service_name}]({service_props['build']['args'].get('APP_REPO')}) |")


if __name__ == "__main__":
    main()
