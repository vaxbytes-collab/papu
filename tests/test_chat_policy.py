import unittest

from chat_policy import PROMPT_SISTEMA, is_contextless_numeric_message


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


if __name__ == "__main__":
    unittest.main()
