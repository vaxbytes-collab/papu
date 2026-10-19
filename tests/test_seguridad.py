import unittest
from collections import deque

from seguridad import contains_discord_invite, count_recent_events


class SecurityHelpersTests(unittest.TestCase):
    def test_detects_supported_discord_invite_formats(self):
        samples = (
            "entra aqui: https://discord.gg/AbC123",
            "discord.com/invite/a-valid-code",
            "https://www.discordapp.com/invite/Code_123",
            "mira discord.gg/abc-DEF",
        )
        for text in samples:
            with self.subTest(text=text):
                self.assertTrue(contains_discord_invite(text))

    def test_normal_links_and_plain_text_are_not_invites(self):
        for text in (
            "https://example.com/invite/abc",
            "mi palabra discord es bonita",
            "",
            "discord.gg",
            "discord.com/invite",
        ):
            with self.subTest(text=text):
                self.assertFalse(contains_discord_invite(text))

    def test_recent_event_window_discards_old_entries(self):
        events = deque([4.0, 6.0, 8.0])
        count = count_recent_events(events, now=10.0, window_seconds=5)
        self.assertEqual(count, 2)
        self.assertEqual(list(events), [6.0, 8.0])

    def test_recent_event_window_keeps_events_on_cutoff(self):
        events = deque([4.9, 5.0, 5.1])
        count = count_recent_events(events, now=8.0, window_seconds=3)
        self.assertEqual(count, 2)
        self.assertEqual(list(events), [5.0, 5.1])


if __name__ == "__main__":
    unittest.main()
