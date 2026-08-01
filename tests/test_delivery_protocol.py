from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from mind_core import MindCore, compile_delivery
from mind_core.errors import ValidationError
from mind_core.util import canonical_json, sha256_text

from tests.helpers import handshake_record
from tests.phase2_helpers import (
    TASK_VECTOR,
    associative_index_manifest,
    phase2_bootstrap_fixture,
)


class ReminderDeliveryProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.core = MindCore(Path(self.temp.name) / "mind-core.sqlite3")
        self.addCleanup(self.core.close)
        self.core.hosts.handshake(handshake_record("agent:a", "session:a"))
        self.core.hosts.handshake(handshake_record("agent:b", "session:b"))
        self.core.bootstrap(phase2_bootstrap_fixture())
        self.core.reminders.ingest_index(associative_index_manifest())
        token = self.core.reminders.issue_session_capability(
            "agent:a", "session:a", exposure_scope="public_only"
        )["session_capability"]
        self.field = self.core.reminders.neighborhood(
            token,
            "snapshot:phase2-synthetic:r1",
            [
                {
                    "anchor_id": "task",
                    "anchor_kind": "task",
                    "vector": list(TASK_VECTOR),
                }
            ],
        )

    def test_delivery_is_minimal_exact_and_representation_conserving(self) -> None:
        canonical = compile_delivery(self.field, representation="canonical")
        compact = compile_delivery(self.field, representation="compact")
        self.assertEqual(
            set(canonical),
            {
                "format",
                "field_id",
                "snapshot_id",
                "scoped_estate_digest",
                "membership_manifest_digest",
                "mode",
                "representation",
                "text",
                "body_sha256",
                "utf8_bytes",
                "delivery_digest",
            },
        )
        self.assertEqual(
            canonical["membership_manifest_digest"],
            compact["membership_manifest_digest"],
        )
        self.assertNotEqual(canonical["text"], compact["text"])
        for envelope in (canonical, compact):
            self.assertEqual(sha256_text(envelope["text"]), envelope["body_sha256"])
            self.assertEqual(len(envelope["text"].encode("utf-8")), envelope["utf8_bytes"])
            rebound = dict(envelope)
            digest = rebound.pop("delivery_digest")
            self.assertEqual(sha256_text(canonical_json(rebound)), digest)
            for forbidden in ("anchors", "members", "visibility_token", "vector"):
                self.assertNotIn(forbidden, envelope)

        contract_vector = (
            Path(__file__).parent
            / "fixtures"
            / "mind_associative_field_delivery_v1.json"
        ).read_bytes()
        contract_field = copy.deepcopy(self.field)
        contract_field["field_id"] = "field:contract-vector-v1"
        contract_envelope = compile_delivery(
            contract_field,
            representation="compact",
        )
        self.assertEqual(
            contract_vector,
            (canonical_json(contract_envelope) + "\n").encode("utf-8"),
        )

    def test_delivery_rejects_tampered_representation_bindings(self) -> None:
        changed = copy.deepcopy(self.field)
        changed["representations"]["canonical"]["text"] += " altered"
        with self.assertRaisesRegex(ValidationError, "body_sha256"):
            compile_delivery(changed, representation="canonical")

        changed = copy.deepcopy(self.field)
        changed["representations"]["compact"][
            "membership_manifest_digest"
        ] = sha256_text("different membership")
        with self.assertRaisesRegex(ValidationError, "changed field membership"):
            compile_delivery(changed, representation="compact")

        with self.assertRaisesRegex(ValidationError, "canonical or compact"):
            compile_delivery(self.field, representation="summary")


if __name__ == "__main__":
    unittest.main()
