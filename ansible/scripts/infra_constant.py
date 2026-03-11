#!/usr/bin/env python3
"""Read selected shared constants from infra/constants.py.

Usage:
  python3 scripts/infra_constant.py SSH_PORT_INITIAL
  python3 scripts/infra_constant.py SSH_PORT_HARDENED
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys


def load_constants_module():
    ansible_dir = pathlib.Path(__file__).resolve().parents[1]
    constants_path = ansible_dir.parent / "infra" / "constants.py"

    spec = importlib.util.spec_from_file_location("infra_constants", constants_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load constants module: {constants_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: infra_constant.py <NAME>", file=sys.stderr)
        return 2

    name = sys.argv[1]
    constants = load_constants_module()

    if not hasattr(constants, name):
        print(f"Unknown constant: {name}", file=sys.stderr)
        return 1

    print(getattr(constants, name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
