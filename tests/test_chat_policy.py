import unittest

from chat_policy import (
    PROMPT_SISTEMA,
    deterministic_chat_reply,
    is_contextless_numeric_message,
    is_dryness_complaint,
    is_spanish_language_complaint,
    normalize_papu_style,
)


class ChatPolicyTests(unittest.TestCase):
    def test_ambiguous_numeric_message_is_detected(self):
        for value in ("1.", "  2  ", "???", "#3"):
            with self.subTest(value=value):
                self.assertTrue(is_contextless_numeric_message(value))

    def test_normal_text_is_not_classified_as_numeric(self):
        for value in ("hola", "porque hablas ingles?", "hello there", "1 y luego"):
            with self.subTest(value=value):
                self.assertFalse(is_contextless_numeric_message(value))

    def test_prompt_defines_persona_format_and_warmth(self):
        self.assertIn("eres papu, un michi/gato grasoso y basado de sonora", PROMPT_SISTEMA)
        self.assertIn("escribe siempre en minusculas", PROMPT_SISTEMA)
        self.assertIn("no uses vocales acentuadas", PROMPT_SISTEMA)
        self.assertIn("cero racismo", PROMPT_SISTEMA)
        self.assertIn("papucollective", PROMPT_SISTEMA)
        self.assertIn("no reveles el historial", PROMPT_SISTEMA)
        self.assertIn("no como un contestador automatico", PROMPT_SISTEMA)
        self.assertIn("los emojis, emoticonos y pacmans SI estan permitidos", PROMPT_SISTEMA)

    def test_language_complaint_is_detected(self):
        self.assertTrue(is_spanish_language_complaint("porque hablas ingles?"))
        self.assertTrue(is_spanish_language_complaint("¿Por qué respondes en inglés?"))
        self.assertFalse(is_spanish_language_complaint("I prefer English, please"))

    def test_dryness_complaint_is_detected_and_answer_is_warm(self):
        message = "porq eres tan seco :,v"
        self.assertTrue(is_dryness_complaint(message))
        answer = deterministic_chat_reply(message, has_prior_context=True)
        self.assertIsNotNone(answer)
        self.assertIn("jaja perdon, compa", answer)
        self.assertIn("cotorrear tambien", answer)
        self.assertEqual(answer, normalize_papu_style(answer))

    def test_first_numeric_ping_gets_playful_reply(self):
        answer = deterministic_chat_reply("1.", has_prior_context=False)
        self.assertIsNotNone(answer)
        self.assertIn("jajaja papu", answer)
        self.assertEqual(answer, normalize_papu_style(answer))

    def test_language_complaint_gets_deterministic_spanish_apology(self):
        answer = deterministic_chat_reply("porque hablas ingles?", has_prior_context=True)
        self.assertIsNotNone(answer)
        self.assertIn("me equivoque al responder en ingles", answer)
        self.assertIn("seguir en espanol", answer)
        self.assertEqual(answer, normalize_papu_style(answer))

    def test_attachments_get_warm_explanation_and_alternative(self):
        answer = deterministic_chat_reply("mira esto", has_prior_context=True, has_attachments=True)
        self.assertIn("compa", answer)
        self.assertIn("lo revisamos juntos", answer)
        self.assertEqual(answer, normalize_papu_style(answer))

    def test_numeric_answer_with_existing_context_is_passed_to_ai(self):
        self.assertIsNone(deterministic_chat_reply("1.", has_prior_context=True))

    def test_output_normalizer_lowercases_and_removes_vowel_accents(self):
        self.assertEqual(normalize_papu_style("¡HOLA, PAPÚ! ¿CÓMO ESTÁS?"), "¡hola, papu! ¿como estas?")
        self.assertEqual(normalize_papu_style("aquí está Ñoño"), "aqui esta ñoño")


if __name__ == "__main__":
    unittest.main()
