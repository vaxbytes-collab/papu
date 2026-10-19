import unittest
from datetime import datetime, timezone

import discord

from moderation_cases import make_case_embed


class ModerationCaseEmbedTests(unittest.TestCase):
    def test_case_embed_uses_requested_fields_and_live_status(self):
        created_at = datetime(2026, 10, 19, 18, 28, tzinfo=timezone.utc)
        embed = make_case_embed(
            case_id=11,
            title="🚨 caso grave",
            username="kafiz",
            user_id=1370856709291118622,
            channel_name="Texto-general",
            channel_id=123456789012345678,
            category="sexual",
            severity=3,
            confidence=1.0,
            reason="amenaza de violencia sexual dirigida, requiere revision de moderacion",
            message_text="mensaje de ejemplo",
            message_url="https://discord.com/channels/123/123456789012345678/456789012345678901",
            status="ACCION APLICADA: mensaje eliminado, timeout aplicado durante 24 horas.",
            created_at=created_at,
        )
        fields = {field.name: field.value for field in embed.fields}
        self.assertEqual(embed.title, "🚨 caso grave")
        self.assertEqual(
            list(fields),
            ["usuario", "canal", "veredicto", "razon", "mensaje", "estado", "ir al mensaje", "id de infraccion"],
        )
        self.assertIn("gravedad 3", fields["veredicto"])
        self.assertIn("confianza 100%", fields["veredicto"])
        self.assertNotIn("PRUEBA", fields["estado"])
        self.assertIn("ACCION APLICADA", fields["estado"])
        self.assertIn("https://discord.com/channels/123/123456789012345678/456789012345678901", fields["ir al mensaje"])
        self.assertIn("11", fields["id de infraccion"])

    def test_report_case_can_show_unassessed_verdict(self):
        embed = make_case_embed(
            case_id=12,
            title="📨 reporte recibido",
            username="example",
            user_id=1234,
            channel_name="general",
            channel_id=5678,
            category="reporte del usuario",
            severity="sin evaluar",
            confidence="sin evaluar",
            reason="motivo enviado al staff",
            message_text="sin texto aportado",
            status="REPORTE RECIBIDO: pendiente de revision humana.",
            reporter="reportero (9876)",
        )
        fields = {field.name: field.value for field in embed.fields}
        self.assertIn("sin evaluar", fields["veredicto"])
        self.assertIn("reportado por", fields)
        self.assertIn("pendiente de revision humana", fields["estado"])


if __name__ == "__main__":
    unittest.main()
