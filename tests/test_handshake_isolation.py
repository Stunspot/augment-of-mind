from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mind_core import MindCore
from mind_core.errors import ConflictError, NotFoundError, ValidationError

from tests.helpers import (
    bound_receipt,
    bootstrap_fixture,
    global_receipt,
    handshake_record,
    scoped_receipt,
    stamp,
)


class HandshakeIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.core = MindCore(Path(self.temp.name) / "mind-core.sqlite3")
        self.core.bootstrap(bootstrap_fixture())

    def tearDown(self) -> None:
        self.core.close()
        self.temp.cleanup()

    def test_same_agent_can_open_later_session_without_rewriting_identity(self) -> None:
        first = self.core.hosts.handshake(
            handshake_record("agent:a", "session:a1", session_epoch=1)
        )
        second = self.core.hosts.handshake(
            handshake_record(
                "agent:a",
                "session:a2",
                session_epoch=2,
                observed_offset=-60,
            )
        )
        created_at = self.core.store.connection.execute(
            "SELECT created_at FROM agent_instances WHERE agent_instance_id='agent:a'"
        ).fetchone()[0]
        self.assertEqual(created_at, first["session"]["observed_at"])
        self.assertNotEqual(
            first["session"]["observed_at"], second["session"]["observed_at"]
        )

    def test_agent_persona_and_profile_cannot_change_by_handshake(self) -> None:
        self.core.hosts.handshake(
            handshake_record(
                "agent:a", "session:a1", persona_id="persona:nova", profile_id="profile:one"
            )
        )
        with self.assertRaises(ConflictError):
            self.core.hosts.handshake(
                handshake_record(
                    "agent:a",
                    "session:a2",
                    session_epoch=2,
                    persona_id=None,
                    profile_id="profile:one",
                )
            )

    def test_handshake_rejects_incompatible_protocol_and_overlong_catalog(self) -> None:
        with self.assertRaises(ValidationError):
            self.core.hosts.handshake(
                handshake_record(
                    "agent:a", "session:a", protocol_version="mind-core/99"
                )
            )
        with self.assertRaises(ValidationError):
            self.core.hosts.handshake(
                handshake_record(
                    "agent:a",
                    "session:a",
                    expires_offset=300,
                    catalog_expires_offset=600,
                )
            )

    def test_declared_h3_remains_reported_h0_metadata(self) -> None:
        result = self.core.hosts.handshake(
            handshake_record(
                "agent:a", "session:a", declared_conformance_level="H3"
            )
        )
        self.assertEqual(result["session"]["declared_conformance_level"], "H3")
        self.assertEqual(result["session"]["evidence_conformance_level"], "H0")
        self.assertEqual(result["receipt"]["evidence_state"], "reported")
        coverage = self.core.hosts.record_coverage(
            {
                "coverage_id": "coverage:test",
                "agent_instance_id": "agent:a",
                "host_session_id": "session:a",
                "event_kind": "tool_result",
                "action_class": "filesystem_write",
                "source_observer": "synthetic test adapter declaration",
                "timing": "post_action",
                "delivery_durability": "not_observed",
                "correlation_method": "none",
                "declared_coverage_state": "enforced",
                "observed_at": stamp(-30),
                "expires_at": stamp(300),
            }
        )
        self.assertEqual(coverage["coverage"]["effective_coverage_state"], "advisory_only")
        self.assertEqual(coverage["coverage"]["evidence_conformance_level"], "H0")

    def test_receipts_and_lifecycle_evidence_do_not_cross_agent_scope(self) -> None:
        self.core.hosts.handshake(handshake_record("agent:a", "session:a"))
        self.core.hosts.handshake(handshake_record("agent:b", "session:b"))
        receipt_a = scoped_receipt(
            self.core,
            "agent:a",
            "session:a",
            receipt_id="receipt:a",
            idempotency_key="same-key",
        )
        receipt_b = scoped_receipt(
            self.core,
            "agent:b",
            "session:b",
            receipt_id="receipt:b",
            idempotency_key="same-key",
        )
        self.assertNotEqual(receipt_a["receipt_id"], receipt_b["receipt_id"])
        with self.assertRaises(NotFoundError):
            self.core.receipts.get(
                "receipt:a",
                agent_instance_id="agent:b",
                host_session_id="session:b",
            )
        lifecycle_record = {
            "observation_id": "lifecycle:cross-scope",
            "capability_id": "capability:augment-of-mind",
            "distribution_id": "distribution:mind:build-week:1.0.0",
            "axis": "host_presence",
            "state": "injected",
            "agent_instance_id": "agent:b",
            "host_session_id": "session:b",
            "observed_at": stamp(-20),
            "expires_at": stamp(300),
            "evidence_receipt_id": "receipt:bound-a",
            "source_reference": "cross-scope negative test",
        }
        bound_receipt(
            self.core,
            lifecycle_record,
            receipt_id="receipt:bound-a",
            idempotency_key="bound-a",
            receipt_type="lifecycle.observation",
            subject_kind="lifecycle_observation",
            subject_id=lifecycle_record["observation_id"],
            agent_instance_id="agent:a",
            host_session_id="session:a",
        )
        with self.assertRaises(NotFoundError):
            with self.core.store.transaction() as connection:
                self.core.estate.ingest_lifecycle_observations(
                    [lifecycle_record],
                    connection,
                )

        unrelated_record = dict(lifecycle_record)
        unrelated_record["observation_id"] = "lifecycle:unrelated-receipt"
        unrelated_record["evidence_receipt_id"] = "receipt:b"
        with self.assertRaises(ValidationError):
            with self.core.store.transaction() as connection:
                self.core.estate.ingest_lifecycle_observations(
                    [unrelated_record], connection
                )

    def test_global_runtime_state_is_rejected(self) -> None:
        evidence = global_receipt(
            self.core,
            receipt_id="receipt:global",
            idempotency_key="global-runtime",
        )
        with self.assertRaises(ValidationError):
            with self.core.store.transaction() as connection:
                self.core.estate.ingest_lifecycle_observations(
                    [
                        {
                            "observation_id": "lifecycle:global-runtime",
                            "capability_id": "capability:augment-of-mind",
                            "distribution_id": None,
                            "axis": "runtime_use",
                            "state": "invoked",
                            "agent_instance_id": None,
                            "host_session_id": None,
                            "observed_at": stamp(-20),
                            "expires_at": None,
                            "evidence_receipt_id": evidence["receipt_id"],
                            "source_reference": "negative test",
                        }
                    ],
                    connection,
                )

    def test_expired_session_invalidates_catalog_freshness(self) -> None:
        result = self.core.hosts.handshake(
            handshake_record(
                "agent:expired",
                "session:expired",
                observed_offset=-600,
                expires_offset=-60,
                catalog_expires_offset=-120,
            )
        )
        self.assertFalse(result["session"]["fresh"])
        self.assertFalse(result["session"]["catalog_snapshot_fresh"])
        self.assertFalse(result["session"]["permission_observation_fresh"])


if __name__ == "__main__":
    unittest.main()
