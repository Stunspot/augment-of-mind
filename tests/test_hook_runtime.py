from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

from mind_core.hook_context import recent_transcript_messages
from mind_core.hook_delivery import (
    HOOK_EVENT,
    HookUnavailable,
    compile_associative_field,
    new_receipt_seed,
    process_event,
)
from mind_core.hook_runtime import (
    HOOK_WALL_SECONDS,
    SEMANTIC_WALL_SECONDS,
    STAGE_PREFIX,
    HookRuntimeError,
    _communicate,
    embed_with_wall_deadline,
    run_prepare_subprocess,
    summarize_stage_markers,
)
from mind_core.util import canonical_json

ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT = {
    "associative_index_snapshot_id": "snapshot:test",
    "snapshot_digest": "a" * 64,
    "embedding_profile_id": "profile:test",
    "model_id": "model:test",
    "current": True,
}


class _FakeHosts:
    def __init__(self, owner: "_FakeFactory"):
        self.owner = owner

    def handshake(self, _record: dict[str, object]) -> None:
        self.owner.handshakes += 1


class _FakeReminders:
    def __init__(self, owner: "_FakeFactory", binding: dict[str, object]):
        self.owner = owner
        self.binding = binding

    def active_snapshot_binding(self) -> dict[str, object]:
        return dict(self.binding)

    def issue_session_capability(self, *_args: object, **_kwargs: object) -> dict[str, str]:
        return {"session_capability": "token:test"}

    def neighborhood(self, *_args: object, **_kwargs: object) -> dict[str, object]:
        self.owner.queries += 1
        return {"field_id": "field:test"}


class _FakeCore:
    def __init__(self, owner: "_FakeFactory", binding: dict[str, object]):
        self.owner = owner
        self.hosts = _FakeHosts(owner)
        self.reminders = _FakeReminders(owner, binding)

    def __enter__(self) -> "_FakeCore":
        self.owner.active += 1
        return self

    def __exit__(self, *_args: object) -> None:
        self.owner.active -= 1


class _FakeFactory:
    def __init__(self, bindings: list[dict[str, object]]):
        self.bindings = bindings
        self.calls = 0
        self.active = 0
        self.handshakes = 0
        self.queries = 0

    def __call__(self, _database: Path) -> _FakeCore:
        binding = self.bindings[min(self.calls, len(self.bindings) - 1)]
        self.calls += 1
        return _FakeCore(self, binding)


class HookDeliveryTests(unittest.TestCase):
    def _event(self) -> dict[str, str]:
        return {
            "hook_event_name": HOOK_EVENT,
            "prompt": "Find a useful capability",
            "turn_id": "turn:test",
        }

    def test_embedding_runs_without_writer_lease(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "mind.sqlite"
            database.touch()
            factory = _FakeFactory([dict(SNAPSHOT), dict(SNAPSHOT)])

            def embedder(
                _texts: list[str], _model: str, _url: str, _timeout: float
            ) -> list[list[float]]:
                self.assertEqual(factory.active, 0)
                return [[0.0]]

            result, vector_state, _context_hash = compile_associative_field(
                self._event(),
                environment={"MIND_CORE_DATABASE": str(database)},
                embedder=embedder,
                core_factory=factory,
            )

        self.assertEqual(result["field_id"], "field:test")
        self.assertIsNone(vector_state)
        self.assertEqual(factory.calls, 2)
        self.assertEqual(factory.active, 0)
        self.assertEqual(factory.handshakes, 1)
        self.assertEqual(factory.queries, 1)

    def test_snapshot_change_after_embedding_fails_closed(self) -> None:
        changed = dict(SNAPSHOT)
        changed["associative_index_snapshot_id"] = "snapshot:changed"
        changed["snapshot_digest"] = "b" * 64
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "mind.sqlite"
            database.touch()
            factory = _FakeFactory([dict(SNAPSHOT), changed])
            with self.assertRaises(HookUnavailable) as raised:
                compile_associative_field(
                    self._event(),
                    environment={"MIND_CORE_DATABASE": str(database)},
                    embedder=lambda *_args: [[0.0]],
                    core_factory=factory,
                )
        self.assertEqual(raised.exception.code, "snapshot_changed_during_embedding")
        self.assertEqual(factory.handshakes, 0)
        self.assertEqual(factory.queries, 0)

    def test_direct_process_event_caller_remains_compatible(self) -> None:
        def compiler(
            _event: dict[str, str], *, environment: dict[str, str]
        ) -> tuple[dict[str, object], None, str]:
            self.assertEqual(environment, {})
            return (
                {
                    "field_id": "field:test",
                    "snapshot_id": "snapshot:test",
                    "membership_manifest_digest": "c" * 64,
                    "mode": "vector_current",
                    "representations": {
                        "canonical": {"text": "Nearby capability"},
                        "compact": {"text": "Nearby capability"},
                    },
                },
                None,
                "d" * 64,
            )

        output = process_event(self._event(), environment={}, compiler=compiler)
        self.assertTrue(output["continue"])
        self.assertIn(
            "Nearby capability",
            output["hookSpecificOutput"]["additionalContext"],
        )
    def test_receipt_seed_is_started_not_completed(self) -> None:
        receipt = new_receipt_seed(self._event(), run_id="run:test")
        self.assertEqual(receipt["run_id"], "run:test")
        self.assertNotIn("completed_at", receipt)


class HookRuntimeTests(unittest.TestCase):
    def test_semantic_deadline_releases_disposable_caller(self) -> None:
        release = threading.Event()

        def blocked_embedder(*_args: object) -> list[list[float]]:
            release.wait(2.0)
            return [[0.0]]

        started = time.perf_counter()
        try:
            with self.assertRaises(HookUnavailable) as raised:
                embed_with_wall_deadline(
                    ["context"],
                    "model",
                    "http://127.0.0.1:1",
                    1.0,
                    embedder=blocked_embedder,
                    wall_seconds=0.05,
                )
        finally:
            release.set()
        self.assertEqual(raised.exception.code, "semantic_deadline_exceeded")
        self.assertLess(time.perf_counter() - started, 1.0)

    def test_supervisor_kills_worker_and_keeps_stage_marker(self) -> None:
        run_id = "run:timeout"
        marker = {
            "format": "mind-hook-stage/v1",
            "run_id": run_id,
            "stage": "semantic_embedding",
            "state": "started",
            "elapsed_ms": 1.0,
            "duration_ms": 0.0,
        }
        child = (
            "import sys,time;"
            f"sys.stderr.write({(STAGE_PREFIX + canonical_json(marker) + chr(10))!r});"
            "sys.stderr.flush();time.sleep(10)"
        )
        started = time.perf_counter()
        with self.assertRaises(HookRuntimeError) as raised:
            _communicate(
                [sys.executable, "-c", child],
                {},
                timeout_seconds=0.1,
                cwd=ROOT,
                environment=os.environ,
                run_id=run_id,
            )
        self.assertEqual(raised.exception.code, "hook_deadline_exceeded")
        self.assertEqual(raised.exception.markers[0]["stage"], "semantic_embedding")
        self.assertLess(time.perf_counter() - started, 5.0)

    def test_worker_start_failure_becomes_runtime_error(self) -> None:
        with patch(
            "mind_core.hook_runtime.subprocess.Popen",
            side_effect=OSError("blocked executable"),
        ):
            with self.assertRaises(HookRuntimeError) as raised:
                _communicate(
                    [sys.executable, "-c", "pass"],
                    {},
                    timeout_seconds=1.0,
                    cwd=ROOT,
                    environment=os.environ,
                    run_id="run:start-failure",
                )
        self.assertEqual(raised.exception.code, "hook_worker_start_failed")
    def test_prepare_subprocess_preserves_public_hook_protocol(self) -> None:
        event = {
            "hook_event_name": HOOK_EVENT,
            "prompt": "probe",
            "turn_id": "turn:worker",
        }
        seed = new_receipt_seed(event, run_id="run:worker")
        with tempfile.TemporaryDirectory() as directory:
            missing_database = Path(directory) / "missing.sqlite"
            outcome = run_prepare_subprocess(
                event,
                seed,
                timeout_seconds=5.0,
                environment={"MIND_CORE_DATABASE": str(missing_database)},
            )
        self.assertTrue(outcome.output["continue"])
        self.assertEqual(
            outcome.output["hookSpecificOutput"]["hookEventName"], HOOK_EVENT
        )
        self.assertEqual(outcome.receipt["run_id"], "run:worker")
        self.assertEqual(outcome.receipt["failure_code"], "database_missing")

    def test_worker_stdout_is_utf8_under_cp1252_parent_setting(self) -> None:
        event = {
            "hook_event_name": HOOK_EVENT,
            "prompt": "probe",
            "turn_id": "turn:utf8",
        }
        seed = new_receipt_seed(event, run_id="run:⟪utf8")
        with tempfile.TemporaryDirectory() as directory:
            missing_database = Path(directory) / "missing.sqlite"
            outcome = run_prepare_subprocess(
                event,
                seed,
                timeout_seconds=5.0,
                environment={
                    "MIND_CORE_DATABASE": str(missing_database),
                    "PYTHONIOENCODING": "cp1252",
                },
            )
        self.assertEqual(outcome.receipt["run_id"], "run:⟪utf8")
        self.assertIn(
            "⟪",
            outcome.output["hookSpecificOutput"]["additionalContext"],
        )
    def test_stage_summary_keeps_failure_and_timings(self) -> None:
        markers = [
            {"stage": "context", "state": "started", "duration_ms": 0.0},
            {"stage": "context", "state": "completed", "duration_ms": 2.5},
            {"stage": "semantic_embedding", "state": "started", "duration_ms": 0.0},
        ]
        summary = summarize_stage_markers(markers)
        self.assertEqual(summary["stage_timings_ms"], {"context": 2.5})
        self.assertEqual(summary["current_stage"], "semantic_embedding")

    def test_stage_summary_retains_failed_stage_after_render(self) -> None:
        markers = [
            {"stage": "semantic_embedding", "state": "started", "duration_ms": 0.0},
            {"stage": "semantic_embedding", "state": "failed", "duration_ms": 12.0},
            {"stage": "render", "state": "started", "duration_ms": 0.0},
            {"stage": "render", "state": "completed", "duration_ms": 0.5},
        ]
        summary = summarize_stage_markers(markers)
        self.assertEqual(summary["last_failed_stage"], "semantic_embedding")
        self.assertEqual(summary["last_completed_stage"], "render")
    def test_internal_deadlines_leave_codex_outer_margin(self) -> None:
        definition = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        timeout = definition["hooks"][HOOK_EVENT][0]["hooks"][0]["timeout"]
        self.assertLess(SEMANTIC_WALL_SECONDS, HOOK_WALL_SECONDS)
        self.assertLess(HOOK_WALL_SECONDS, timeout)


class HookContextTests(unittest.TestCase):
    @staticmethod
    def _record(role: str, text: str, turn_id: str | None) -> str:
        message: dict[str, object] = {
            "type": "message",
            "role": role,
            "content": [{"type": "input_text", "text": text}],
        }
        if turn_id is not None:
            message["internal_chat_message_metadata_passthrough"] = {
                "turn_id": turn_id
            }
        return json.dumps({"type": "response_item", "payload": message})

    def test_current_turn_scaffold_is_excluded_by_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            transcript = Path(directory) / "rollout.jsonl"
            transcript.write_text(
                "\n".join(
                    [
                        self._record("user", "prior user request", "turn:a"),
                        self._record("assistant", "prior answer", "turn:a"),
                        self._record(
                            "user",
                            "# AGENTS.md instructions <environment_context>",
                            "turn:b",
                        ),
                        self._record("user", "actual prompt", "turn:b"),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            observed = recent_transcript_messages(
                {
                    "transcript_path": str(transcript),
                    "turn_id": "turn:b",
                    "prompt": "actual prompt",
                }
            )
        self.assertEqual(
            observed,
            [("user", "prior user request"), ("assistant", "prior answer")],
        )

    def test_nested_nonmessage_records_never_enter_context(self) -> None:
        nested = json.dumps(
            {
                "type": "world_state",
                "payload": {
                    "state": {
                        "role": "user",
                        "content": "nested scaffold must be ignored",
                    }
                },
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            transcript = Path(directory) / "rollout.jsonl"
            transcript.write_text(
                nested
                + "\n"
                + self._record("user", "actual prior message", "turn:a")
                + "\n",
                encoding="utf-8",
            )
            observed = recent_transcript_messages(
                {
                    "transcript_path": str(transcript),
                    "turn_id": "turn:b",
                    "prompt": "new prompt",
                }
            )
        self.assertEqual(observed, [("user", "actual prior message")])
    def test_legacy_transcript_keeps_exact_prompt_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            transcript = Path(directory) / "rollout.jsonl"
            transcript.write_text(
                "\n".join(
                    [
                        self._record(
                            "user",
                            "A legitimate discussion of # AGENTS.md instructions "
                            "and <environment_context>",
                            None,
                        ),
                        self._record("user", "actual prompt", None),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            observed = recent_transcript_messages(
                {"transcript_path": str(transcript), "prompt": "actual prompt"}
            )
        self.assertEqual(len(observed), 1)
        self.assertIn("legitimate discussion", observed[0][1])


class HookEntrypointTests(unittest.TestCase):
    def test_started_receipt_precedes_supervisor(self) -> None:
        script = ROOT / "hooks" / "mind_prompt_submit.py"
        spec = spec_from_file_location("mind_prompt_submit_test", script)
        if spec is None or spec.loader is None:
            self.fail("could not load hook entrypoint")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        receipts: list[dict[str, object]] = []

        def record_receipt(receipt: dict[str, object]) -> bool:
            receipts.append(dict(receipt))
            return True

        def fail_supervisor(*_args: object, **_kwargs: object) -> object:
            self.assertEqual(receipts[0]["evidence_state"], "started")
            raise HookRuntimeError("hook_deadline_exceeded")

        module.write_receipt = record_receipt
        module.run_prepare_subprocess = fail_supervisor
        original_stdin = module.sys.stdin
        module.sys.stdin = io.StringIO(
            json.dumps(
                {
                    "hook_event_name": HOOK_EVENT,
                    "prompt": "probe",
                    "turn_id": "turn:entrypoint",
                }
            )
        )
        output = io.StringIO()
        try:
            with redirect_stdout(output):
                exit_code = module.main()
        finally:
            module.sys.stdin = original_stdin

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [receipt["evidence_state"] for receipt in receipts],
            ["started", "prepared_degraded", "tool_returned_degraded"],
        )
        returned = json.loads(output.getvalue())
        self.assertTrue(returned["continue"])
        self.assertIn("additionalContext", returned["hookSpecificOutput"])


    def test_missing_started_receipt_adds_warning(self) -> None:
        script = ROOT / "hooks" / "mind_prompt_submit.py"
        spec = spec_from_file_location("mind_prompt_submit_warning_test", script)
        if spec is None or spec.loader is None:
            self.fail("could not load hook entrypoint")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        receipts: list[dict[str, object]] = []

        def record_receipt(receipt: dict[str, object]) -> bool:
            receipts.append(dict(receipt))
            return len(receipts) != 1

        module.write_receipt = record_receipt
        module.run_prepare_subprocess = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            HookRuntimeError("hook_deadline_exceeded")
        )
        original_stdin = module.sys.stdin
        module.sys.stdin = io.StringIO(
            json.dumps(
                {
                    "hook_event_name": HOOK_EVENT,
                    "prompt": "probe",
                    "turn_id": "turn:warning",
                }
            )
        )
        output = io.StringIO()
        try:
            with redirect_stdout(output):
                exit_code = module.main()
        finally:
            module.sys.stdin = original_stdin

        self.assertEqual(exit_code, 0)
        returned = json.loads(output.getvalue())
        self.assertIn("initial started receipt", returned["systemMessage"])

if __name__ == "__main__":
    unittest.main()
