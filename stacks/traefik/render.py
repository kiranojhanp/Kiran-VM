#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def render_template(path: Path, replacements: dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


def main() -> None:
    domain = required("DOMAIN_NAME_DEFAULT")
    acme_email = required("ACME_EMAIL_DEFAULT")
    komodo_label = required("KOMODO_SUBDOMAIN_LABEL")
    shared_network = required("SHARED_DOCKER_NETWORK")

    replacements = {
        "__DOMAIN_NAME__": domain,
        "__ACME_EMAIL__": acme_email,
        "__KOMODO_HOST__": f"{komodo_label}.{domain}",
        "__SITE_MESSAGE__": f"{domain} - coming soon",
        "__SHARED_NETWORK__": shared_network,
    }

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        ("compose.tmpl.yaml", ROOT / "compose.yaml"),
        ("traefik.tmpl.yml", CONFIG_DIR / "traefik.yml"),
        ("dynamic.tmpl.yml", CONFIG_DIR / "dynamic.yml"),
    ]

    for src_name, dst in files:
        src = ROOT / src_name
        rendered = render_template(src, replacements)
        dst.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
