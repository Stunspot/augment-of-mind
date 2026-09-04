from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FINGERPRINT_SCRIPT = ROOT / "scripts" / "build_integrated_fingerprint.py"

SPEC = importlib.util.spec_from_file_location(
    "build_integrated_fingerprint", FINGERPRINT_SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

TESTFORGE_TREE_SHA256 = {
    "software-verification": "a075641cfaae67027d6ecc25fbe934177eb394b489c77cac560104085858edd7",
    "verification-reviewer": "9e6e05eafa85d5ddd973e8d0aec572ac8ff38870faa81dd4b1929d9e369de465",
}


class ReleaseVersionTests(unittest.TestCase):
    def test_release_identity_is_synchronized(self) -> None:
        plugin = json.loads(
            (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        registry = json.loads(
            (
                ROOT
                / "skills"
                / "augment-of-mind"
                / "references"
                / "faculty-runtime"
                / "faculty-registry.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual("2.1.7", plugin["version"])
        self.assertEqual("2.1.7", registry["runtime_version"])
        self.assertEqual("2.1.7", MODULE.VERSIONS["augment-of-mind"])
        self.assertEqual("1.1.6", MODULE.VERSIONS["software-verification"])
        self.assertEqual("1.1.6", MODULE.VERSIONS["verification-reviewer"])

    def test_current_branch_is_legacy_compatibility_not_a_product_lane(self) -> None:
        plugin = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        decision = (ROOT / "design" / "DEC-MIND-PRODUCT-SUCCESSION.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(plugin["interface"]["displayName"], "MIND Legacy Compatibility")
        self.assertIn("Legacy Compatibility", marketplace["interface"]["displayName"])
        verifier = (ROOT / "scripts" / "verify_release.py").read_text(encoding="utf-8")
        self.assertIn(
            'MARKETPLACE_DISPLAY_NAME = "Collaborative Dynamics: MIND (Legacy Compatibility)"',
            verifier,
        )
        self.assertIn("standalone “Augment of MIND” product lane is superseded", decision)
        self.assertIn("No new standalone MIND release", decision)
        self.assertIn("MIND is Nova's edition-invariant cognitive architecture", readme)
        self.assertIn("Do not disable or uninstall", readme)

    def test_integrated_fingerprint_matches_current_skill_bytes(self) -> None:
        recorded = json.loads(MODULE.OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(MODULE.build(), recorded)

    def test_testforge_1_1_6_skill_trees_remain_exact(self) -> None:
        recorded = json.loads(MODULE.OUTPUT.read_text(encoding="utf-8"))
        observed = {
            capability["name"]: capability["tree_sha256"]
            for capability in recorded["capabilities"]
            if capability["name"] in TESTFORGE_TREE_SHA256
        }
        self.assertEqual(TESTFORGE_TREE_SHA256, observed)


if __name__ == "__main__":
    unittest.main()
