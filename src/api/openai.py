"""
OpenAI AI Provider
"""

import os
import logging
from typing import List, Optional

from src.api.base import BaseAIProvider
from src.api.client import HTTPClient
from src.models.api import ModelInfo
from src.config.loader import get_config

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """AI provider for OpenAI."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        config = get_config()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        # Find a way to get the model from the config for this provider
        self.model = model or "gpt-4o-mini"
        self.api_url = "https://api.openai.com/v1"

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set.")

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

    def generate_commit_message(self, diff: str, context: str) -> Optional[str]:
        """Generate a commit message using OpenAI API."""
        config = get_config()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": context},
                {"role": "user", "content": diff},
            ],
            "max_tokens": config.ai.max_tokens,
            "temperature": config.ai.temperature,
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
                timeout=config.ai.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None

    def test_connectivity(self) -> bool:
        """Test connectivity to the OpenAI API."""
        from src.api.tcp_check import check_tcp_connection, parse_url_for_tcp_check

        host, port = parse_url_for_tcp_check(self.api_url)
        return check_tcp_connection(host, port)
