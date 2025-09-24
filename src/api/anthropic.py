"""
Anthropic AI Provider (Placeholder)
"""

import os
from typing import List, Optional

from src.api.base import BaseAIProvider
from src.models.api import ModelInfo
from src.models.commit import CommitMessage

class AnthropicProvider(BaseAIProvider):
    """AI provider for Anthropic (Not implemented)."""

    def __init__(self):
        raise NotImplementedError("Anthropic provider is not yet implemented.")

    def generate_commit_message(self, diff: str, context: str) -> Optional[CommitMessage]:
        raise NotImplementedError

    def test_connectivity(self) -> bool:
        raise NotImplementedError

    def get_model_info(self) -> Optional[ModelInfo]:
        raise NotImplementedError

    def get_required_env_vars(self) -> List[str]:
        return ["ANTHROPIC_API_KEY"]
