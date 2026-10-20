import unittest

from chat_policy import (
    PROMPT_SISTEMA,
    deterministic_chat_reply,
    is_contextless_numeric_message,
    is_dryness_complaint,
    is_emoji_only_message,
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

    def test_prompt_defines_persona_warmth_and_fact_checking(self):
        self.assertIn("eres papu, un gato digital/michi grasoso", PROMPT_SISTEMA)
        self.assertIn("tu personalidad es la de un gato", PROMPT_SISTEMA)
        self.assertIn("escribe siempre en minusculas", PROMPT_SISTEMA)
        self.assertIn("comete errores ortograficos y gramaticales a proposito", PROMPT_SISTEMA)
        self.assertIn('en vez de "pero", usa "but"', PROMPT_SISTEMA)
        self.assertIn('en vez de "cuando", usa "when"', PROMPT_SISTEMA)
        self.assertIn("nunca hables como español de España", PROMPT_SISTEMA)
        self.assertIn('"momos :v"', PROMPT_SISTEMA)
        self.assertIn('"elfa"', PROMPT_SISTEMA)
        self.assertIn("cero racismo", PROMPT_SISTEMA)
        self.assertIn("no como un contestador automatico", PROMPT_SISTEMA)
        self.assertIn("nunca fabriques tracklists", PROMPT_SISTEMA)
        self.assertIn('RESULTADOS DE BUSQUEDA WEB', PROMPT_SISTEMA)
        self.assertIn("no decir que no puedes buscar", PROMPT_SISTEMA)
        self.assertIn("no inventes lo que siente la persona", PROMPT_SISTEMA)

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

    def test_number_after_unrelated_list_does_not_get_guessed(self):
        answer = deterministic_chat_reply(
            "1.",
            has_prior_context=True,
            last_assistant_message="tracklist oficial: 1. welcome to america 2. ultra 3. real nice",
        )
        self.assertIsNotNone(answer)
        self.assertIn("nomas me llego", answer)

    def test_number_is_allowed_as_selection_only_after_explicit_prompt(self):
        answer = deterministic_chat_reply(
            "1.",
            has_prior_context=True,
            last_assistant_message="elige una opcion: 1. musica 2. juegos. responde con el numero.",
        )
        self.assertIsNone(answer)

    def test_emoji_only_message_is_detected(self):
        self.assertTrue(is_emoji_only_message("😭🙏"))
        self.assertTrue(is_emoji_only_message("[😭] [🙏]"))
        self.assertTrue(is_emoji_only_message("<:cry:123456><:pray:789012>"))
        self.assertFalse(is_emoji_only_message("😭🙏 que paso"))
        self.assertFalse(is_emoji_only_message("hola"))

    def test_emoji_reply_does_not_infer_user_emotions(self):
        answer = deterministic_chat_reply("😭🙏", has_prior_context=True)
        self.assertIsNotNone(answer)
        self.assertIn("no quiero inventarme que significan", answer)
        self.assertNotIn("pecho pesado", answer)
        self.assertNotIn("te toco el corazon", answer)
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

    def test_output_normalizer_lowercases_and_removes_vowel_accents(self):
        self.assertEqual(normalize_papu_style("¡HOLA, PAPÚ! ¿CÓMO ESTÁS?"), "¡hola, papu! ¿como estas?")
        self.assertEqual(normalize_papu_style("aquí está Ñoño"), "aqui esta ñoño")

    def test_output_normalizer_replaces_pero_and_cuando_with_papu_slang(self):
        self.assertEqual(
            normalize_papu_style("Pero cuando llegue, te aviso."),
            "but when llegue, te aviso.",
        )
        self.assertEqual(
            normalize_papu_style("no es pero si cuando?"),
            "no es but si when?",
        )

    def test_output_normalizer_does_not_change_words_inside_case_sensitive_urls(self):
        self.assertEqual(
            normalize_papu_style("cuando abres https://example.com/pero/cuando"),
            "when abres https://example.com/pero/cuando",
        )

    def test_output_normalizer_preserves_case_sensitive_urls(self):
        self.assertEqual(
            normalize_papu_style("mira https://example.com/MiAlbum/TrackA"),
            "mira https://example.com/MiAlbum/TrackA",
        )


if __name__ == "__main__":
    unittest.main()
