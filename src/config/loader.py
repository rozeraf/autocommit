"""
Configuration loader for Git Auto Commit

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

import logging
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

from ..models.config import (
    AIConfig,
    FormatConfig,
    DiffConfig,
    ContextConfig,
    AppConfig,
)

logger = logging.getLogger(__name__)


def _find_config_file() -> Optional[Path]:
    """Find config.toml file in current directory, then home directory"""
    # Check current directory first
    current_dir = Path.cwd()
    config_path = current_dir / "config.toml"
    if config_path.exists():
        logger.debug(f"Found config.toml in current directory: {config_path}")
        return config_path

    # Check home directory
    home_dir = Path.home()
    config_path = home_dir / "config.toml"
    if config_path.exists():
        logger.debug(f"Found config.toml in home directory: {config_path}")
        return config_path

    logger.debug("No config.toml found, using defaults")
    return None


def _load_toml_config(config_path: Path) -> dict:
    """Load TOML configuration file"""
    if not tomllib:
        logger.warning("tomllib or toml library not available, using defaults")
        return {}

    try:
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
        logger.debug(f"Loaded config from {config_path}")
        return config_data
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}


def get_config() -> AppConfig:
    """
    Load configuration with fallback to defaults

    Returns:
        AppConfig: Complete application configuration
    """
    config_data = {}

    # Try to load from config file
    config_path = _find_config_file()
    if config_path:
        config_data = _load_toml_config(config_path)

    # Create configuration objects with defaults
    ai_config = AIConfig(
        model=config_data.get("ai", {}).get("model", "anthropic/claude-3.5-sonnet"),
        api_url=config_data.get("ai", {}).get(
            "api_url", "https://openrouter.ai/api/v1"
        ),
        temperature=config_data.get("ai", {}).get("temperature", 0.3),
        max_tokens=config_data.get("ai", {}).get("max_tokens", 1000),
        timeout=config_data.get("ai", {}).get("timeout", 45),
        prompts=config_data.get("ai", {}).get("prompts", {}),
    )

    format_config = FormatConfig(
        max_subject_length=config_data.get("format", {}).get("max_subject_length", 70),
        require_body_for_features=config_data.get("format", {}).get(
            "require_body_for_features", True
        ),
        enforce_conventional=config_data.get("format", {}).get(
            "enforce_conventional", True
        ),
        allowed_types=config_data.get("format", {}).get(
            "allowed_types",
            [
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
            ],
        ),
    )

    diff_config = DiffConfig(
        context_reserve=config_data.get("diff", {}).get("context_reserve", 4000),
        char_per_line_ratio=config_data.get("diff", {}).get("char_per_line_ratio", 80),
    )

    context_config = ContextConfig(
        wip_keywords=config_data.get("context", {}).get(
            "wip_keywords", ["TODO", "FIXME", "WIP", "HACK", "XXX", "NOTE"]
        ),
        auto_detect=config_data.get("context", {}).get("auto_detect", True),
    )

    return AppConfig(
        ai=ai_config, format=format_config, diff=diff_config, context=context_config
    )
