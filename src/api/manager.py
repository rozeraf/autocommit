"""
AI Provider Manager for Git Auto Commit
"""

import logging
import fnmatch
from typing import Dict

from src.config.models import Config
from src.api.providers import BaseAIProvider
from src.api.factory import ProviderFactory
from src.parsers.diff_parser import DiffParser

logger = logging.getLogger(__name__)


class AIProviderManager:
    """Manages AI provider selection and creation."""

    def __init__(self, config: Config):
        self.config = config
        self._providers: Dict[str, BaseAIProvider] = {}

    def get_base_provider(self) -> BaseAIProvider:
        """Gets the base provider specified in the config."""
        provider_name = self.config.ai.base_provider
        if provider_name not in self._providers:
            provider_config = self.config.ai.providers.get(provider_name)
            if not provider_config:
                raise ValueError(
                    f"Configuration for base provider '{provider_name}' not found."
                )
            self._providers[provider_name] = ProviderFactory.create_provider(
                provider_name, provider_config
            )
        return self._providers[provider_name]

    def get_provider_for_context(self, diff: str) -> BaseAIProvider:
        """Gets a provider based on the context of the diff."""
        if not self.config.ai.context_switching:
            return self.get_base_provider()

        diff_parser = DiffParser()
        diff_stats = diff_parser._analyze_diff_stats(diff)
        total_lines = diff_stats.lines_added + diff_stats.lines_removed

        for rule_name, rule in self.config.ai.context_rules.items():
            provider_name = rule.get("provider")
            if not provider_name:
                continue

            # Check threshold
            if "threshold_lines" in rule and total_lines >= rule["threshold_lines"]:
                logger.debug(f"Context rule '{rule_name}' matched by line count.")
                return self._get_or_create_provider(provider_name)

            # Check file patterns
            if "file_patterns" in rule:
                filenames = [
                    diff_parser._extract_filename_from_diff_line(line)
                    for line in diff.split("\n")
                    if line.startswith("diff --git")
                ]
                for pattern in rule["file_patterns"]:
                    for filename in filenames:
                        if filename and fnmatch.fnmatch(filename, pattern):
                            logger.debug(
                                f"Context rule '{rule_name}' matched by file pattern '{pattern}'."
                            )
                            return self._get_or_create_provider(provider_name)

        return self.get_base_provider()

    def test_all_providers(self) -> Dict[str, bool]:
        """Tests connectivity for all configured providers."""
        results = {}
        for name, config in self.config.ai.providers.items():
            try:
                provider = self._get_or_create_provider(name)
                results[name] = provider.test_connectivity()
            except Exception as e:
                logger.error(f"Failed to test provider '{name}': {e}")
                results[name] = False
        return results

    def _get_or_create_provider(self, provider_name: str) -> BaseAIProvider:
        """Helper to get a provider instance, creating it if it doesn't exist."""
        if provider_name not in self._providers:
            provider_config = self.config.ai.providers.get(provider_name)
            if not provider_config:
                raise ValueError(
                    f"Configuration for provider '{provider_name}' not found."
                )
            self._providers[provider_name] = ProviderFactory.create_provider(
                provider_name, provider_config
            )
        return self._providers[provider_name]
