"""
OpenRouter API client for generating commit messages

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

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)


def _get_session() -> requests.Session:
    """Creates a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_model_info(model_name: str) -> dict | None:
    """Gets model information from the OpenRouter API"""
    api_url = "https://openrouter.ai/api/v1/models"
    logger.debug("Getting model information...")
    try:
        session = _get_session()
        response = session.get(api_url, timeout=15)
        response.raise_for_status()

        data = response.json()
        models_data = data.get("data", [])

        for model in models_data:
            if model.get("id") == model_name:
                logger.debug(f"Model information for {model_name} received.")
                return model

        logger.warning(f"Model '{model_name}' not found.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error requesting model information: {e}")
        return None


def parse_ai_response(full_message: str) -> tuple[str, str | None]:
    """Splits the full commit message into a subject and description."""
    lines = full_message.strip().split("\n", 1)
    commit_msg = lines[0].strip()
    description = None
    if len(lines) > 1 and lines[1].strip():
        description = lines[1].strip()
    return commit_msg, description


def generate_commit_message(diff: str, model_info: dict | None) -> tuple[str, str | None] | None:
    """Generates a commit message via the OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    if not api_key:
        logger.error("Error: OPENROUTER_API_KEY is not set in the .env file.")
        logger.error("Create a .env file with OPENROUTER_API_KEY=your_key")
        return None

    logger.debug(f"Using API key: {api_key[:8]}...")
    logger.debug(f"URL: {api_url}")
    logger.debug(f"Model: {model}")

    context_length = None
    if model_info and "context_length" in model_info:
        context_length = int(model_info["context_length"])
        logger.debug(f"Model context length: {context_length} tokens")
    else:
        logger.debug("Could not determine context length, using default values.")

    from . import git_utils
    smart_diff = git_utils.get_smart_diff(diff, context_length)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/rozeraf/git-auto-commit",
        "X-Title": "Git Auto Commit"
    }

    system_prompt = """Your task is to generate a commit message based on the provided diff, following the Conventional Commits specification.

RULES:
1. The output must be ONLY the commit message text, without any extra words or explanations.
2. The message must be in English.
3. The format is: `type(scope): subject`
    - Followed by an optional longer body.
    - Followed by an optional `BREAKING CHANGE:` footer.
4. Use the following types:
    - `feat`: A new feature.
    - `fix`: A bug fix.
    - `docs`: Documentation only changes.
    - `style`: Code style changes (formatting, etc).
    - `refactor`: A code change that neither fixes a bug nor adds a feature.
    - `perf`: A code change that improves performance.
    - `test`: Adding missing tests or correcting existing tests.
    - `build`: Changes that affect the build system or external dependencies.
    - `ci`: Changes to CI configuration files and scripts.
    - `chore`: Other changes that don't modify src or test files.
    - `revert`: Reverts a previous commit.
5. The body, if present, should have a header, a list of changes starting with `-`, and an optional footer."""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Create a commit message for these changes:\n{smart_diff}"
            }
        ],
        "max_tokens": 250,
        "temperature": 0.4
    }

    try:
        logger.debug("Generating commit message...")
        logger.debug("Sending request to API...")

        session = _get_session()
        response = session.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=45
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

        return parse_ai_response(ai_response)
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if e.response is not None:
            try:
                error_data = e.response.json()
                logger.error(f"Error details: {error_data}")
            except json.JSONDecodeError:
                logger.error(f"Response body: {e.response.text}")
        return None
    except KeyboardInterrupt:
        logger.info("\nRequest cancelled by user")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_api_key() -> bool:
    """Tests if the OpenRouter API key is valid and working"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    if not api_key:
        logger.error("Error: OPENROUTER_API_KEY is not set in the .env file.")
        return False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }

    try:
        logger.info("Testing API key...")
        logger.debug(f"URL: {api_url}")
        logger.debug(f"Model: {model}")

        session = _get_session()
        response = session.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        logger.debug(f"Status: {response.status_code}")
        logger.info("API key is working!")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Problem with API key or connection: {e}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False
