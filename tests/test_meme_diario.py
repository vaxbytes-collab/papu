import unittest
from datetime import datetime

from meme_diario import parse_publish_time, publication_is_due, validate_timezone


class MemeDiarioTests(unittest.TestCase):
    def test_parse_publish_time_normalizes_valid_time(self):
        self.assertEqual(parse_publish_time("09:05"), "09:05")
        self.assertEqual(parse_publish_time(" 23:59 "), "23:59")

    def test_parse_publish_time_rejects_invalid_values(self):
        for value in ("9:05", "24:00", "12:60", "noon", "", "12:00:00"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_publish_time(value)

    def test_timezone_validation_accepts_iana_timezone(self):
        self.assertEqual(validate_timezone("Europe/Madrid"), "Europe/Madrid")

    def test_timezone_validation_rejects_unknown_zone(self):
        with self.assertRaises(ValueError):
            validate_timezone("Mars/Olympus")

    def test_publication_due_at_or_after_time_once_per_local_day(self):
        now = datetime(2026, 10, 21, 12, 30)
        self.assertFalse(publication_is_due(now, "12:00", "2026-10-21"))
        self.assertTrue(publication_is_due(now, "12:00", "2026-10-20"))
        self.assertFalse(publication_is_due(datetime(2026, 10, 21, 11, 59), "12:00", "2026-10-20"))

    def test_publication_due_before_configured_time_is_false(self):
        self.assertFalse(publication_is_due(datetime(2026, 10, 21, 9, 0), "12:00", ""))


if __name__ == "__main__":
    unittest.main()
