import unittest

from chat_policy import (
    PROMPT_SISTEMA,
    deterministic_chat_reply,
    is_contextless_numeric_message,
    is_spanish_language_complaint,
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

    def test_prompt_enforces_spanish_by_default(self):
        self.assertIn("Responde SIEMPRE en español latinoamericano", PROMPT_SISTEMA)
        self.assertIn("Nunca abras una conversación con un saludo genérico en inglés", PROMPT_SISTEMA)
        self.assertIn("pregunta en español", PROMPT_SISTEMA)

    def test_spanish_language_complaint_is_detected(self):
        self.assertTrue(is_spanish_language_complaint("porque hablas ingles?"))
        self.assertTrue(is_spanish_language_complaint("¿Por qué respondes en inglés?"))
        self.assertFalse(is_spanish_language_complaint("I prefer English, please"))

    def test_first_numeric_ping_gets_deterministic_spanish_reply(self):
        answer = deterministic_chat_reply("1.", has_prior_context=False)
        self.assertIsNotNone(answer)
        self.assertIn("¿Qué querías decir?", answer)

    def test_language_complaint_gets_deterministic_spanish_apology(self):
        answer = deterministic_chat_reply("porque hablas ingles?", has_prior_context=True)
        self.assertIsNotNone(answer)
        self.assertIn("me equivoqué al responder en inglés", answer)
        self.assertIn("seguir en español", answer)

    def test_numeric_answer_with_existing_context_is_passed_to_ai(self):
        self.assertIsNone(deterministic_chat_reply("1.", has_prior_context=True))


if __name__ == "__main__":
    unittest.main()
