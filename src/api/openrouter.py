"""
OpenRouter AI Provider
"""

import os
import logging
from typing import List, Optional

from src.api.base import BaseAIProvider
from src.api.client import HTTPClient
from src.models.api import ModelInfo
from src.models.commit import CommitMessage
from src.config.loader import get_config

logger = logging.getLogger(__name__)

class OpenRouterProvider(BaseAIProvider):
    """AI provider for OpenRouter."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        config = get_config()
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or config.ai.model
        self.api_url = config.ai.api_url or "https://openrouter.ai/api/v1"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")

        self.http_client = HTTPClient(base_url=self.api_url)

    def get_required_env_vars(self) -> List[str]:
        return ["OPENROUTER_API_KEY"]

    def get_model_info(self) -> Optional[ModelInfo]:
        """Get model information from OpenRouter API"""
        logger.debug(f"Getting model information for {self.model}...")
        try:
            response = self.http_client.get("/models", timeout=15)
            response.raise_for_status()
            data = response.json()
            for model_data in data.get("data", []):
                if model_data.get("id") == self.model:
                    return ModelInfo.from_dict(model_data)
            logger.warning(f"Model '{self.model}' not found on OpenRouter.")
            return None
        except Exception as e:
            logger.error(f"Error requesting model information: {e}")
            return None

    def generate_commit_message(self, diff: str, context: str) -> Optional[str]:
        """Generate a commit message using OpenRouter API."""
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
            "HTTP-Referer": "https://github.com/rozeraf/git-auto-commit",
            "X-Title": "Git Auto Commit",
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
        """Test connectivity to the OpenRouter API."""
        from src.api.tcp_check import check_tcp_connection, parse_url_for_tcp_check
        host, port = parse_url_for_tcp_check(self.api_url)
        return check_tcp_connection(host, port)