from typing import List, Dict, Type
from src.api.base import BaseAIProvider
from src.api.openrouter import OpenRouterProvider
from src.api.openai import OpenAIProvider

# Placeholder for other providers
# from src.api.anthropic import AnthropicProvider
# from src.api.local import LocalProvider


class ProviderFactory:
    """Factory for creating AI providers."""

    _providers: Dict[str, Type[BaseAIProvider]] = {
        "openrouter": OpenRouterProvider,
        "openai": OpenAIProvider,
        # "anthropic": AnthropicProvider,
        # "local": LocalProvider,
    }

    @staticmethod
    def create_provider(provider_name: str, config: dict) -> BaseAIProvider:
        """Creates a provider instance."""
        if provider_name not in ProviderFactory._providers:
            raise ValueError(f"Provider '{provider_name}' is not supported.")

        provider_class = ProviderFactory._providers[provider_name]
        # Here we would pass provider-specific config to the constructor
        return provider_class()

    @staticmethod
    def get_available_providers() -> List[str]:
        """Returns a list of available providers."""
        return list(ProviderFactory._providers.keys())

    @staticmethod
    def validate_provider_config(provider_name: str, config: dict) -> bool:
        """Validates the configuration for a given provider."""
        if provider_name not in ProviderFactory._providers:
            return False

        provider_class = ProviderFactory._providers[provider_name]
        required_vars = provider_class().get_required_env_vars()
        # Basic validation: check if env vars are present in config or environment
        # This logic will be more complex later
        return True
