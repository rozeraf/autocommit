import unittest
from unittest.mock import patch

from src.api.factory import ProviderFactory
from src.config.models import AIConfig, ProviderConfig
from src.api.providers import (
    AnthropicProvider,
    OpenAIProvider,
    OpenRouterProvider,
)


class TestProviderFactory(unittest.TestCase):
    def setUp(self):
        self.ai_config = AIConfig(
            providers={
                "openai": ProviderConfig(
                    model="gpt-4o-mini",
                    api_url="https://api.openai.com/v1",
                    env_key="OPENAI_API_KEY",
                ),
                "openrouter": ProviderConfig(
                    model="deepseek/deepseek-chat-v3.1:free",
                    api_url="https://openrouter.ai/api/v1",
                    env_key="OPENROUTER_API_KEY",
                ),
                "anthropic": ProviderConfig(
                    model="claude-3-5-sonnet-20240620",
                    api_url="https://api.anthropic.com/v1",
                    env_key="ANTHROPIC_API_KEY",
                ),
            }
        )

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test"})
    def test_create_openai_provider(self):
        provider = ProviderFactory.create_provider(
            "openai", self.ai_config.providers["openai"]
        )
        self.assertIsInstance(provider, OpenAIProvider)

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test"})
    def test_create_openrouter_provider(self):
        provider = ProviderFactory.create_provider(
            "openrouter", self.ai_config.providers["openrouter"]
        )
        self.assertIsInstance(provider, OpenRouterProvider)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"})
    def test_create_anthropic_provider(self):
        provider = ProviderFactory.create_provider(
            "anthropic", self.ai_config.providers["anthropic"]
        )
        self.assertIsInstance(provider, AnthropicProvider)

    def test_create_unknown_provider(self):
        with self.assertRaises(ValueError):
            ProviderFactory.create_provider(
                "unknown", ProviderConfig(model="", api_url="")
            )

    def test_get_available_providers(self):
        available = ProviderFactory.get_available_providers()
        self.assertIn("openai", available)
        self.assertIn("openrouter", available)
        self.assertIn("anthropic", available)


if __name__ == "__main__":
    unittest.main()
