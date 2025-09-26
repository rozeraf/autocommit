from abc import ABC, abstractmethod
from typing import List
from ...models.api import ModelInfo


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate_commit_message(self, user_content: str, system_prompt: str) -> str:
        """Generates a commit message for the given diff and context."""
        raise NotImplementedError

    @abstractmethod
    def test_connectivity(self) -> bool:
        """Tests the connectivity to the AI provider's API."""
        raise NotImplementedError

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Gets information about the model."""
        raise NotImplementedError

    @abstractmethod
    def get_required_env_vars(self) -> List[str]:
        """Gets the list of required environment variables for the provider."""
        raise NotImplementedError
