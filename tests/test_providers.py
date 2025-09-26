import os
import unittest
from unittest.mock import patch, MagicMock

from src.config.models import ProviderConfig
from src.api.providers import (
    AnthropicProvider,
    OpenAIProvider,
    OpenRouterProvider,
)


class TestProviders(unittest.TestCase):
    def setUp(self):
        self.openai_config = ProviderConfig(
            model="gpt-4o-mini",
            api_url="https://api.openai.com/v1",
            env_key="OPENAI_API_KEY",
        )
        self.openrouter_config = ProviderConfig(
            model="deepseek/deepseek-chat-v3.1:free",
            api_url="https://openrouter.ai/api/v1",
            env_key="OPENROUTER_API_KEY",
        )
        self.anthropic_config = ProviderConfig(
            model="claude-3-5-sonnet-20240620",
            api_url="https://api.anthropic.com/v1",
            env_key="ANTHROPIC_API_KEY",
        )
        self.user_content = "Test user content"
        self.system_prompt = "Test system prompt"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("src.api.providers.openai.HTTPClient")
    def test_openai_provider_success(self, MockHTTPClient):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test commit message"}}]
        }
        mock_instance = MockHTTPClient.return_value
        mock_instance.post.return_value = mock_response

        provider = OpenAIProvider(self.openai_config)
        result = provider.generate_commit_message(self.user_content, self.system_prompt)

        self.assertEqual(result, "Test commit message")
        mock_instance.post.assert_called_once()
        args, kwargs = mock_instance.post.call_args
        self.assertEqual(args[0], "/chat/completions")
        self.assertEqual(kwargs["json"]["messages"][0]["content"], self.system_prompt)
        self.assertEqual(kwargs["json"]["messages"][1]["content"], self.user_content)

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    @patch("src.api.providers.openrouter.HTTPClient")
    def test_openrouter_provider_success(self, MockHTTPClient):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test commit message"}}]
        }
        mock_instance = MockHTTPClient.return_value
        mock_instance.post.return_value = mock_response

        provider = OpenRouterProvider(self.openrouter_config)
        result = provider.generate_commit_message(self.user_content, self.system_prompt)

        self.assertEqual(result, "Test commit message")
        mock_instance.post.assert_called_once()
        args, kwargs = mock_instance.post.call_args
        self.assertEqual(args[0], "/chat/completions")
        self.assertIn("HTTP-Referer", kwargs["headers"])

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    @patch("src.api.providers.anthropic.HTTPClient")
    def test_anthropic_provider_success(self, MockHTTPClient):
        mock_response = MagicMock()
        mock_response.json.return_value = {"content": [{"text": "Test commit message"}]}
        mock_instance = MockHTTPClient.return_value
        mock_instance.post.return_value = mock_response

        provider = AnthropicProvider(self.anthropic_config)
        result = provider.generate_commit_message(self.user_content, self.system_prompt)

        self.assertEqual(result, "Test commit message")
        mock_instance.post.assert_called_once()
        args, kwargs = mock_instance.post.call_args
        self.assertEqual(args[0], "/messages")
        self.assertEqual(kwargs["json"]["system"], self.system_prompt)
        self.assertEqual(kwargs["json"]["messages"][0]["content"], self.user_content)
        self.assertEqual(kwargs["headers"]["anthropic-version"], "2023-06-01")

    def test_provider_key_missing(self):
        with patch.dict(os.environ, clear=True):
            with self.assertRaises(ValueError):
                OpenAIProvider(self.openai_config)
            with self.assertRaises(ValueError):
                OpenRouterProvider(self.openrouter_config)
            with self.assertRaises(ValueError):
                AnthropicProvider(self.anthropic_config)


if __name__ == "__main__":
    unittest.main()
