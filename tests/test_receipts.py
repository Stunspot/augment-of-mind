from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from mind_core import MindCore
from mind_core.errors import ConflictError, ScopeError, ValidationError

from tests.helpers import global_receipt, handshake_record, scoped_receipt


class ReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.core = MindCore(Path(self.temp.name) / "mind-core.sqlite3")
        self.core.hosts.handshake(handshake_record("agent:a", "session:a"))
        self.core.hosts.handshake(handshake_record("agent:b", "session:b"))

    def tearDown(self) -> None:
        self.core.close()
        self.temp.cleanup()

    def test_idempotent_replay_is_stable_and_conflicting_reuse_fails(self) -> None:
        first = global_receipt(
            self.core,
            receipt_id="receipt:stable",
            idempotency_key="stable",
        )
        envelope = {
            "receipt_id": "receipt:stable",
            "idempotency_key": "stable",
            "receipt_type": "test.global",
            "subject_kind": "test_subject",
            "subject_id": "subject:global",
            "evidence_state": "reported",
            "claimed_boundary": "A global metadata premise was recorded.",
            "observed_at": first["observed_at"],
            "redaction_class": "metadata_only",
            "payload_hash": "e" * 64,
        }
        replay = self.core.receipts.append(envelope)
        self.assertEqual(first["receipt_id"], replay["receipt_id"])
        changed = dict(envelope)
        changed["claimed_boundary"] = "Different content."
        with self.assertRaises(ConflictError):
            self.core.receipts.append(changed)
        changed_id = dict(envelope)
        changed_id["receipt_id"] = "receipt:different"
        with self.assertRaises(ConflictError):
            self.core.receipts.append(changed_id)

    def test_parent_scope_rules_allow_global_or_same_scope_only(self) -> None:
        global_parent = global_receipt(
            self.core,
            receipt_id="receipt:global-parent",
            idempotency_key="global-parent",
        )
        parent_a = scoped_receipt(
            self.core,
            "agent:a",
            "session:a",
            receipt_id="receipt:parent-a",
            idempotency_key="parent-a",
        )
        child = scoped_receipt(
            self.core,
            "agent:a",
            "session:a",
            receipt_id="receipt:child-a",
            idempotency_key="child-a",
        )
        child_envelope = {
            **child,
            "idempotency_key": "child-with-parents",
            "receipt_id": "receipt:child-with-parents",
        }
        for field in ("recorded_at", "content_digest"):
            child_envelope.pop(field, None)
        linked = self.core.receipts.append(
            child_envelope,
            parents=[
                {"receipt_id": global_parent["receipt_id"], "relation": "premise"},
                {"receipt_id": parent_a["receipt_id"], "relation": "supports"},
            ],
        )
        self.assertEqual(linked["receipt_id"], "receipt:child-with-parents")

        parent_b = scoped_receipt(
            self.core,
            "agent:b",
            "session:b",
            receipt_id="receipt:parent-b",
            idempotency_key="parent-b",
        )
        cross = dict(child_envelope)
        cross["receipt_id"] = "receipt:cross"
        cross["idempotency_key"] = "cross"
        with self.assertRaises(ScopeError):
            self.core.receipts.append(
                cross,
                parents=[{"receipt_id": parent_b["receipt_id"], "relation": "supports"}],
            )

        global_child = {
            "receipt_id": "receipt:global-child",
            "idempotency_key": "global-child",
            "receipt_type": "test.global",
            "subject_kind": "test_subject",
            "subject_id": "subject:global-child",
            "evidence_state": "reported",
            "claimed_boundary": "Global child negative test.",
            "observed_at": global_parent["observed_at"],
            "redaction_class": "metadata_only",
            "payload_hash": "f" * 64,
        }
        with self.assertRaises(ScopeError):
            self.core.receipts.append(
                global_child,
                parents=[{"receipt_id": parent_a["receipt_id"], "relation": "supports"}],
            )

    def test_duplicate_parents_are_rejected_before_sql(self) -> None:
        parent = global_receipt(
            self.core,
            receipt_id="receipt:parent",
            idempotency_key="parent",
        )
        with self.assertRaises(ValidationError):
            self.core.receipts.append(
                {
                    "receipt_id": "receipt:duplicate-child",
                    "idempotency_key": "duplicate-child",
                    "receipt_type": "test.global",
                    "subject_kind": "test_subject",
                    "subject_id": "subject:duplicate",
                    "evidence_state": "reported",
                    "claimed_boundary": "Duplicate edge negative test.",
                    "observed_at": parent["observed_at"],
                    "redaction_class": "metadata_only",
                    "payload_hash": "0" * 64,
                },
                parents=[
                    {"receipt_id": parent["receipt_id"], "relation": "supports"},
                    {"receipt_id": parent["receipt_id"], "relation": "supports"},
                ],
            )

    def test_receipts_and_edges_are_database_append_only(self) -> None:
        first = global_receipt(
            self.core,
            receipt_id="receipt:first",
            idempotency_key="first",
        )
        second = self.core.receipts.append(
            {
                "receipt_id": "receipt:second",
                "idempotency_key": "second",
                "receipt_type": "test.global",
                "subject_kind": "test_subject",
                "subject_id": "subject:second",
                "evidence_state": "reported",
                "claimed_boundary": "Second receipt.",
                "observed_at": first["observed_at"],
                "redaction_class": "metadata_only",
                "payload_hash": "1" * 64,
            },
            parents=[{"receipt_id": first["receipt_id"], "relation": "supports"}],
        )
        with self.assertRaises(sqlite3.DatabaseError):
            self.core.store.connection.execute(
                "UPDATE receipts SET claimed_boundary='changed' WHERE receipt_id=?",
                (first["receipt_id"],),
            )
        with self.assertRaises(sqlite3.DatabaseError):
            self.core.store.connection.execute(
                "DELETE FROM receipt_edges WHERE child_receipt_id=?",
                (second["receipt_id"],),
            )
        with self.assertRaises(sqlite3.DatabaseError):
            self.core.store.connection.execute(
                "INSERT INTO receipt_edges(child_receipt_id,parent_receipt_id,relation) "
                "VALUES (?,?,?)",
                (first["receipt_id"], second["receipt_id"], "cycle"),
            )


if __name__ == "__main__":
    unittest.main()
