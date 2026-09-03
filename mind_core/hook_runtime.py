"""Bounded subprocess runtime for the Codex Arm's Reach prompt hook."""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping, Sequence

from .contextual_recall import embed_membranes
from .hook_delivery import (
    HOOK_EVENT,
    HookUnavailable,
    compile_associative_field,
    degraded_context,
    prepare_event,
    sha256_text,
)
from .util import canonical_json, timestamp

SEMANTIC_WALL_SECONDS = 12.0
HOOK_WALL_SECONDS = 18.0
FINALIZATION_RESERVE_SECONDS = 1.0
STAGE_PREFIX = "MIND_HOOK_STAGE "

Embedder = Callable[[list[str], str, str, float], list[list[float]]]


def _configure_standard_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")

class HookRuntimeError(RuntimeError):
    """The disposable hook worker missed its wall or protocol boundary."""

    def __init__(self, code: str, markers: list[dict[str, Any]] | None = None):
        super().__init__(code)
        self.code = code
        self.markers = markers or []


@dataclass(frozen=True)
class WorkerOutcome:
    output: dict[str, Any]
    receipt: dict[str, Any]
    markers: list[dict[str, Any]]


class StageReporter:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.started = perf_counter()

    def __call__(self, stage: str, state: str, duration_ms: float) -> None:
        marker = {
            "format": "mind-hook-stage/v1",
            "run_id": self.run_id,
            "stage": stage,
            "state": state,
            "elapsed_ms": round((perf_counter() - self.started) * 1000.0, 3),
            "duration_ms": round(duration_ms, 3),
        }
        sys.stderr.write(STAGE_PREFIX + canonical_json(marker) + "\n")
        sys.stderr.flush()


def embed_with_wall_deadline(
    texts: list[str],
    model: str,
    url: str,
    timeout_seconds: float,
    *,
    embedder: Embedder = embed_membranes,
    wall_seconds: float = SEMANTIC_WALL_SECONDS,
) -> list[list[float]]:
    """Run one embedding call on a daemon thread inside a disposable worker."""

    effective_timeout = min(float(timeout_seconds), float(wall_seconds))
    if effective_timeout <= 0:
        raise HookUnavailable("semantic_deadline_exceeded")

    result_queue: queue.Queue[tuple[bool, object]] = queue.Queue(maxsize=1)

    def invoke() -> None:
        try:
            result_queue.put(
                (True, embedder(texts, model, url, effective_timeout)),
                block=False,
            )
        except Exception as error:
            result_queue.put((False, error), block=False)

    worker = threading.Thread(
        target=invoke,
        name="mind-arm-reach-embedding",
        daemon=True,
    )
    worker.start()
    worker.join(effective_timeout)
    if worker.is_alive():
        raise HookUnavailable("semantic_deadline_exceeded")
    try:
        succeeded, result = result_queue.get_nowait()
    except queue.Empty as error:
        raise HookUnavailable("semantic_worker_failed") from error
    if not succeeded:
        if isinstance(result, Exception):
            raise result
        raise HookUnavailable("semantic_worker_failed")
    if not isinstance(result, list):
        raise HookUnavailable("semantic_worker_failed")
    return result


def _parse_stage_markers(stderr: str, run_id: str) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for line in stderr.splitlines():
        if not line.startswith(STAGE_PREFIX):
            continue
        try:
            marker = json.loads(line[len(STAGE_PREFIX) :])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(marker, dict)
            and marker.get("format") == "mind-hook-stage/v1"
            and marker.get("run_id") == run_id
            and isinstance(marker.get("stage"), str)
            and marker.get("state") in {"started", "completed", "failed"}
        ):
            markers.append(marker)
    return markers


def summarize_stage_markers(markers: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    timings: dict[str, float] = {}
    current_stage: str | None = None
    last_stage: str | None = None
    last_failed_stage: str | None = None
    for marker in markers:
        stage = marker.get("stage")
        state = marker.get("state")
        if not isinstance(stage, str):
            continue
        last_stage = stage
        if state == "started":
            current_stage = stage
        elif state in {"completed", "failed"}:
            duration = marker.get("duration_ms")
            if isinstance(duration, (int, float)) and duration >= 0:
                timings[stage] = round(float(duration), 3)
            current_stage = stage if state == "failed" else None
            if state == "failed":
                last_failed_stage = stage
    result: dict[str, Any] = {"stage_timings_ms": timings}
    if last_failed_stage is not None:
        result["last_failed_stage"] = last_failed_stage
    if current_stage is not None:
        result["current_stage"] = current_stage
    elif last_stage is not None:
        result["last_completed_stage"] = last_stage
    return result


def _communicate(
    command: Sequence[str],
    payload: Mapping[str, Any],
    *,
    timeout_seconds: float,
    cwd: Path,
    environment: Mapping[str, str],
    run_id: str,
) -> tuple[str, str]:
    if timeout_seconds <= 0:
        raise HookRuntimeError("hook_deadline_exceeded")
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            env=dict(environment),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            creationflags=creationflags,
        )
    except OSError as error:
        raise HookRuntimeError("hook_worker_start_failed") from error
    try:
        stdout, stderr = process.communicate(
            canonical_json(dict(payload)),
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except OSError:
            pass
        try:
            _stdout, stderr = process.communicate()
        except OSError:
            stderr = ""
        raise HookRuntimeError(
            "hook_deadline_exceeded",
            _parse_stage_markers(stderr, run_id),
        ) from None
    except OSError as error:
        try:
            process.kill()
        except OSError:
            pass
        raise HookRuntimeError("hook_worker_io_failed") from error
    markers = _parse_stage_markers(stderr, run_id)
    if process.returncode != 0:
        raise HookRuntimeError("hook_worker_failed", markers)
    return stdout, stderr


def run_prepare_subprocess(
    event: Mapping[str, Any],
    receipt_seed: Mapping[str, Any],
    *,
    timeout_seconds: float,
    environment: Mapping[str, str] | None = None,
) -> WorkerOutcome:
    """Prepare one hook result in a worker the launcher can kill at its wall."""

    plugin_root = Path(__file__).resolve().parents[1]
    child_environment = dict(os.environ)
    if environment is not None:
        child_environment.update(environment)
    child_environment["PLUGIN_ROOT"] = str(plugin_root)
    child_environment["PYTHONUTF8"] = "1"
    child_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-m", "mind_core.hook_runtime", "--prepare-worker"]
    payload = {"event": dict(event), "receipt_seed": dict(receipt_seed)}
    run_id = str(receipt_seed["run_id"])
    stdout, stderr = _communicate(
        command,
        payload,
        timeout_seconds=timeout_seconds,
        cwd=plugin_root,
        environment=child_environment,
        run_id=run_id,
    )
    markers = _parse_stage_markers(stderr, run_id)
    try:
        response = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise HookRuntimeError("hook_worker_protocol_invalid", markers) from error
    if not isinstance(response, dict):
        raise HookRuntimeError("hook_worker_protocol_invalid", markers)
    output = response.get("output")
    receipt = response.get("receipt")
    if not isinstance(output, dict) or not isinstance(receipt, dict):
        raise HookRuntimeError("hook_worker_protocol_invalid", markers)
    if receipt.get("run_id") != run_id:
        raise HookRuntimeError("hook_worker_protocol_invalid", markers)
    return WorkerOutcome(output=output, receipt=receipt, markers=markers)


def degraded_preparation(
    receipt_seed: Mapping[str, Any],
    code: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    run_id = str(receipt_seed["run_id"])
    additional_context = degraded_context(code, run_id)
    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "additionalContext": additional_context,
        },
    }
    receipt = {
        **dict(receipt_seed),
        "evidence_state": "prepared_degraded",
        "claimed_boundary": "unavailable-field notice prepared; hook stdout not yet written",
        "failure_code": code,
        "additional_context_hash": sha256_text(additional_context),
        "completed_at": timestamp(),
    }
    return output, receipt


def _prepare_worker(payload: Mapping[str, Any]) -> int:
    event = payload.get("event")
    receipt_seed = payload.get("receipt_seed")
    if not isinstance(event, dict) or not isinstance(receipt_seed, dict):
        return 2
    run_id = receipt_seed.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        return 2
    reporter = StageReporter(run_id)

    def compiler(
        candidate: Mapping[str, Any],
        *,
        environment: Mapping[str, str],
    ) -> tuple[dict[str, Any], str | None, str]:
        return compile_associative_field(
            candidate,
            environment=environment,
            embedder=embed_with_wall_deadline,
            stage_sink=reporter,
        )

    output, receipt = prepare_event(
        event,
        environment=os.environ,
        compiler=compiler,
        receipt_seed=receipt_seed,
        stage_sink=reporter,
    )
    sys.stdout.write(canonical_json({"output": output, "receipt": receipt}) + "\n")
    sys.stdout.flush()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    _configure_standard_streams()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments != ["--prepare-worker"]:
        return 2
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 2
    if not isinstance(payload, dict):
        return 2
    return _prepare_worker(payload)


if __name__ == "__main__":
    raise SystemExit(main())
