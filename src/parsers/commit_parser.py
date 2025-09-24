"""
Commit message parser for Git Auto Commit

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

import re
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

from ..config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ParsedCommit:
    """Parsed commit message with validation results"""

    subject: str
    description: Optional[str] = None
    is_valid: bool = True
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class CommitParser:
    """Parser for AI-generated commit messages with validation"""

    # Conventional commit types
    CONVENTIONAL_TYPES = {
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "build",
        "ci",
        "chore",
        "revert",
    }

    # Unwanted patterns to clean from AI responses
    UNWANTED_PATTERNS = [
        r"Looking at the diff, this represents.*?(?=\n|$)",
        r"^This is a [a-zA-Z]+.*?(?=\n|$)",  # More specific - "This is a [word]" at start
        r"Based on the changes.*?(?=\n|$)",
        r"The changes include.*?(?=\n|$)",
        r"### Analysis.*?(?=\n\n)",
        r"## Summary.*?(?=\n\n)",
        r"- \*\*Core project files\*\*.*?(?=\n\n|\Z)",
        r"- \*\*Configuration files\*\*.*?(?=\n\n|\Z)",
        r"- \*\*Documentation\*\*.*?(?=\n\n|\Z)",
        r"- \*\*Dependencies\*\*.*?(?=\n\n|\Z)",
        r"graph TD.*?(?=\n\n|\Z)",
        r"\n{3,}",  # Only remove 3+ consecutive newlines
    ]

    def __init__(self, max_subject_length: Optional[int] = None):
        """
        Initialize commit parser

        Args:
            max_subject_length: Maximum length for subject line (defaults to config)
        """
        config = get_config()
        self.max_subject_length = max_subject_length or config.format.max_subject_length

    def parse_ai_response(self, full_message: str) -> ParsedCommit:
        """
        Parse AI response into structured commit message with validation

        Args:
            full_message: Raw AI response

        Returns:
            ParsedCommit with parsed content and validation results
        """
        # Clean up the message
        cleaned_message = self._clean_message(full_message)

        # Extract subject and description
        subject, description = self._extract_subject_and_description(cleaned_message)

        # Validate the parsed commit
        is_valid, warnings = self._validate_commit(subject, description)

        return ParsedCommit(
            subject=subject,
            description=description,
            is_valid=is_valid,
            warnings=warnings,
        )

    def _clean_message(self, message: str) -> str:
        """Clean up common markdown patterns and AI artifacts"""
        cleaned_message = message.strip()

        # Remove mermaid code blocks more thoroughly
        while "```mermaid" in cleaned_message:
            start_idx = cleaned_message.find("```mermaid")
            if start_idx == -1:
                break
            end_idx = cleaned_message.find("```", start_idx + 3)
            if end_idx != -1:
                cleaned_message = (
                    cleaned_message[:start_idx].strip()
                    + cleaned_message[end_idx + 3 :].strip()
                )
            else:
                # If no closing ```, remove from start_idx to end
                cleaned_message = cleaned_message[:start_idx].strip()

        # Remove other code blocks more robustly
        while "```" in cleaned_message:
            start_idx = cleaned_message.find("```")
            if start_idx == -1:
                break
            end_idx = cleaned_message.find("```", start_idx + 3)
            if end_idx != -1:
                cleaned_message = (
                    cleaned_message[:start_idx].strip()
                    + cleaned_message[end_idx + 3 :].strip()
                )
            else:
                cleaned_message = cleaned_message[:start_idx].strip()

        # Remove unwanted patterns
        for pattern in self.UNWANTED_PATTERNS:
            cleaned_message = re.sub(
                pattern, "", cleaned_message, flags=re.IGNORECASE | re.DOTALL
            )
            cleaned_message = re.sub(
                r"\n\s*\n", "\n\n", cleaned_message
            )  # Clean up extra newlines

        # Remove markdown formatting
        cleaned_message = re.sub(
            r"\*\*(.*?)\*\*", r"\1", cleaned_message
        )  # Remove **bold**
        cleaned_message = re.sub(
            r"\*(.*?)\*", r"\1", cleaned_message
        )  # Remove *italic*
        cleaned_message = re.sub(r"`(.*?)`", r"\1", cleaned_message)  # Remove `code`
        cleaned_message = re.sub(r"#{1,6}\s*", "", cleaned_message)  # Remove headers
        cleaned_message = re.sub(
            r"[-*]\s*\*?\*?[A-Za-z ]+\*?\*?:", "", cleaned_message
        )  # Remove bullet points with bold

        return cleaned_message.strip()

    def _extract_subject_and_description(self, cleaned_message: str) -> Tuple[str, str]:
        """Extract subject and description from cleaned message"""
        lines = cleaned_message.split("\n")

        start_index = 0
        for i, line in enumerate(lines):
            if re.match(r"^[a-z]+(\([^)]+\))?:", line.strip()):
                start_index = i
                break

        relevant_message = "\n".join(lines[start_index:])

        parts = relevant_message.split("\n\n", 1)
        subject = parts[0].replace("\n", " ").strip()
        description = parts[1].strip() if len(parts) > 1 else None

        # The old logic for making the subject concise might still be useful
        if len(subject) > self.max_subject_length and ":" in subject:
            subject, extra_lines = self._make_concise(subject, description or "")
            description = extra_lines if extra_lines else None

        return subject, description

    def _split_on_dash(self, text: str) -> Tuple[str, str]:
        """Split text on first dash that follows the commit type and scope"""
        # Find the first colon (after type and scope)
        colon_idx = text.find(":")
        if colon_idx == -1:
            return text, None

        # Look for dash after the colon
        after_colon = text[colon_idx + 1 :]
        dash_idx = after_colon.find("-")
        if dash_idx == -1:
            return text, None  # No dash found, return full text

        # Split at the dash
        subject = text[: colon_idx + 1 + dash_idx].strip()
        details = text[colon_idx + 1 + dash_idx + 1 :].strip()
        return subject, details

    def _make_concise(self, commit_msg: str, extra_lines: str) -> Tuple[str, str]:
        """Make commit message more concise by moving details to description"""
        # Keep only up to the first logical break after type(scope):
        parts = commit_msg.split(":", 1)
        header = parts[0] + ":"  # type(scope):
        content = parts[1].strip()

        # Find a good break point
        break_points = [". ", ", ", " - ", " and "]
        for point in break_points:
            idx = content.find(point)
            if idx > 0 and idx < 50:  # Found a break point in reasonable range
                commit_msg = header + " " + content[:idx]
                remaining = content[idx + len(point) :].strip()
                if remaining:
                    extra_lines = (
                        (remaining + "\n" + extra_lines) if extra_lines else remaining
                    )
                break

        return commit_msg, extra_lines

    def _validate_commit(
        self, subject: str, description: Optional[str]
    ) -> Tuple[bool, list[str]]:
        """Validate parsed commit message"""
        warnings = []
        is_valid = True

        # Check if subject is empty
        if not subject.strip():
            warnings.append("Subject line is empty")
            is_valid = False
            return is_valid, warnings

        # Check subject length
        if len(subject) > self.max_subject_length:
            warnings.append(
                f"Subject line is too long ({len(subject)} chars, max {self.max_subject_length})"
            )
            is_valid = False

        # Check if it follows conventional commit format
        if not self._is_conventional_commit(subject):
            warnings.append("Subject doesn't follow conventional commit format")
            is_valid = False

        # Check for required description for certain types
        if self._requires_description(subject) and not description:
            warnings.append("Description is recommended for this type of commit")

        return is_valid, warnings

    def _is_conventional_commit(self, subject: str) -> bool:
        """Check if subject follows conventional commit format"""
        # Pattern: type(scope): description
        pattern = r"^([a-z]+)(\([^)]+\))?:\s+.+"
        if not re.match(pattern, subject):
            return False

        # Extract type
        type_match = re.match(r"^([a-z]+)", subject)
        if not type_match:
            return False

        commit_type = type_match.group(1)
        return commit_type in self.CONVENTIONAL_TYPES

    def _requires_description(self, subject: str) -> bool:
        """Check if commit type typically requires a description"""
        # Extract type
        type_match = re.match(r"^([a-z]+)", subject)
        if not type_match:
            return False

        commit_type = type_match.group(1)
        # feat and fix often benefit from descriptions
        return commit_type in {"feat", "fix", "refactor", "perf"}

    def format_for_git(self, parsed_commit: ParsedCommit) -> str:
        """Format parsed commit for git command"""
        if parsed_commit.description:
            return f"{parsed_commit.subject}\n\n{parsed_commit.description}"
        return parsed_commit.subject
