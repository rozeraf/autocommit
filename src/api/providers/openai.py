"""
OpenAI AI Provider
"""

import os
import logging
from typing import List, Optional

from .base import BaseAIProvider
from ..client import HTTPClient
from ...config.models import ProviderConfig
from ...models.api import ModelInfo

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """AI provider for OpenAI."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_key = os.getenv(config.env_key) if config.env_key else None
        self.model = config.model
        self.api_url = config.api_url

        if not self.api_key:
            raise ValueError(f"{config.env_key} is not set.")

        self.http_client = HTTPClient(base_url=self.api_url)

    def get_required_env_vars(self) -> List[str]:
        return ["OPENAI_API_KEY"]

    def get_model_info(self) -> Optional[ModelInfo]:
        # The OpenAI API does not have a single endpoint to get all model details
        # like OpenRouter. We can get a list of models, but details are sparse.
        # For now, we'll return a hardcoded ModelInfo.
        logger.debug("Returning hardcoded model info for OpenAI.")
        return ModelInfo(
            id=self.model,
            name=self.model,
            context_length=128000,  # Common for gpt-4o-mini
        )

    def generate_commit_message(
        self, user_content: str, system_prompt: str
    ) -> Optional[str]:
        """Generate a commit message using OpenAI API."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self.http_client.post(
                "/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None

    def test_connectivity(self) -> bool:
        """Test connectivity to the OpenAI API."""
        from ..tcp_check import check_tcp_connection, parse_url_for_tcp_check

        host, port = parse_url_for_tcp_check(self.api_url)
        return check_tcp_connection(host, port)
