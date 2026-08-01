from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mind_core import MindCore
from mind_core.errors import NotFoundError, ValidationError

from tests.helpers import (
    bound_receipt,
    bootstrap_fixture,
    handshake_record,
    scoped_receipt,
    stamp,
)


class MountSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.core = MindCore(Path(self.temp.name) / "mind-core.sqlite3")
        self.core.bootstrap(bootstrap_fixture())
        self.core.hosts.handshake(handshake_record("agent:a", "session:a"))
        self.core.hosts.handshake(handshake_record("agent:b", "session:b"))
        scoped_receipt(
            self.core,
            "agent:a",
            "session:a",
            receipt_id="receipt:a",
            idempotency_key="mount-a",
        )
        scoped_receipt(
            self.core,
            "agent:b",
            "session:b",
            receipt_id="receipt:b",
            idempotency_key="mount-b",
        )

    def tearDown(self) -> None:
        self.core.close()
        self.temp.cleanup()

    def observation(
        self,
        *,
        observation_id: str,
        agent: str,
        session: str,
        receipt: str,
        availability: str,
        path_visible: bool | None,
        runtime_openable: bool | None,
        schema_valid: bool | None = None,
        integrity_valid: bool | None = None,
        authoritative_read_succeeded: bool | None = None,
        failure_boundary: str | None = None,
    ) -> dict[str, object]:
        return {
            "mount_observation_id": observation_id,
            "mount_id": "mount:dunbar",
            "agent_instance_id": agent,
            "host_session_id": session,
            "availability_state": availability,
            "path_visible": path_visible,
            "runtime_openable": runtime_openable,
            "schema_valid": schema_valid,
            "integrity_valid": integrity_valid,
            "authoritative_read_succeeded": authoritative_read_succeeded,
            "failure_boundary": failure_boundary,
            "observed_at": stamp(-20),
            "expires_at": stamp(300),
            "evidence_receipt_id": receipt,
        }

    def test_cross_agent_receipt_cannot_evidence_mount_observation(self) -> None:
        record = self.observation(
            observation_id="mount-observation:cross",
            agent="agent:b",
            session="session:b",
            receipt="receipt:cross-bound",
            availability="BACKEND_UNAVAILABLE",
            path_visible=True,
            runtime_openable=False,
            failure_boundary="owner runtime could not open the store",
        )
        bound_receipt(
            self.core,
            record,
            receipt_id="receipt:cross-bound",
            idempotency_key="cross-bound",
            receipt_type="mount.observation",
            subject_kind="mount_observation",
            subject_id=record["mount_observation_id"],
            agent_instance_id="agent:a",
            host_session_id="session:a",
        )
        with self.assertRaises(NotFoundError):
            self.core.mounts.record_observation(record)

    def test_same_scope_unrelated_receipt_cannot_evidence_observation(self) -> None:
        with self.assertRaises(ValidationError):
            self.core.mounts.record_observation(
                self.observation(
                    observation_id="mount-observation:unrelated",
                    agent="agent:a",
                    session="session:a",
                    receipt="receipt:a",
                    availability="BACKEND_UNAVAILABLE",
                    path_visible=True,
                    runtime_openable=False,
                    failure_boundary="owner runtime unavailable",
                )
            )

    def test_path_visible_runtime_closed_is_backend_unavailable_not_empty(self) -> None:
        record = self.observation(
            observation_id="mount-observation:backend",
            agent="agent:a",
            session="session:a",
            receipt="receipt:backend-bound",
            availability="BACKEND_UNAVAILABLE",
            path_visible=True,
            runtime_openable=False,
            failure_boundary="owner runtime could not open the store",
        )
        bound_receipt(
            self.core,
            record,
            receipt_id="receipt:backend-bound",
            idempotency_key="backend-bound",
            receipt_type="mount.observation",
            subject_kind="mount_observation",
            subject_id=record["mount_observation_id"],
            agent_instance_id="agent:a",
            host_session_id="session:a",
        )
        accepted = self.core.mounts.record_observation(record)
        self.assertEqual(accepted["availability_state"], "BACKEND_UNAVAILABLE")
        with self.assertRaises(ValidationError):
            self.core.mounts.record_observation(
                self.observation(
                    observation_id="mount-observation:false-empty",
                    agent="agent:b",
                    session="session:b",
                    receipt="receipt:b",
                    availability="AUTHORITATIVE_EMPTY",
                    path_visible=True,
                    runtime_openable=False,
                )
            )

    def test_authoritative_empty_requires_successful_owner_read(self) -> None:
        with self.assertRaises(ValidationError):
            self.core.mounts.record_observation(
                self.observation(
                    observation_id="mount-observation:unproved-empty",
                    agent="agent:b",
                    session="session:b",
                    receipt="receipt:b",
                    availability="AUTHORITATIVE_EMPTY",
                    path_visible=True,
                    runtime_openable=True,
                    schema_valid=True,
                    integrity_valid=True,
                    authoritative_read_succeeded=None,
                )
            )
        record = self.observation(
            observation_id="mount-observation:proved-empty",
            agent="agent:b",
            session="session:b",
            receipt="receipt:empty-bound",
            availability="AUTHORITATIVE_EMPTY",
            path_visible=True,
            runtime_openable=True,
            schema_valid=True,
            integrity_valid=True,
            authoritative_read_succeeded=True,
        )
        bound_receipt(
            self.core,
            record,
            receipt_id="receipt:empty-bound",
            idempotency_key="empty-bound",
            receipt_type="mount.observation",
            subject_kind="mount_observation",
            subject_id=record["mount_observation_id"],
            agent_instance_id="agent:b",
            host_session_id="session:b",
        )
        accepted = self.core.mounts.record_observation(record)
        self.assertTrue(accepted["authoritative_read_succeeded"])

    def test_authoritative_empty_rejects_reported_only_receipt(self) -> None:
        record = self.observation(
            observation_id="mount-observation:reported-empty",
            agent="agent:b",
            session="session:b",
            receipt="receipt:reported-empty",
            availability="AUTHORITATIVE_EMPTY",
            path_visible=True,
            runtime_openable=True,
            schema_valid=True,
            integrity_valid=True,
            authoritative_read_succeeded=True,
        )
        bound_receipt(
            self.core,
            record,
            receipt_id="receipt:reported-empty",
            idempotency_key="reported-empty",
            receipt_type="mount.observation",
            subject_kind="mount_observation",
            subject_id=record["mount_observation_id"],
            agent_instance_id="agent:b",
            host_session_id="session:b",
            evidence_state="reported",
        )
        with self.assertRaises(ValidationError):
            self.core.mounts.record_observation(record)

    def test_mount_grant_requires_exact_bound_same_scope_receipt(self) -> None:
        observed_at = stamp(-20)
        expires_at = stamp(300)
        grant_input = {
            "grant_id": "grant:test",
            "mount_id": "mount:dunbar",
            "agent_instance_id": "agent:a",
            "host_session_id": "session:a",
            "purpose": "Read one purpose-scoped test record.",
            "sensitivity_ceiling": "private_people",
            "allowed_operations": ["read"],
            "authority_ref": "synthetic test authority",
            "observed_at": observed_at,
            "expires_at": expires_at,
            "evidence_receipt_id": "receipt:grant-bound",
        }
        unrelated = dict(grant_input)
        unrelated["grant_id"] = "grant:unrelated"
        unrelated["evidence_receipt_id"] = "receipt:a"
        with self.assertRaises(ValidationError):
            self.core.mounts.record_grant(unrelated)

        canonical_record = {
            key: value
            for key, value in grant_input.items()
            if key != "allowed_operations"
        }
        canonical_record["allowed_operations_json"] = json.dumps(
            ["read"], ensure_ascii=False, separators=(",", ":")
        )
        bound_receipt(
            self.core,
            canonical_record,
            receipt_id="receipt:grant-bound",
            idempotency_key="grant-bound",
            receipt_type="mount.grant",
            subject_kind="mount_grant",
            subject_id=grant_input["grant_id"],
            agent_instance_id="agent:a",
            host_session_id="session:a",
        )
        accepted = self.core.mounts.record_grant(grant_input)
        self.assertEqual(accepted["grant_id"], "grant:test")

    def test_observations_do_not_leak_between_agent_catalogs(self) -> None:
        record = self.observation(
            observation_id="mount-observation:a-only",
            agent="agent:a",
            session="session:a",
            receipt="receipt:a-only-bound",
            availability="BACKEND_UNAVAILABLE",
            path_visible=True,
            runtime_openable=False,
            failure_boundary="owner runtime unavailable",
        )
        bound_receipt(
            self.core,
            record,
            receipt_id="receipt:a-only-bound",
            idempotency_key="a-only-bound",
            receipt_type="mount.observation",
            subject_kind="mount_observation",
            subject_id=record["mount_observation_id"],
            agent_instance_id="agent:a",
            host_session_id="session:a",
        )
        self.core.mounts.record_observation(record)
        catalog_a = {
            item["mount_id"]: item
            for item in self.core.mounts.catalog("session:a", "agent:a")
        }
        catalog_b = {
            item["mount_id"]: item
            for item in self.core.mounts.catalog("session:b", "agent:b")
        }
        self.assertIsNotNone(catalog_a["mount:dunbar"]["observation"])
        self.assertIsNone(catalog_b["mount:dunbar"]["observation"])


if __name__ == "__main__":
    unittest.main()
