"""Inject one bounded MIND Arm's Reach field through Codex UserPromptSubmit."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

PLUGIN_ROOT = Path(os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(PLUGIN_ROOT))

from mind_core.hook_delivery import (  # noqa: E402
    HOOK_EVENT,
    new_receipt_seed,
    write_receipt,
)
from mind_core.hook_runtime import (  # noqa: E402
    FINALIZATION_RESERVE_SECONDS,
    HOOK_WALL_SECONDS,
    HookRuntimeError,
    degraded_preparation,
    run_prepare_subprocess,
    summarize_stage_markers,
)
from mind_core.util import canonical_json, timestamp  # noqa: E402


def _configure_standard_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def _round_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000.0, 3)


def _attach_stage_evidence(
    receipt: dict[str, Any],
    markers: list[dict[str, Any]],
    fixed_timings: dict[str, float],
) -> None:
    summary = summarize_stage_markers(markers)
    timings = dict(summary.pop("stage_timings_ms", {}))
    timings.update(fixed_timings)
    receipt["stage_timings_ms"] = timings
    receipt.update(summary)


def main() -> int:
    hook_started = perf_counter()
    _configure_standard_streams()
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError("hook input must be an object")
    except (json.JSONDecodeError, ValueError):
        event = {"hook_event_name": HOOK_EVENT, "prompt": "", "turn_id": ""}
    input_parse_ms = _round_ms(hook_started)

    receipt_seed = new_receipt_seed(event)
    started_receipt = {
        **receipt_seed,
        "evidence_state": "started",
        "claimed_boundary": "hook invocation observed; field not prepared or returned",
        "current_stage": "dispatch",
        "stage_timings_ms": {"input_parse": input_parse_ms},
    }
    started_receipt_persisted = write_receipt(started_receipt)

    worker_started = perf_counter()
    markers: list[dict[str, Any]] = []
    remaining = (
        HOOK_WALL_SECONDS
        - (perf_counter() - hook_started)
        - FINALIZATION_RESERVE_SECONDS
    )
    try:
        outcome = run_prepare_subprocess(
            event,
            receipt_seed,
            timeout_seconds=remaining,
            environment=os.environ,
        )
        output = outcome.output
        receipt = outcome.receipt
        markers = outcome.markers
    except HookRuntimeError as error:
        markers = error.markers
        output, receipt = degraded_preparation(receipt_seed, error.code)
    worker_total_ms = _round_ms(worker_started)
    _attach_stage_evidence(
        receipt,
        markers,
        {
            "input_parse": input_parse_ms,
            "prepare_worker": worker_total_ms,
        },
    )

    prepared_receipt_persisted = write_receipt(receipt)
    if not prepared_receipt_persisted:
        output["systemMessage"] = (
            "MIND prepared this reminder field, but its delivery receipt "
            "could not be persisted."
        )
    elif not started_receipt_persisted:
        output["systemMessage"] = (
            "MIND prepared this reminder field, but its initial started receipt "
            "could not be persisted."
        )
    stdout_started = perf_counter()
    try:
        print(canonical_json(output), flush=True)
    except Exception:
        receipt["evidence_state"] = "execution_failed"
        receipt["claimed_boundary"] = "hook stdout write did not complete"
        receipt["failure_code"] = "stdout_write_failed"
        receipt["stage_timings_ms"]["stdout_write"] = _round_ms(stdout_started)
        receipt["stage_timings_ms"]["hook_total"] = _round_ms(hook_started)
        receipt["completed_at"] = timestamp()
        write_receipt(receipt)
        return 1

    degraded = "failure_code" in receipt
    receipt["evidence_state"] = (
        "tool_returned_degraded" if degraded else "tool_returned"
    )
    receipt["claimed_boundary"] = (
        ("degraded " if degraded else "")
        + "additionalContext JSON written and flushed to hook stdout"
    )
    receipt["stage_timings_ms"]["stdout_write"] = _round_ms(stdout_started)
    receipt["stage_timings_ms"]["hook_total"] = _round_ms(hook_started)
    receipt["completed_at"] = timestamp()
    write_receipt(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
