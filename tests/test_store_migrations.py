from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mind_core import MindCore
from mind_core.errors import MigrationError, WriterLeaseError

from tests.helpers import bootstrap_fixture


class StoreMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "mind-core.sqlite3"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_second_writer_is_rejected(self) -> None:
        first = MindCore(self.database)
        try:
            with self.assertRaises(WriterLeaseError):
                MindCore(self.database)
        finally:
            first.close()

    def test_second_process_is_rejected_and_lock_releases_on_clean_close(self) -> None:
        first = MindCore(self.database)
        child_code = (
            "import sys; "
            "from mind_core import MindCore; "
            "from mind_core.errors import WriterLeaseError; "
            "\ntry: MindCore(sys.argv[1])"
            "\nexcept WriterLeaseError: raise SystemExit(0)"
            "\nraise SystemExit(3)"
        )
        try:
            result = subprocess.run(
                [sys.executable, "-B", "-X", "utf8", "-c", child_code, str(self.database)],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(first.status()["counts"]["receipts"], 0)
        finally:
            first.close()
        reopened = MindCore(self.database)
        reopened.close()

    def test_bootstrap_state_survives_clean_restart(self) -> None:
        first = MindCore(self.database)
        first.bootstrap(bootstrap_fixture())
        core_id = first.status()["core_instance_id"]
        first.close()
        reopened = MindCore(self.database)
        try:
            self.assertEqual(reopened.status()["core_instance_id"], core_id)
            self.assertEqual(
                reopened.estate.resolve("egdod")[0]["capability_id"],
                "capability:egdod",
            )
        finally:
            reopened.close()

    def test_migration_checksum_tampering_fails_closed(self) -> None:
        core = MindCore(self.database)
        core.close()
        connection = sqlite3.connect(self.database)
        try:
            connection.execute(
                "UPDATE schema_migrations SET checksum=? WHERE migration_id=?",
                ("0" * 64, "0001_core_metadata"),
            )
            connection.commit()
        finally:
            connection.close()
        with self.assertRaises(MigrationError):
            MindCore(self.database)

    def test_non_database_bytes_fail_before_service_start(self) -> None:
        self.database.write_bytes(b"this is not a sqlite database")
        with self.assertRaises(MigrationError):
            MindCore(self.database)


if __name__ == "__main__":
    unittest.main()
