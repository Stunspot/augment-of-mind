from __future__ import annotations

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
from verify_release import (  # noqa: E402
    MARKETPLACE_DISPLAY_NAME,
    MARKETPLACE_NAME,
    ReleaseError,
    validate_payload_path,
    verify_marketplace,
)


class ReleaseToolingTests(unittest.TestCase):
    def test_skill_selection_excludes_development_material(self) -> None:
        selected = skill_release_files(REPO_ROOT / "skills")
        relative = {
            path.relative_to(REPO_ROOT / "skills").as_posix() for path in selected
        }
        self.assertEqual(sum(path.endswith("/SKILL.md") for path in relative), 16)
        self.assertIn(
            "cognitive-continuity/scripts/continuity_store.py",
            relative,
        )
        for path in relative:
            self.assertNotIn("/evals/", f"/{path}")
            self.assertNotIn("/tests/", f"/{path}")
            self.assertNotIn("/__pycache__/", f"/{path}")
            self.assertFalse(path.endswith((".pyc", ".pyo")))

    def test_verifier_enforces_the_same_skill_boundary(self) -> None:
        validate_payload_path("skills/sensemaking/SKILL.md")
        validate_payload_path("skills/cognitive-continuity/scripts/continuity_store.py")
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


if __name__ == "__main__":
    unittest.main()
