"""
Anthropic AI Provider
"""

import os
import logging
from typing import List, Optional

from src.api.base import BaseAIProvider
from src.api.client import HTTPClient
from src.config.models import ProviderConfig
from src.models.api import ModelInfo

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseAIProvider):
    """AI provider for Anthropic."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_key = os.getenv(config.env_key) if config.env_key else None
        self.model = config.model
        self.api_url = config.api_url

        if not self.api_key:
            raise ValueError(f"{config.env_key} is not set.")

        self.http_client = HTTPClient(base_url=self.api_url)

    def get_required_env_vars(self) -> List[str]:
        return ["ANTHROPIC_API_KEY"]

    def get_model_info(self) -> Optional[ModelInfo]:
        """Provide hardcoded model info for Anthropic models."""
        logger.debug("Returning hardcoded model info for Anthropic.")
        # Anthropic doesn't have a public-facing models endpoint like OpenRouter
        # We'll provide a sensible default for Claude 3.5 Sonnet
        return ModelInfo(
            id=self.model,
            name=self.model,
            context_length=200000,  # 200K context window for Claude 3.5 Sonnet
        )

    def generate_commit_message(
        self, user_content: str, system_prompt: str
    ) -> Optional[str]:
        """Generate a commit message using Anthropic API."""
        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        try:
            response = self.http_client.post(
                "/messages",
                json=payload,
                headers=headers,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"].strip()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None

    def test_connectivity(self) -> bool:
        """Test connectivity to the Anthropic API."""
        from src.api.tcp_check import check_tcp_connection, parse_url_for_tcp_check

        host, port = parse_url_for_tcp_check(self.api_url)
        return check_tcp_connection(host, port)
