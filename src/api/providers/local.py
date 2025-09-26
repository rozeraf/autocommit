"""
Local AI Provider (Placeholder)
"""

from typing import List, Optional

from .base import BaseAIProvider
from ...models.api import ModelInfo


class LocalProvider(BaseAIProvider):
    """AI provider for Local Models (Not implemented)."""

    def __init__(self):
        raise NotImplementedError("Local provider is not yet implemented.")

    def generate_commit_message(
        self, user_content: str, system_prompt: str
    ) -> Optional[str]:
        raise NotImplementedError

    def test_connectivity(self) -> bool:
        raise NotImplementedError

    def get_model_info(self) -> Optional[ModelInfo]:
        raise NotImplementedError

    def get_required_env_vars(self) -> List[str]:
        return []
