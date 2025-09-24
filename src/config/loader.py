"""
Configuration loader for Git Auto Commit
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

from .models import Config, AIConfig, FormatConfig, ContextConfig, ProviderConfig, DiffConfig

logger = logging.getLogger(__name__)

def _find_config_file() -> Optional[Path]:
    """Find config.toml file in project root, current directory, then home directory"""
    search_paths = [Path.cwd(), Path.home(), Path(__file__).parent.parent.parent]
    for path in search_paths:
        config_path = path / "config.toml"
        if config_path.exists():
            logger.debug(f"Found config.toml in: {config_path}")
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
            return tomllib.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}

def get_config() -> Config:
    """
    Load configuration with fallback to defaults
    """
    config_data = _load_toml_config(_find_config_file()) if _find_config_file() else {}
    ai_data = config_data.get("ai", {})

    providers = {}
    for name, provider_data in ai_data.get("providers", {}).items():
        providers[name] = ProviderConfig(**provider_data)

    ai_config = AIConfig(
        base_provider=ai_data.get("base_provider", "openrouter"),
        context_switching=ai_data.get("context_switching", True),
        providers=providers,
        context_rules=ai_data.get("context_rules", {}),
        prompts=ai_data.get("prompts", {}),
        model=ai_data.get("model", ""),
        api_url=ai_data.get("api_url", ""),
        temperature=ai_data.get("temperature", 0.4),
        max_tokens=ai_data.get("max_tokens", 250),
        timeout=ai_data.get("timeout", 45),
    )

    format_data = config_data.get("format", {})
    format_config = FormatConfig(**format_data)

    context_data = config_data.get("context", {})
    context_config = ContextConfig(**context_data)

    diff_data = config_data.get("diff", {})
    diff_config = DiffConfig(**diff_data)

    return Config(ai=ai_config, format=format_config, context=context_config, diff=diff_config)