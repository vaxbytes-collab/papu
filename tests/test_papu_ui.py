import unittest

import discord

from papu_ui import PALETTE, branded_embed, feedback_embed, progress_bar, status_label


class PapuUiTests(unittest.TestCase):
    def test_branded_embed_uses_papu_palette_and_footer(self):
        embed = branded_embed(title="Prueba", description="Tarjeta de prueba")
        self.assertEqual(embed.color.value, PALETTE["cyan"])
        self.assertIn("PapuCollective", embed.footer.text)
        self.assertIsNotNone(embed.timestamp)

    def test_legacy_blurple_maps_to_violet(self):
        embed = branded_embed(title="Prueba", color=discord.Color.blurple())
        self.assertEqual(embed.color.value, PALETTE["violet"])

    def test_custom_color_is_preserved(self):
        custom = 0x123456
        embed = branded_embed(title="Prueba", color=custom)
        self.assertEqual(embed.color.value, custom)

    def test_custom_footer_keeps_branding(self):
        embed = branded_embed(title="Prueba", footer="Michi • Cuidado")
        self.assertEqual(embed.footer.text, "Michi • Cuidado • PapuCollective")

    def test_feedback_embed_uses_tone(self):
        embed = feedback_embed("Todo correcto.", title="Guardado", tone="success")
        self.assertIn("Guardado", embed.title)
        self.assertEqual(embed.color.value, PALETTE["success"])
        self.assertEqual(embed.description, "Todo correcto.")

    def test_progress_bar_clamps_values(self):
        self.assertEqual(progress_bar(100, width=4), "▰▰▰▰")
        self.assertEqual(progress_bar(0, width=4), "▱▱▱▱")
        self.assertEqual(progress_bar(200, width=4), "▰▰▰▰")
        self.assertEqual(progress_bar(-5, width=4), "▱▱▱▱")

    def test_progress_bar_handles_invalid_values(self):
        self.assertEqual(len(progress_bar("bad", width=5)), 5)

    def test_status_label_is_consistent(self):
        self.assertEqual(status_label(True), "🟢 Activado")
        self.assertEqual(status_label(False), "⚪ Desactivado")


if __name__ == "__main__":
    unittest.main()
