from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from mind_core import MindCore


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "skills" / "augment-of-mind" / "assets"
EVIDENCE = ROOT / "verification" / "associative-retrieval" / "live-results.json"


class AssociativeReleaseAssetsTests(unittest.TestCase):
    def test_public_h0_adapter_keeps_persona_identity_neutral(self) -> None:
        adapter = (ROOT / "scripts" / "query_associative_field.py").read_text(encoding="utf-8")
        self.assertIn('default="agent:mind-h0"', adapter)
        self.assertNotIn('default="agent:nova"', adapter)


    def test_authored_cards_cover_all_sixteen_faculties_and_six_views(self) -> None:
        source = json.loads((ASSETS / "associative-capability-cards.json").read_text(encoding="utf-8"))
        self.assertEqual(source["format"], "mind-authored-capability-cards/v1")
        self.assertEqual(len(source["cards"]), 16)
        self.assertEqual(len({card["handle"] for card in source["cards"]}), 16)
        expected = {"transformation", "situation", "positive_cue", "error_or_correction", "negative_boundary", "example"}
        for card in source["cards"]:
            self.assertEqual(set(card["views"]), expected)

    def test_qualified_manifest_binds_live_evidence_and_ingests_fresh(self) -> None:
        bootstrap = json.loads((ASSETS / "associative-bootstrap.json").read_text(encoding="utf-8"))
        manifest = json.loads((ASSETS / "associative-index-qwen3-embedding-0.6b.json").read_text(encoding="utf-8"))
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["summary"], {"passed": 6, "total": 6, "verdict": "PASS"})
        self.assertEqual(manifest["embedding_profile"]["qualification_state"], "behavior_qualified")
        self.assertEqual(manifest["embedding_profile"]["qualification_digest"], hashlib.sha256(EVIDENCE.read_bytes()).hexdigest())
        self.assertEqual(manifest["snapshot"]["expected_card_count"], 16)
        self.assertEqual(manifest["snapshot"]["expected_vector_count"], 96)
        with tempfile.TemporaryDirectory() as directory:
            with MindCore(Path(directory) / "mind.sqlite3") as core:
                core.bootstrap(bootstrap)
                status = core.reminders.ingest_index(manifest)
        self.assertTrue(status["current"])
        self.assertEqual(status["counts"], {"cards": 16, "relations": 15, "vectors": 96})
        self.assertEqual(status["qualification_state"], "behavior_qualified")


if __name__ == "__main__":
    unittest.main()
