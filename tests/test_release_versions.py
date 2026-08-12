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
        self.assertEqual("2.1.6", plugin["version"])
        self.assertEqual("2.1.6", registry["runtime_version"])
        self.assertEqual("2.1.6", MODULE.VERSIONS["augment-of-mind"])
        self.assertEqual("1.1.6", MODULE.VERSIONS["software-verification"])
        self.assertEqual("1.1.6", MODULE.VERSIONS["verification-reviewer"])

    def test_integrated_fingerprint_matches_current_skill_bytes(self) -> None:
        recorded = json.loads(MODULE.OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(MODULE.build(), recorded)


if __name__ == "__main__":
    unittest.main()
