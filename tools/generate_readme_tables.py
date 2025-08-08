import yaml

def main() -> None:
    print("### HTTP Servers")
    print("| Name | Runs locally? | Coverage Collected? |")
    print("| ---- | ------------- | ------------------- |")

    with open("../docker-compose.yml", encoding="utf-8") as f:
        for service_name, service_props in yaml.safe_load(f)["services"].items():
            if "x-props" not in service_props:
                continue
            x_props = service_props["x-props"]
            if x_props["role"] == "origin":
                row = f"| [{service_name}]({service_props['build']['args'].get('APP_REPO')})"
                row += " | yes"
                row += " |"
                print(row)

    with open("../external-services.yml", encoding="utf-8") as f:
        for service_name, service_props in yaml.safe_load(f).items():
            x_props = service_props["x-props"]
            if x_props["role"] == "origin":
                row = f"| {service_name} "
                row += " | no"
                row += " |"
                print(row)

    print()

    print("### HTTP Transducers")
    print("| Name | Runs locally? |")
    print("| ---- | ------------- |")

    with open("../docker-compose.yml", encoding="utf-8") as f:
        for service_name, service_props in yaml.safe_load(f)["services"].items():
            if "x-props" not in service_props:
                continue
            x_props = service_props["x-props"]
            if x_props["role"] == "transducer":
                row = f"| [{service_name}]({service_props['build']['args'].get('APP_REPO')})"
                row += " | yes"
                row += " |"
                print(row)

    with open("../external-services.yml", encoding="utf-8") as f:
        for service_name, service_props in yaml.safe_load(f).items():
            x_props = service_props["x-props"]
            if x_props["role"] == "transducer":
                row = f"| {service_name}"
                row += " | no"
                row += " |"
                print(row)

if __name__ == "__main__":
    main()
