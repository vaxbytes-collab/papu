import unittest
from unittest.mock import patch

from web_search import (
    build_search_query,
    format_search_context,
    format_search_reply,
    search_web,
    should_search_web,
)


class WebSearchTests(unittest.TestCase):
    def test_explicit_search_request_is_detected(self):
        self.assertTrue(should_search_web("busca"))
        self.assertTrue(should_search_web("buscala porfa"))
        self.assertTrue(should_search_web("investiga esto"))

    def test_music_tracklist_questions_trigger_search(self):
        self.assertTrue(should_search_web("dime la tracklist de ye"))
        self.assertTrue(should_search_web("lista de canciones del album"))
        self.assertFalse(should_search_web("porq eres tan seco"))

    def test_bare_search_command_uses_previous_user_context(self):
        history = [
            {"role": "user", "content": "te voy a volver a preguntar, dime la tracklist de ye"},
            {"role": "assistant", "content": "a que edicion te refieres?"},
            {"role": "user", "content": "de 2018"},
        ]
        query = build_search_query("busca", history)
        self.assertIn("tracklist", query.lower())
        self.assertIn("2018", query)
        self.assertIn("kanye west", query.lower())
        self.assertIn("official album tracklist", query.lower())

    def test_search_request_with_topic_uses_current_text(self):
        query = build_search_query("busca tracklist de ye 2018")
        self.assertIn("tracklist", query.lower())
        self.assertIn("2018", query)
        self.assertIn("kanye west", query.lower())

    def test_life_of_pablo_tracklist_is_enriched_with_artist(self):
        query = build_search_query("busca the life of pablo tracklist")
        self.assertIn("kanye west", query.lower())

    def test_bare_search_does_not_forward_private_chat_without_factual_topic(self):
        history = [
            {"role": "user", "content": "me siento raro hoy"},
            {"role": "assistant", "content": "quieres contarme mas?"},
            {"role": "user", "content": "ando preocupado"},
        ]
        self.assertEqual(build_search_query("busca", history), "")

    def test_search_filters_invalid_and_duplicate_urls(self):
        fake_results = [
            {"title": "Official Album", "href": "https://music.example/Album", "body": "Seven songs."},
            {"title": "Bad scheme", "href": "javascript:alert(1)", "body": "do not trust"},
            {"title": "Duplicate", "href": "https://music.example/Album", "body": "duplicate"},
            {"title": "Second source", "href": "https://label.example/ye", "body": "Track list."},
        ]
        with patch("web_search.DDGS") as ddgs_class:
            ddgs_class.return_value.text.return_value = fake_results
            results = search_web("Ye tracklist")
            ddgs_class.assert_called_once_with(timeout=2.5)
            ddgs_class.return_value.text.assert_called_once_with(
                "Ye tracklist",
                region="es-es",
                safesearch="moderate",
                max_results=5,
                backend="google",
            )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["url"], "https://music.example/Album")
        self.assertTrue(all(x["url"].startswith("https://") for x in results))

    def test_google_failure_falls_back_to_brave(self):
        brave_results = [
            {"title": "Backup result", "href": "https://brave.example/search", "body": "Found through fallback."}
        ]
        with patch("web_search.DDGS") as ddgs_class:
            ddgs_class.return_value.text.side_effect = [RuntimeError("Google blocked"), brave_results]
            results = search_web("papu search test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Backup result")
        calls = ddgs_class.return_value.text.call_args_list
        self.assertEqual(calls[0].kwargs["backend"], "google")
        self.assertEqual(calls[1].kwargs["backend"], "brave")

    def test_search_returns_empty_instead_of_raising_when_all_engines_fail(self):
        with patch("web_search.DDGS") as ddgs_class:
            ddgs_class.return_value.text.side_effect = RuntimeError("search unavailable")
            self.assertEqual(search_web("papu search test"), [])
        self.assertEqual(ddgs_class.return_value.text.call_count, 4)

    def test_search_context_includes_source_urls_and_safety_instructions(self):
        context = format_search_context("Ye tracklist", [
            {"title": "Apple Music", "url": "https://music.example/Ye", "snippet": "7 songs."}
        ])
        self.assertIn("https://music.example/Ye", context)
        self.assertIn("no digas que no puedes buscar", context)
        self.assertIn("datos externos no confiables", context)

    def test_no_model_fallback_shows_real_links(self):
        reply = format_search_reply("ye tracklist", [
            {"title": "Apple Music", "url": "https://music.example/Ye", "snippet": "7 songs."}
        ])
        self.assertIn("[Apple Music](https://music.example/Ye)", reply)


if __name__ == "__main__":
    unittest.main()
