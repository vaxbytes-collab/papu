import os
import unittest
from unittest.mock import patch

import groq_config


class GroqConfigTests(unittest.TestCase):
    def test_default_is_current_supported_model(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(groq_config.get_groq_model("GROQ_CHAT_MODEL"), "openai/gpt-oss-20b")

    def test_old_eight_billion_model_is_migrated(self):
        with patch.dict(os.environ, {"GROQ_CHAT_MODEL": "llama-3.1-8b-instant"}):
            self.assertEqual(groq_config.get_groq_model("GROQ_CHAT_MODEL"), "openai/gpt-oss-20b")

    def test_old_seventy_billion_model_is_migrated(self):
        with patch.dict(os.environ, {"GROQ_MODERATION_MODEL": "llama-3.3-70b-versatile"}):
            self.assertEqual(groq_config.get_groq_model("GROQ_MODERATION_MODEL"), "openai/gpt-oss-120b")

    def test_custom_nonretired_model_is_preserved(self):
        with patch.dict(os.environ, {"GROQ_CHAT_MODEL": "my/custom-model"}):
            self.assertEqual(groq_config.get_groq_model("GROQ_CHAT_MODEL"), "my/custom-model")


if __name__ == "__main__":
    unittest.main()
