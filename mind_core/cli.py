"""Administrative CLI and cooperative H0 entrypoints for MIND Core."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .core import MindCore
from .errors import MindCoreError
from .service import QueryService, serve
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
    index = subparsers.add_parser("index")
    index.add_argument("--database", required=True, type=Path)
    index.add_argument("--manifest", required=True, type=Path)
    issue = subparsers.add_parser("issue-session-capability")
    issue.add_argument("--database", required=True, type=Path)
    issue.add_argument("--agent-instance-id", required=True)
    issue.add_argument("--host-session-id", required=True)
    issue.add_argument(
        "--exposure-scope",
        choices=("public_only", "public_and_agent_private"),
        default="public_only",
    )
    issue.add_argument("--expires-at")
    revoke = subparsers.add_parser("revoke-session-capability")
    revoke.add_argument("--database", required=True, type=Path)
    revoke.add_argument("--session-capability", required=True)
    query = subparsers.add_parser("query")
    query.add_argument("--database", required=True, type=Path)
    query.add_argument("--request", required=True, type=Path)
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
            if args.command == "index":
                manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
                if not isinstance(manifest, dict):
                    raise ValueError("associative index manifest must be a JSON object")
                _write_json(core.reminders.ingest_index(manifest))
                return 0
            if args.command == "issue-session-capability":
                _write_json(
                    core.reminders.issue_session_capability(
                        args.agent_instance_id,
                        args.host_session_id,
                        exposure_scope=args.exposure_scope,
                        expires_at=args.expires_at,
                    )
                )
                return 0
            if args.command == "revoke-session-capability":
                _write_json(
                    core.reminders.revoke_session_capability(
                        args.session_capability
                    )
                )
                return 0
            if args.command == "query":
                request = json.loads(args.request.read_text(encoding="utf-8"))
                if not isinstance(request, dict):
                    raise ValueError("query request must be a JSON object")
                _write_json(QueryService(core).handle(request))
                return 0
            if args.command == "serve":
                return serve(core, sys.stdin.buffer, sys.stdout.buffer)
    except (MindCoreError, OSError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"mind-core: {exc}\n")
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
