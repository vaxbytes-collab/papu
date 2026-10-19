import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import papu_store


class PapuStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patch = patch.object(papu_store, "DATA_DIR", Path(self.temp.name))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_render_defaults_to_var_data(self):
        self.assertEqual(
            papu_store._select_data_dir({"RENDER_SERVICE_ID": "srv-test"}, cwd="/project"),
            Path("/var/data"),
        )

    def test_explicit_data_dir_overrides_render_default(self):
        self.assertEqual(
            papu_store._select_data_dir(
                {"RENDER_SERVICE_ID": "srv-test", "PAPU_DATA_DIR": "/custom/store"},
                cwd="/project",
            ),
            Path("/custom/store"),
        )

    def test_local_default_is_data_subdirectory(self):
        self.assertEqual(
            papu_store._select_data_dir({}, cwd="/project"),
            Path("/project/data"),
        )

    def test_round_trip_unicode_and_nested_data(self):
        value = {"guild": {"michi": "Bigotes 🐈", "coins": 12}}
        papu_store.save_json("state.json", value)
        self.assertEqual(papu_store.load_json("state.json", {}), value)

    def test_missing_or_invalid_file_returns_default(self):
        self.assertEqual(papu_store.load_json("missing.json", []), [])
        papu_store.data_path("broken.json").write_text("{oops", encoding="utf-8")
        self.assertEqual(papu_store.load_json("broken.json", {}), {})

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            papu_store.data_path("../secrets.json")

    def test_atomic_write_leaves_valid_json(self):
        papu_store.save_json("atomic.json", {"ok": True})
        self.assertEqual(json.loads(papu_store.data_path("atomic.json").read_text(encoding="utf-8")), {"ok": True})

    def test_migrates_legacy_data_without_overwriting_existing_data(self):
        legacy = Path(self.temp.name) / "legacy"
        destination = Path(self.temp.name) / "destination"
        legacy.mkdir()
        destination.mkdir()
        (legacy / "pets.json").write_text('{"123": {"name": "bigotes"}}', encoding="utf-8")
        (legacy / "events.json").write_text('{"old": "event"}', encoding="utf-8")
        (destination / "events.json").write_text('{"new": "event"}', encoding="utf-8")
        with patch.object(papu_store, "DATA_DIR", destination):
            copied = papu_store._migrate_legacy_data([legacy])
        self.assertEqual(copied, 1)
        self.assertEqual(json.loads((destination / "pets.json").read_text(encoding="utf-8")), {"123": {"name": "bigotes"}})
        self.assertEqual(json.loads((destination / "events.json").read_text(encoding="utf-8")), {"new": "event"})

    def test_migration_skips_invalid_legacy_json(self):
        legacy = Path(self.temp.name) / "legacy"
        destination = Path(self.temp.name) / "destination"
        legacy.mkdir()
        destination.mkdir()
        (legacy / "pets.json").write_text("{broken", encoding="utf-8")
        with patch.object(papu_store, "DATA_DIR", destination):
            copied = papu_store._migrate_legacy_data([legacy])
        self.assertEqual(copied, 0)
        self.assertFalse((destination / "pets.json").exists())


if __name__ == "__main__":
    unittest.main()
