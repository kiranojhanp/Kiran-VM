#!/usr/bin/env python3

import json
import re
import subprocess
import sys
from collections import defaultdict


def main() -> int:
    ids = subprocess.check_output(["docker", "ps", "-q"], text=True).split()
    if not ids:
        print("No running containers; skipping Traefik route uniqueness check")
        return 0

    containers = json.loads(
        subprocess.check_output(["docker", "inspect", *ids], text=True)
    )
    host_to_containers: dict[str, set[str]] = defaultdict(set)

    for container in containers:
        name = (container.get("Name") or "").lstrip("/") or "unknown"
        labels = (container.get("Config") or {}).get("Labels") or {}
        if str(labels.get("traefik.enable", "")).lower() != "true":
            continue

        for key, value in labels.items():
            if not (key.startswith("traefik.http.routers.") and key.endswith(".rule")):
                continue
            if not isinstance(value, str):
                continue
            if "Host(" not in value and "HostRegexp(" not in value:
                continue

            for host in re.findall(r"`([^`]+)`", value):
                host_to_containers[host.lower()].add(name)

    duplicates = {
        host: sorted(container_names)
        for host, container_names in host_to_containers.items()
        if len(container_names) > 1
    }

    if duplicates:
        print("Duplicate Traefik host routes detected:")
        for host, container_names in sorted(duplicates.items()):
            print(f"  {host}: {', '.join(container_names)}")
        print(
            "Fix: keep one stack per app/host and remove duplicate containers or labels"
        )
        return 2

    print("Traefik host routes are unique")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
