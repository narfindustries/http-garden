import sys

import yaml

print("### HTTP Servers")
print("| Name | Runs locally? | Coverage Collected? |")
print("| ---- | ------------- | ------------------- |")

for service_name, service_props in yaml.safe_load(open("../docker-compose.yml"))["services"].items():
    if "x-props" not in service_props:
        continue
    x_props = service_props["x-props"]
    if x_props["role"] == "server":
        row = f"| [{service_name}]({service_props['build']['args'].get('APP_REPO')})"
        row += " | yes"
        row += f" | {'yes' if (x_props.get('is-traced')) else 'no'}"
        row += " |"
        print(row)

for service_name, service_props in yaml.safe_load(open("../external-services.yml")).items():
    x_props = service_props["x-props"]
    if x_props["role"] == "server":
        row = f"| {service_name} "
        row += " | no"
        row += f" | no"
        row += " |"
        print(row)

print()

print("### HTTP Proxies")
print("| Name | Runs locally? |")
print("| ---- | ------------- |")

for service_name, service_props in yaml.safe_load(open("../docker-compose.yml"))["services"].items():
    if "x-props" not in service_props:
        continue
    x_props = service_props["x-props"]
    if x_props["role"] == "transducer":
        row = f"| [{service_name}]({service_props['build']['args'].get('APP_REPO')})"
        row += " | yes"
        row += " |"
        print(row)

for service_name, service_props in yaml.safe_load(open("../external-services.yml")).items():
    x_props = service_props["x-props"]
    if x_props["role"] == "transducer":
        row = f"| {service_name}"
        row += " | no"
        row += " |"
        print(row)
