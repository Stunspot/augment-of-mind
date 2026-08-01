"""Administrative CLI and stdio service entrypoint for MIND Core Phase 1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .core import MindCore
from .errors import MindCoreError
from .service import serve
from .util import canonical_json


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mind-core")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "status", "serve"):
        command = subparsers.add_parser(name)
        command.add_argument("--database", required=True, type=Path)
    bootstrap = subparsers.add_parser("bootstrap")
    bootstrap.add_argument("--database", required=True, type=Path)
    bootstrap.add_argument("--manifest", required=True, type=Path)
    return parser


def _write_json(value: Any) -> None:
    sys.stdout.buffer.write((canonical_json(value) + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        with MindCore(args.database) as core:
            if args.command == "init":
                _write_json(core.status())
                return 0
            if args.command == "status":
                _write_json(core.status())
                return 0
            if args.command == "bootstrap":
                manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
                if not isinstance(manifest, dict):
                    raise ValueError("bootstrap manifest must be a JSON object")
                _write_json(core.bootstrap(manifest))
                return 0
            if args.command == "serve":
                return serve(core, sys.stdin.buffer, sys.stdout.buffer)
    except (MindCoreError, OSError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"mind-core: {exc}\n")
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
