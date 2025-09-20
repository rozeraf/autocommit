"""
OpenRouter API client for Git Auto Commit

Copyright (C) 2025 rozeraf
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import json
import logging
import os
from typing import Optional

from .client import HTTPClient
from ..models import ModelInfo, CommitMessage
from ..config import get_config

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = """Your task is to generate a commit message based on the provided diff, following the Conventional Commits specification.

RULES:
1. Output ONLY the commit message text - no explanations, markdown blocks, or extra text.

2. Format: `type(scope): subject`
   - Subject: max 50 chars, imperative mood ("add", not "added")
   - Body: detailed bullet points if needed
   - Footer: BREAKING CHANGE if applicable

3. Scope selection:
   - Use specific module/component names when possible
   - Examples: api, ui, config, models, tests, git_utils
   - Omit scope only for broad changes across multiple areas

4. Types (strict priority order):
   - `feat`: New features or capabilities
   - `fix`: Bug fixes and error corrections  
   - `refactor`: Code restructuring without behavior change
   - `perf`: Performance improvements
   - `test`: Test additions or modifications
   - `docs`: Documentation changes
   - `style`: Formatting, whitespace, etc.
   - `build`: Dependencies, build system
   - `ci`: CI/CD configuration
   - `chore`: Maintenance tasks
   - `revert`: Reverting previous commits

5. Body structure (when needed):
   - Use bullet points with hyphens (-)
   - Start each point with action verb
   - Group related changes logically
   - Explain WHY for complex changes

6. Quality checks:
   - Subject must be imperative mood
   - No period at end of subject
   - Body separated by blank line
   - Each bullet point is a complete thought"""


class OpenRouterClient:
    """OpenRouter API client for generating commit messages"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            api_url: OpenRouter API URL (defaults to config or OPENROUTER_API_URL env var)
            model: Model to use (defaults to config or OPENROUTER_MODEL env var)
        """
        config = get_config()

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.api_url = (
            api_url
            or config.ai.api_url
            or os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
        )
        self.model = (
            model
            or config.ai.model
            or os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        )

        # Extract base URL from the full API URL
        if "/chat/completions" in self.api_url:
            base_url = self.api_url.replace("/chat/completions", "")
        else:
            base_url = self.api_url

        self.http_client = HTTPClient(base_url=base_url)

        if not self.api_key:
            logger.error("Error: OPENROUTER_API_KEY is not set")
            raise ValueError("OPENROUTER_API_KEY is required")

    def get_headers(self) -> dict:
        """Get standard headers for OpenRouter API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/rozeraf/git-auto-commit",
            "X-Title": "Git Auto Commit",
        }

    def get_model_info(self, model_name: Optional[str] = None) -> Optional[ModelInfo]:
        """Get model information from OpenRouter API"""
        model_name = model_name or self.model
        logger.debug(f"Getting model information for {model_name}...")

        try:
            # Use the correct models endpoint URL
            response = self.http_client.get("/models", timeout=15)
            response.raise_for_status()

            data = response.json()
            models_data = data.get("data", [])

            for model in models_data:
                if model.get("id") == model_name:
                    logger.debug(f"Model information for {model_name} received.")
                    return ModelInfo.from_dict(model)

            logger.warning(f"Model '{model_name}' not found.")
            return None

        except Exception as e:
            logger.error(f"Error requesting model information: {e}")
            return None

    def generate_commit_message(
        self, diff: str, model_info: Optional[ModelInfo] = None
    ) -> Optional[CommitMessage]:
        """Generate a commit message via the OpenRouter API"""
        if self.api_key:
            logger.debug("Using API key.")
        logger.debug(f"URL: {self.api_url}")
        logger.debug(f"Model: {self.model}")

        context_length = None
        if model_info and model_info.context_length:
            context_length = model_info.context_length
            logger.debug(f"Model context length: {context_length} tokens")
        else:
            logger.debug("Could not determine context length, using default values.")

        # Import here to avoid circular imports
        from ..parsers import DiffParser

        diff_parser = DiffParser()
        smart_diff_result = diff_parser.parse_diff(diff, context_length)
        smart_diff = smart_diff_result.content

        logger.debug(f"Smart diff length: {len(smart_diff)} characters")
        logger.debug(f"Smart diff preview (first 200 chars): {smart_diff[:200]}")

        config = get_config()

        # Get the prompt from config, with a fallback to the default
        system_prompt = (config.ai.prompts or {}).get(
            "openrouter", DEFAULT_SYSTEM_PROMPT
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": f"Create a commit message for these changes:\n{smart_diff}",
                },
            ],
            "max_tokens": config.ai.max_tokens,
            "temperature": config.ai.temperature,
        }

        try:
            logger.debug("Generating commit message...")
            logger.debug("Sending request to API...")

            response = self.http_client.post(
                "/chat/completions",
                json=payload,
                headers=self.get_headers(),
                timeout=config.ai.timeout,
            )

            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()

            response_text = response.text.strip()
            if not response_text:
                logger.error("Empty response from API")
                return None

            logger.debug(f"Received response ({len(response_text)} characters)")

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.debug(f"First 200 characters of response: {response_text[:200]}")
                return None

            if "choices" not in data or len(data["choices"]) == 0:
                logger.error("Invalid response format from API")
                logger.debug(f"Response data: {data}")
                return None

            if "message" not in data["choices"][0]:
                logger.error("Invalid response format from API")
                logger.debug(f"Missing message field: {data['choices'][0]}")
                return None

            ai_response = data["choices"][0]["message"]["content"].strip()
            logger.debug(f"AI Response:\n{ai_response}")

            # Use the new commit parser
            from ..parsers import CommitParser

            parser = CommitParser()
            parsed_commit = parser.parse_ai_response(ai_response)

            # Log warnings if any
            if parsed_commit.warnings:
                for warning in parsed_commit.warnings:
                    logger.warning(f"Commit parsing warning: {warning}")

            return CommitMessage(
                subject=parsed_commit.subject, description=parsed_commit.description
            )

        except Exception as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"Error details: {error_data}")
                except json.JSONDecodeError:
                    logger.error(f"Response body: {e.response.text}")
            return None

    def test_api_key(self) -> bool:
        """Test if the OpenRouter API is reachable (TCP check only, no API calls)"""
        logger.info("Testing API connectivity...")
        logger.debug(f"URL: {self.api_url}")
        logger.debug(f"Model: {self.model}")

        # Import here to avoid circular imports
        from .tcp_check import check_openrouter_connectivity, parse_url_for_tcp_check

        try:
            # First check if we can reach OpenRouter at all
            if not check_openrouter_connectivity():
                logger.error("Cannot reach OpenRouter API server")
                return False

            # Parse the API URL to get host and port
            host, port = parse_url_for_tcp_check(self.api_url)
            logger.debug(f"Checking connectivity to {host}:{port}")

            # Additional check for the specific host if different
            if host != "openrouter.ai":
                from .tcp_check import check_tcp_connection

                if not check_tcp_connection(host, port, timeout=5.0):
                    logger.error(f"Cannot reach {host}:{port}")
                    return False

            logger.info("API server is reachable!")
            logger.info("Note: This only checks connectivity, not API key validity")
            return True

        except Exception as e:
            logger.error(f"Problem with API connectivity: {e}")
            return False

    def close(self):
        """Close the HTTP client"""
        self.http_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
