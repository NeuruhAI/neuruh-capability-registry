from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .core import CapabilityError, CapabilityRegistry


def _json_object(value: str) -> dict:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("arguments must be a JSON object")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="neuruh-capability-registry")
    parser.add_argument("manifest", help="path to a capability manifest")
    parser.add_argument(
        "--operation",
        help="operation to validate; validates manifest structure when omitted",
    )
    parser.add_argument(
        "--args",
        type=_json_object,
        default={},
        help="JSON object containing operation arguments",
    )
    args = parser.parse_args(argv)

    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        registry = CapabilityRegistry.from_manifest(manifest)
        if args.operation:
            registry.validate_args(args.operation, args.args)
    except (OSError, json.JSONDecodeError, CapabilityError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    if args.operation:
        print(f"VALID {args.operation}")
    else:
        print(f"VALID {len(registry.list())} capabilities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
