import unittest
from unittest.mock import patch

from src.config.loader import get_config
from src.api.manager import AIProviderManager
from src.api.providers import OpenAIProvider, OpenRouterProvider


class TestAIProviderManager(unittest.TestCase):
    def setUp(self):
        # Load the actual config to test with
        self.config = get_config()
        # Ensure we have a base provider set for tests
        self.config.ai.base_provider = "openrouter"

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test_key"})
    def test_get_base_provider(self):
        manager = AIProviderManager(self.config)
        provider = manager.get_base_provider()
        self.assertIsInstance(provider, OpenRouterProvider)

    @patch.dict(
        "os.environ",
        {"OPENROUTER_API_KEY": "test_key", "OPENAI_API_KEY": "test_key"},
    )
    def test_get_provider_for_context_fallback(self):
        # Test that it falls back to base_provider when no context rules match
        manager = AIProviderManager(self.config)
        provider = manager.get_provider_for_context("diff")
        self.assertIsInstance(provider, OpenRouterProvider)

    @patch.dict(
        "os.environ",
        {
            "OPENROUTER_API_KEY": "test_key",
            "OPENAI_API_KEY": "test_key",
            "ANTHROPIC_API_KEY": "test_key",
        },
    )
    def test_test_all_providers(self):
        manager = AIProviderManager(self.config)
        # Mock the test_connectivity method for each provider instance
        with (
            patch.object(
                OpenRouterProvider,
                "test_connectivity",
                return_value=True,
            ),
            patch.object(OpenAIProvider, "test_connectivity", return_value=False),
        ):
            # We only have openrouter and openai configured by default in config.toml
            # Anthropic is not in the default config so it won't be tested
            results = manager.test_all_providers()

            self.assertTrue(results["openrouter"])
            self.assertFalse(results["openai"])
            self.assertIn("anthropic", results)  # It should be tested now


if __name__ == "__main__":
    unittest.main()
