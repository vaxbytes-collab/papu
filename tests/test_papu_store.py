import json
import os
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


if __name__ == "__main__":
    unittest.main()
