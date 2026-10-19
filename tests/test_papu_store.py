import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

    def test_render_relative_data_dir_is_resolved_inside_persistent_disk(self):
        self.assertEqual(
            papu_store._select_data_dir(
                {"RENDER_SERVICE_ID": "srv-test", "PAPU_DATA_DIR": "data"},
                cwd="/project",
            ),
            Path("/var/data/data"),
        )

    def test_render_dot_directory_does_not_escape_persistent_disk(self):
        self.assertEqual(
            papu_store._select_data_dir(
                {"RENDER_SERVICE_ID": "srv-test", "PAPU_DATA_DIR": "."},
                cwd="/project",
            ),
            Path("/var/data/."),
        )

    def test_chat_history_is_included_in_persisted_files(self):
        self.assertIn("chat_histories.json", papu_store.PERSISTED_JSON_FILES)

    def test_round_trip_unicode_and_nested_data(self):
        value = {"guild": {"michi": "Bigotes 🐈", "coins": 12}}
        papu_store.save_json("state.json", value)
        self.assertEqual(papu_store.load_json("state.json", {}), value)

    def test_postgres_load_reads_jsonb_value(self):
        expected = {"guild": {"michi": "Bigotes 🐈", "coins": 12}}
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://papu:test@db.example/papu"}):
            with patch("papu_store.psycopg.connect") as connect:
                connection = connect.return_value.__enter__.return_value
                connection.execute.return_value.fetchone.return_value = (expected,)
                actual = papu_store.load_json("pets.json", {})
        self.assertEqual(actual, expected)
        connect.assert_called_once_with(
            "postgresql://papu:test@db.example/papu", connect_timeout=8
        )
        self.assertIn("SELECT value FROM papu_json_store", connection.execute.call_args.args[0])

    def test_postgres_save_upserts_jsonb_value(self):
        value = {"michi": "Bigotes 🐈", "coins": 12}
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://papu:test@db.example/papu"}):
            with patch("papu_store.psycopg.connect") as connect:
                connection = connect.return_value.__enter__.return_value
                papu_store.save_json("pets.json", value)
        statement, params = connection.execute.call_args.args
        self.assertIn("ON CONFLICT (key) DO UPDATE", statement)
        self.assertEqual(params[0], "pets.json")
        self.assertIsInstance(params[1], papu_store.Jsonb)

    def test_database_error_does_not_silently_fallback_to_local_json(self):
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://papu:test@db.example/papu"}):
            with patch("papu_store.psycopg.connect", side_effect=RuntimeError("database down")):
                with self.assertRaises(RuntimeError):
                    papu_store.load_json("pets.json", {})

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

    def test_postgres_import_uses_do_nothing_to_preserve_existing_database_rows(self):
        legacy = Path(self.temp.name) / "legacy"
        legacy.mkdir()
        (legacy / "pets.json").write_text('{"123": {"name": "bigotes"}}', encoding="utf-8")
        connection = MagicMock()
        connection.execute.return_value.fetchone.return_value = None
        imported = papu_store._migrate_legacy_data_to_postgres(connection, [legacy])
        self.assertEqual(imported, 0)
        statement, params = connection.execute.call_args.args
        self.assertIn("ON CONFLICT (key) DO NOTHING", statement)
        self.assertEqual(params[0], "pets.json")
        self.assertIsInstance(params[1], papu_store.Jsonb)


if __name__ == "__main__":
    unittest.main()
