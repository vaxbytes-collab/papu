import unittest
from datetime import datetime, timezone

from moderation_cases import make_case_content


class ModerationCaseContentTests(unittest.TestCase):
    def test_case_message_uses_requested_markdown_fields_and_live_status(self):
        created_at = datetime(2026, 10, 19, 18, 28, tzinfo=timezone.utc)
        content = make_case_content(
            case_id=11,
            title="🚨 caso grave",
            username="kafiz",
            user_id=1370856709291118622,
            channel_name="Texto-general",
            channel_id=123456789012345678,
            category="sexual",
            severity=3,
            confidence=1.0,
            reason="amenaza de violencia sexual dirigida; requiere revision de moderacion",
            message_text="mensaje de ejemplo",
            message_url="https://discord.com/channels/123/123456789012345678/456789012345678901",
            status="ACCION APLICADA: mensaje eliminado, timeout aplicado durante 24 horas.",
            created_at=created_at,
        )
        for label in (
            "**[🚨](https://discord.com/assets/8d433206d7a0fe81.svg) caso grave**",
            "**usuario**",
            "**canal**",
            "**veredicto**",
            "**razon**",
            "**mensaje**",
            "**estado**",
            "**ir al mensaje**",
            "**id de infraccion: 11**",
        ):
            self.assertIn(label, content)
        self.assertIn("gravedad 3 · confianza 100%", content)
        self.assertIn("ACCION APLICADA", content)
        self.assertNotIn("PRUEBA", content)
        self.assertIn("https://discord.com/channels/123/123456789012345678/456789012345678901", content)
        self.assertLessEqual(len(content), 2000)

    def test_user_report_can_have_unassessed_verdict(self):
        content = make_case_content(
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
        self.assertIn("gravedad sin evaluar · confianza sin evaluar", content)
        self.assertIn("**reportado por**", content)
        self.assertIn("pendiente de revision humana", content)

    def test_invalid_external_message_link_is_not_rendered_as_clickable(self):
        content = make_case_content(
            case_id=13,
            title="reporte",
            username="example",
            user_id=1234,
            channel_name="general",
            channel_id=5678,
            category="reporte",
            severity="sin evaluar",
            confidence="sin evaluar",
            reason="motivo",
            message_text="texto",
            status="pendiente",
            message_url="https://example.com/fake",
        )
        self.assertIn("enlace al mensaje no disponible", content)
        self.assertNotIn("[generalMensaje", content)


if __name__ == "__main__":
    unittest.main()
