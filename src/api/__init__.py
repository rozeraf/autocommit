"""
API module for Git Auto Commit

This module provides HTTP client functionality and OpenRouter API integration.
"""

from .client import HTTPClient
from .openrouter import OpenRouterClient
from .models import ModelInfo, CommitMessage

__all__ = ["HTTPClient", "OpenRouterClient", "ModelInfo", "CommitMessage"]
