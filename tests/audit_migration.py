"""Explicit historical audit of the imported Free My TV snapshot a9e1027.

Run: python -B tests/audit_migration.py
Not discovered by the permanent test suite. Later customizations may legitimately
differ from this snapshot; do not refresh the historical inventory to hide them.
"""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MigrationAudit(unittest.TestCase):
    def test_imported_snapshot_a9e1027(self):
        inventory = json.loads((ROOT / "docs/migration-inventory.json").read_text(encoding="utf-8"))
        # These files were deliberately adapted during the initial reorganization.
        adapted = {"scripts/prepare_preview.py", "scripts/prepare_tizen.py",
                   "scripts/webapp.py", "scripts/translate.py", "tizen/config.xml"}
        self.assertEqual(inventory["commit"], "a9e1027")
        for item in inventory["files"]:
            with self.subTest(path=item["target"]):
                path = ROOT / item["target"]
                self.assertTrue(path.is_file())
                if item["target"] not in adapted:
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"],
                                     "Differs from historical snapshot a9e1027; may be an intentional customization")

    def test_previous_app_backup(self):
        folder = ROOT / "backups/previous-app"
        if not folder.exists():
            self.skipTest("Local backup absent; previous application is preserved in Git")
        for item in json.loads((folder / "inventory.json").read_text(encoding="utf-8")):
            with self.subTest(path=item["path"]):
                self.assertEqual(hashlib.sha256((folder / item["path"]).read_bytes()).hexdigest(),
                                 item["sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
