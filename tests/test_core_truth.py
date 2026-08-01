from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mind_core import MindCore
from mind_core.constants import FORBIDDEN_PHASE1_TABLE_TERMS

from tests.helpers import bootstrap_fixture, handshake_record


class CoreTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "mind-core.sqlite3"
        self.core = MindCore(self.database)

    def tearDown(self) -> None:
        self.core.close()
        self.temp.cleanup()

    def test_fresh_core_is_persona_free_and_dependency_optional(self) -> None:
        status = self.core.status()
        self.assertFalse(status["persona_required"])
        self.assertFalse(status["persona_inference"])
        self.assertEqual(status["maximum_host_conformance"], "H0")
        self.assertNotIn("nova", str(status).casefold())
        self.assertNotIn("testforge", str(status).casefold())
        self.assertNotIn("obsidian", str(status).casefold())
        self.assertNotIn("mnemosyne", str(status).casefold())

    def test_bootstrap_is_idempotent_and_preserves_lifecycle_truth(self) -> None:
        manifest = bootstrap_fixture()
        first = self.core.bootstrap(manifest)
        second = self.core.bootstrap(manifest)
        self.assertEqual(first["counts"], second["counts"])

        egdod = self.core.estate.resolve("egdod")[0]
        self.assertEqual(egdod["capability_id"], "capability:egdod")
        self.assertEqual(egdod["distributions"], [])
        states = {
            (item["axis"], item["state"])
            for item in egdod["lifecycle_observations"]
        }
        self.assertEqual(
            states,
            {
                ("custody", "canonical-constructed"),
                ("distribution", "not-generated"),
            },
        )
        self.assertIsNone(egdod["derived_active_state"])
        lifecycle_states = {
            item["state"] for item in egdod["lifecycle_observations"]
        }
        self.assertTrue(
            lifecycle_states.isdisjoint({"installed", "invoked", "healthy"})
        )

    def test_duplicate_mind_providers_remain_distinct_distributions(self) -> None:
        self.core.bootstrap(bootstrap_fixture())
        mind = self.core.estate.resolve("mind")[0]
        observed = {
            (item["provider_id"], item["version"])
            for item in mind["distributions"]
        }
        self.assertEqual(
            observed,
            {
                ("provider:personal", "0.2.0"),
                ("provider:build-week", "1.0.0"),
            },
        )
        self.assertIsNone(mind["derived_active_state"])

    def test_registered_and_known_unregistered_mounts_are_distinct(self) -> None:
        self.core.bootstrap(bootstrap_fixture())
        self.core.hosts.handshake(handshake_record("agent:a", "session:a"))
        catalog = self.core.mounts.catalog("session:a", "agent:a")
        states = {item["mount_id"]: item["registration_state"] for item in catalog}
        self.assertEqual(states["mount:cd-data-registry"], "registered")
        self.assertEqual(states["mount:dunbar"], "known_unregistered")
        self.assertEqual(states["mount:obsidian"], "known_unregistered")
        self.assertTrue(all(item["observation"] is None for item in catalog))

    def test_schema_has_no_phase1_forbidden_storage_or_action_tables(self) -> None:
        schema_rows = self.core.store.connection.execute(
            "SELECT name,sql FROM sqlite_schema WHERE type='table' ORDER BY name"
        ).fetchall()
        rendered = "\n".join(
            f"{row['name']} {row['sql'] or ''}" for row in schema_rows
        ).casefold()
        for term in FORBIDDEN_PHASE1_TABLE_TERMS:
            self.assertNotIn(term, rendered)


if __name__ == "__main__":
    unittest.main()
