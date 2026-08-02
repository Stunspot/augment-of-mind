from __future__ import annotations

import json
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
import zipfile


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_release import (  # noqa: E402
    ARCHIVE_ROOT,
    BuildError,
    build_zip,
    safe_extract,
    skill_release_files,
)
from build_integrated_fingerprint import build as build_integrated_fingerprint  # noqa: E402
from verify_release import (  # noqa: E402
    MARKETPLACE_DISPLAY_NAME,
    MARKETPLACE_NAME,
    ReleaseError,
    validate_payload_path,
    verify_marketplace,
)


class ReleaseToolingTests(unittest.TestCase):
    def test_integrated_capability_fingerprint_recomputes_from_source(self) -> None:
        recorded = json.loads(
            (REPO_ROOT / "skills" / "augment-of-mind" / "assets" / "integrated-capability-fingerprint.json").read_text(encoding="utf-8")
        )
        self.assertEqual(recorded, build_integrated_fingerprint())


    def test_skill_selection_excludes_development_material(self) -> None:
        selected = skill_release_files(REPO_ROOT / "skills")
        relative = {
            path.relative_to(REPO_ROOT / "skills").as_posix() for path in selected
        }
        self.assertEqual(sum(path.endswith("/SKILL.md") for path in relative), 17)
        self.assertIn(
            "cognitive-continuity/scripts/continuity_store.py",
            relative,
        )
        self.assertIn("agentic-eros/SKILL.md", relative)
        self.assertIn("agentic-eros/manifest.json", relative)
        self.assertIn(
            "agentic-eros/references/eros-and-relational-perception.md",
            relative,
        )
        self.assertNotIn("agentic-eros/evals/eval-manifest.yaml", relative)
        self.assertNotIn("agentic-eros/scripts/validate_package.py", relative)
        for path in relative:
            self.assertNotIn("/evals/", f"/{path}")
            self.assertNotIn("/tests/", f"/{path}")
            self.assertNotIn("/__pycache__/", f"/{path}")
            self.assertFalse(path.endswith((".pyc", ".pyo")))

    def test_verifier_enforces_the_same_skill_boundary(self) -> None:
        validate_payload_path("skills/sensemaking/SKILL.md")
        validate_payload_path("skills/agentic-eros/manifest.json")
        validate_payload_path("skills/cognitive-continuity/scripts/continuity_store.py")
        validate_payload_path("scripts/query_associative_field.py")
        validate_payload_path("scripts/build_associative_assets.py")
        with self.assertRaises(ReleaseError):
            validate_payload_path("scripts/unapproved.py")
        with self.assertRaises(ReleaseError):
            validate_payload_path("skills/sensemaking/evals/eval-manifest.yaml")
        with self.assertRaises(ReleaseError):
            validate_payload_path("skills/agent-striving/scripts/tests/test_state.py")
        with self.assertRaises(ReleaseError):
            validate_payload_path("skills/sensemaking/unclassified/file.txt")
        with self.assertRaises(ReleaseError):
            validate_payload_path(".")

    def test_marketplace_identity_binds_machine_and_display_names(self) -> None:
        marketplace = {
            "name": MARKETPLACE_NAME,
            "interface": {"displayName": MARKETPLACE_DISPLAY_NAME},
            "plugins": [
                {
                    "name": "augment-of-mind",
                    "source": {"source": "local", "path": "./"},
                }
            ],
        }
        verify_marketplace(marketplace)

        wrong_name = dict(marketplace)
        wrong_name["name"] = "collaborative-dynamics"
        with self.assertRaisesRegex(ReleaseError, "identity, display metadata"):
            verify_marketplace(wrong_name)

        wrong_display = dict(marketplace)
        wrong_display["interface"] = {"displayName": "Collaborative Dynamics"}
        with self.assertRaisesRegex(ReleaseError, "identity, display metadata"):
            verify_marketplace(wrong_display)

    def test_two_zip_builds_are_byte_identical_with_fixed_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mind-zip-test-") as temporary:
            root = Path(temporary) / "stage"
            root.mkdir()
            (root / "alpha.txt").write_text("alpha\n", encoding="utf-8", newline="\n")
            nested = root / "nested"
            nested.mkdir()
            (nested / "beta.txt").write_text("beta\n", encoding="utf-8", newline="\n")
            first = Path(temporary) / "first.zip"
            second = Path(temporary) / "second.zip"
            build_zip(root, first)
            build_zip(root, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.comment, b"")
                for member in archive.infolist():
                    self.assertEqual(member.create_system, 3)
                    self.assertEqual(member.date_time, (2026, 1, 1, 0, 0, 0))

    def test_safe_extract_rejects_duplicate_members_before_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mind-zip-test-") as temporary:
            archive_path = Path(temporary) / "duplicate.zip"
            name = f"{ARCHIVE_ROOT}/README.md"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(archive_path, "w") as archive:
                    archive.writestr(name, b"first")
                    archive.writestr(name, b"second")
            destination = Path(temporary) / "extract"
            with self.assertRaisesRegex(BuildError, "duplicate member"):
                safe_extract(archive_path, destination)
            self.assertFalse(destination.exists())

    def test_safe_extract_rejects_directory_members(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mind-zip-test-") as temporary:
            archive_path = Path(temporary) / "directory.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(f"{ARCHIVE_ROOT}/", b"")
            with self.assertRaisesRegex(BuildError, "unsafe archive member"):
                safe_extract(archive_path, Path(temporary) / "extract")


    def test_registry_and_agentic_eros_promotion_contract(self) -> None:
        registry_path = (
            REPO_ROOT
            / "skills"
            / "augment-of-mind"
            / "references"
            / "faculty-runtime"
            / "faculty-registry.json"
        )
        runtime_path = registry_path.with_name("runtime.md")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        faculties = registry["faculties"]
        by_name = {faculty["name"]: faculty for faculty in faculties}

        self.assertEqual(registry["faculty_count"], 16)
        self.assertEqual(len(faculties), 16)
        self.assertEqual(len(by_name), 16)
        eros = by_name["agentic-eros"]
        self.assertIn("associatively surfaced", eros["activate_when"])
        self.assertIn("absent invitation", eros["must_not_own"])
        self.assertIn("durable intimate inference", eros["must_not_own"])

        eros_root = REPO_ROOT / "skills" / "agentic-eros"
        metadata = (eros_root / "agents" / "openai.yaml").read_text(encoding="utf-8")
        manifest = json.loads((eros_root / "manifest.json").read_text(encoding="utf-8"))
        runtime = runtime_path.read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: true", metadata)
        self.assertEqual(manifest["name"], "agentic-eros")
        self.assertEqual(manifest["version"], "0.2.0")
        self.assertEqual(manifest["privacy_default"], "transient conversation state")
        self.assertIn("that reminder is attention, not selection", runtime)
        self.assertIn("association into activation", runtime)
        self.assertIn("Only explicit user authority", runtime)

        fingerprint_path = (
            REPO_ROOT
            / "skills"
            / "augment-of-mind"
            / "assets"
            / "integrated-capability-fingerprint.json"
        )
        fingerprint = json.loads(fingerprint_path.read_text(encoding="utf-8"))
        fingerprint_by_name = {item["name"]: item for item in fingerprint["capabilities"]}
        self.assertEqual(fingerprint["capability_count"], 17)
        self.assertEqual(fingerprint["faculty_count"], 16)
        self.assertEqual(
            fingerprint_by_name["agentic-eros"]["tree_sha256"],
            "39c22a578415776263204a97dea4ea82db84341168bc8173db961823816e9ae9",
        )

        eval_root = REPO_ROOT / "skills" / "augment-of-mind" / "evals"
        eval_manifest = json.loads(
            (eval_root / "eval-manifest.yaml").read_text(encoding="utf-8")
        )
        runtime_cases = json.loads(
            (eval_root / "faculty-runtime-cases.yaml").read_text(encoding="utf-8")
        )
        self.assertTrue(
            {
                "implicit_eros_promotion",
                "eros_expression_gate",
                "intimate_state_boundary",
            }.issubset(eval_manifest["indispensable_dimensions"])
        )
        case_ids = {case["id"] for case in runtime_cases["cases"]}
        self.assertTrue({"HAFR-010", "HAFR-011", "HAFR-012"}.issubset(case_ids))


if __name__ == "__main__":
    unittest.main()
