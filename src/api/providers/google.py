"""
Google AI Provider
"""

import os
import logging
from typing import List, Optional

from google import genai
from google.genai import types

from .base import BaseAIProvider
from ...config.models import ProviderConfig
from ...models.api import ModelInfo

logger = logging.getLogger(__name__)


class GoogleProvider(BaseAIProvider):
    """AI provider for Google Gemini."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.model_name = config.model

        # Determine the environment variable name to look for the API key
        api_key_env_var_name = (
            config.env_key if config.env_key else self.get_required_env_vars()[0]
        )

        # Attempt to retrieve the API key from the environment variable
        self.api_key = os.getenv(api_key_env_var_name)

        # If API key is still not found, raise a clear error.
        if not self.api_key:
            raise ValueError(
                f"API key environment variable '{api_key_env_var_name}' is not set. "
                "Please set this environment variable to your API key."
            )

        self.client = genai.Client(api_key=self.api_key)

    def get_required_env_vars(self) -> List[str]:
        return ["GOOGLE_API_KEY"]

    def get_model_info(self) -> Optional[ModelInfo]:
        # Gemini API provides a list_models method, but for simplicity we return hardcoded info for now.
        logger.debug("Returning hardcoded model info for Google Gemini.")
        return ModelInfo(
            id=self.model_name,
            name=self.model_name,
            context_length=1048576,  # Gemini 1.5 Pro/Flash have 1M+ context
        )

    def generate_commit_message(
        self, user_content: str, system_prompt: str
    ) -> Optional[str]:
        """Generate a commit message using Google Gemini API."""
        try:
            # Using the new google-genai SDK format
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                ),
            )

            if not response or not response.text:
                logger.error("Google Gemini API returned an empty response.")
                return None

            return response.text.strip()
        except Exception as e:
            logger.error(f"Google Gemini API request failed: {e}")
            return None

    def test_connectivity(self) -> bool:
        """Test connectivity to the Google API."""
        try:
            # Use a simple list_models call to verify connectivity and API key
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Google API connectivity test failed: {e}")
            return False
