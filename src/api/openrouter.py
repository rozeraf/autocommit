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
from typing import Optional, Tuple

from .client import HTTPClient
from .models import ModelInfo, CommitMessage

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """OpenRouter API client for generating commit messages"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 api_url: Optional[str] = None,
                 model: Optional[str] = None):
        """
        Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            api_url: OpenRouter API URL (defaults to OPENROUTER_API_URL env var)
            model: Model to use (defaults to OPENROUTER_MODEL env var)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.api_url = api_url or os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
        self.model = model or os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        
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
            "X-Title": "Git Auto Commit"
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
    
    def generate_commit_message(self, 
                               diff: str, 
                               model_info: Optional[ModelInfo] = None) -> Optional[CommitMessage]:
        """Generate a commit message via the OpenRouter API"""
        logger.debug(f"Using API key: {self.api_key[:8]}...")
        logger.debug(f"URL: {self.api_url}")
        logger.debug(f"Model: {self.model}")
        
        context_length = None
        if model_info and model_info.context_length:
            context_length = model_info.context_length
            logger.debug(f"Model context length: {context_length} tokens")
        else:
            logger.debug("Could not determine context length, using default values.")
        
        # Import here to avoid circular imports
        from .. import git_utils
        smart_diff = git_utils.get_smart_diff(diff, context_length)
        
        system_prompt = """Your task is to generate a commit message based on the provided diff, following the Conventional Commits specification.

RULES:
1. The output must be ONLY the commit message text, without any extra words or explanations.
2. The message must be in English.
3. The format is: `type(scope): subject`
    - Subject line MUST be concise (max 50-70 chars)
    - Followed by an optional longer body for details
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
5. Keep the subject line VERY SHORT and move details to the body:
    Bad:  feat(ui): add new button component with custom styles and hover effects
    Good: feat(ui): add new button component
          
          - Implemented custom styling system
          - Added hover effect animations
          - Updated component documentation
6. The body should be structured with bullet points (-) and clear sections."""

        payload = {
            "model": self.model,
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
            
            response = self.http_client.post(
                "/chat/completions",
                json=payload,
                headers=self.get_headers(),
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
            
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
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
    
    def _parse_ai_response(self, full_message: str) -> CommitMessage:
        """Parse AI response into structured commit message"""
        import re
        
        def split_on_dash(text: str) -> tuple[str, str | None]:
            """Split text on first dash that follows the commit type and scope"""
            # Find the first colon (after type and scope)
            colon_idx = text.find(':')
            if colon_idx == -1:
                return text, None
                
            # Look for dash after the colon
            after_colon = text[colon_idx + 1:]
            dash_idx = after_colon.find('-')
            if dash_idx == -1:
                return text, None  # No dash found, return full text
                
            # Split at the dash
            subject = text[:colon_idx + 1 + dash_idx].strip()
            details = text[colon_idx + 1 + dash_idx + 1:].strip()
            return subject, details
        
        # Clean up common markdown patterns
        cleaned_message = full_message.strip()
        
        # Remove mermaid code blocks more thoroughly
        while '```mermaid' in cleaned_message:
            start_idx = cleaned_message.find('```mermaid')
            if start_idx == -1:
                break
            end_idx = cleaned_message.find('```', start_idx + 3)
            if end_idx != -1:
                cleaned_message = cleaned_message[:start_idx].strip() + cleaned_message[end_idx + 3:].strip()
            else:
                # If no closing ```, remove from start_idx to end
                cleaned_message = cleaned_message[:start_idx].strip()
        
        # Remove other code blocks more robustly
        while '```' in cleaned_message:
            start_idx = cleaned_message.find('```')
            if start_idx == -1:
                break
            end_idx = cleaned_message.find('```', start_idx + 3)
            if end_idx != -1:
                cleaned_message = cleaned_message[:start_idx].strip() + cleaned_message[end_idx + 3:].strip()
            else:
                cleaned_message = cleaned_message[:start_idx].strip()
        
        # Remove common AI response patterns more comprehensively
        unwanted_patterns = [
            r'Looking at the diff, this represents.*?(?=\n|$)',
            r'^This is a [a-zA-Z]+.*?(?=\n|$)',  # More specific - "This is a [word]" at start
            r'Based on the changes.*?(?=\n|$)',
            r'The changes include.*?(?=\n|$)',
            r'### Analysis.*?(?=\n\n)',
            r'## Summary.*?(?=\n\n)',
            r'- \*\*Core project files\*\*.*?(?=\n\n|\Z)',
            r'- \*\*Configuration files\*\*.*?(?=\n\n|\Z)',
            r'- \*\*Documentation\*\*.*?(?=\n\n|\Z)',
            r'- \*\*Dependencies\*\*.*?(?=\n\n|\Z)',
            r'graph TD.*?(?=\n\n|\Z)',
            r'\n{3,}',  # Only remove 3+ consecutive newlines
        ]
        
        for pattern in unwanted_patterns:
            cleaned_message = re.sub(pattern, '', cleaned_message, flags=re.IGNORECASE | re.DOTALL)
            cleaned_message = re.sub(r'\n\s*\n', '\n\n', cleaned_message)  # Clean up extra newlines
        
        # Remove extra whitespace and markdown artifacts more aggressively
        cleaned_message = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_message)  # Remove **bold**
        cleaned_message = re.sub(r'\*(.*?)\*', r'\1', cleaned_message)  # Remove *italic*
        cleaned_message = re.sub(r'`(.*?)`', r'\1', cleaned_message)  # Remove `code`
        cleaned_message = re.sub(r'#{1,6}\s*', '', cleaned_message)  # Remove headers
        cleaned_message = re.sub(r'[-*]\s*\*?\*?[A-Za-z ]+\*?\*?:', '', cleaned_message)  # Remove bullet points with bold
        
        # Strip leading/trailing whitespace
        cleaned_message = cleaned_message.strip()
        
        # Try to find the actual commit message if the first line doesn't look like one
        lines = cleaned_message.split('\n')
        commit_line_idx = 0
        
        # Look for a line that looks like a conventional commit (type: or type(scope):)
        for i, line in enumerate(lines):
            line = line.strip()
            if line and re.match(r'^[a-z]+(\([^)]+\))?:', line):
                commit_line_idx = i
                break
        
        # If we found a commit-like line, reconstruct the message from that point
        if commit_line_idx > 0:
            cleaned_message = '\n'.join(lines[commit_line_idx:])
        
        # Now parse the cleaned message
        lines = cleaned_message.split('\n', 1)
        first_line = lines[0].strip() if lines else ""
        extra_lines = lines[1].strip() if len(lines) > 1 else ""
        
        # Process the first line to ensure it's a concise conventional commit
        commit_msg = first_line
        if first_line and ':' in first_line:
            # If the first line contains details after a dash, move them to description
            subject, details = split_on_dash(first_line)
            if details:
                commit_msg = subject
                extra_lines = (details + "\n" + extra_lines) if extra_lines else details
        
        # If the message is still too long, try to make it more concise
        if len(commit_msg) > 70 and ':' in commit_msg:
            # Keep only up to the first logical break after type(scope):
            parts = commit_msg.split(':', 1)
            header = parts[0] + ':'  # type(scope):
            content = parts[1].strip()
            
            # Find a good break point
            break_points = ['. ', ', ', ' - ', ' and ']  # Removed ' with ' as it's too common
            for point in break_points:
                idx = content.find(point)
                if idx > 0 and idx < 50:  # Found a break point in reasonable range
                    commit_msg = header + ' ' + content[:idx]
                    remaining = content[idx + len(point):].strip()
                    if remaining:
                        extra_lines = (remaining + "\n" + extra_lines) if extra_lines else remaining
                    break
        
        description = extra_lines if extra_lines else None
        
        # Clean up description
        if description:
            description = description.strip()
        
        return CommitMessage(subject=commit_msg, description=description)
    
    def close(self):
        """Close the HTTP client"""
        self.http_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
