"""
Context detector for Git Auto Commit
"""

import logging
from typing import List

from ..models.diff import DiffStats

logger = logging.getLogger(__name__)


class ContextDetector:
    """Detects context from git diff and stats"""

    def __init__(self, wip_keywords: List[str]):
        """Initialize the detector with configurable keywords."""
        self.wip_keywords = [kw.upper() for kw in wip_keywords]

    def detect(self, diff: str, stats: DiffStats) -> List[str]:
        """
        Detect context hints from diff content and stats.

        Args:
            diff: The raw diff content.
            stats: The statistics analyzed from the diff.

        Returns:
            A list of context hint strings.
        """
        hints = []

        # 1. Detect from keywords in diff content
        for line in diff.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                content_upper = line[1:].upper()
                for keyword in self.wip_keywords:
                    if keyword in content_upper:
                        hints.append(f"wip_keyword_{keyword.lower()}")
                        break  # Move to next line once a keyword is found

        # 2. Detect from DiffStats
        if stats.has_tests:
            hints.append("tests_modified")

        if stats.has_docs:
            hints.append("docs_modified")

        if stats.has_config:
            hints.append("config_modified")

        if stats.has_dependencies:
            hints.append("deps_modified")

        # 3. Detect from add/remove ratio (simple heuristic)
        if stats.lines_added > 100 and stats.lines_removed < 20:
            hints.append("large_feature")

        if stats.lines_removed > 100 and stats.lines_added < 20:
            hints.append("large_refactor_or_removal")

        # Remove duplicates and return
        return sorted(list(set(hints)))
