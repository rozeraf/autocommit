"""
Commit message generator using a specified AI provider.
"""

import logging
from typing import Optional

from src.api.base import BaseAIProvider
from src.models.commit import CommitMessage
from src.parsers.diff_parser import DiffParser
from src.parsers.commit_parser import CommitParser
from src.config.loader import get_config

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


class CommitGenerator:
    """Generates commit messages using a provider."""

    def __init__(self, provider: BaseAIProvider):
        self.provider = provider
        self.config = get_config()

    def generate(
        self, diff: str, context: Optional[str] = None
    ) -> Optional[CommitMessage]:
        """
        Generates a commit message.

        Args:
            diff: The git diff to generate the message from.
            context: Optional context to include in the prompt.

        Returns:
            A CommitMessage object or None if generation fails.
        """
        logger.debug("Starting commit message generation...")

        model_info = self.provider.get_model_info()
        context_length = None
        if model_info and model_info.context_length:
            context_length = model_info.context_length
            logger.debug(f"Model context length: {context_length} tokens")
        else:
            logger.debug("Could not determine context length, using default values.")

        diff_parser = DiffParser()
        smart_diff_result = diff_parser.parse_diff(diff, context_length)
        smart_diff = smart_diff_result.content

        logger.debug(f"Smart diff length: {len(smart_diff)} characters")

        # This logic will be expanded when provider-specific prompts are added
        system_prompt = DEFAULT_SYSTEM_PROMPT

        user_content = f"""Create a commit message for these changes:
{smart_diff}"""
        if context:
            user_content = f"""An important context to consider: {context}

{user_content}"""

        # The actual call to the provider is now much simpler
        ai_response = self.provider.generate_commit_message(user_content, system_prompt)

        if not ai_response:
            logger.error("AI provider returned an empty response.")
            return None

        logger.debug(
            f"""AI Response:
{ai_response}"""
        )

        parser = CommitParser()
        parsed_commit = parser.parse_ai_response(ai_response)

        if parsed_commit.warnings:
            for warning in parsed_commit.warnings:
                logger.warning(f"Commit parsing warning: {warning}")

        return CommitMessage(
            subject=parsed_commit.subject, description=parsed_commit.description
        )
