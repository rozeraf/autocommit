"""
Configuration models for Git Auto Commit

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

from dataclasses import dataclass
from typing import List


@dataclass
class AIConfig:
    """AI model configuration"""
    model: str
    api_url: str
    temperature: float
    max_tokens: int
    timeout: int
    
    def __post_init__(self):
        """Validate AI configuration"""
        if not self.model:
            raise ValueError("AI model cannot be empty")
        if not self.api_url:
            raise ValueError("API URL cannot be empty")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")


@dataclass
class FormatConfig:
    """Commit message format configuration"""
    max_subject_length: int
    require_body_for_features: bool
    enforce_conventional: bool
    allowed_types: List[str]
    
    def __post_init__(self):
        """Validate format configuration"""
        if self.max_subject_length <= 0:
            raise ValueError("Max subject length must be positive")
        if not self.allowed_types:
            raise ValueError("Allowed types cannot be empty")


@dataclass
class DiffConfig:
    """Diff processing configuration"""
    context_reserve: int
    char_per_line_ratio: int
    
    def __post_init__(self):
        """Validate diff configuration"""
        if self.context_reserve < 0:
            raise ValueError("Context reserve cannot be negative")
        if self.char_per_line_ratio <= 0:
            raise ValueError("Char per line ratio must be positive")


@dataclass
class AppConfig:
    """Complete application configuration"""
    ai: AIConfig
    format: FormatConfig
    diff: DiffConfig
    
    def __post_init__(self):
        """Validate complete configuration"""
        if not isinstance(self.ai, AIConfig):
            raise ValueError("AI config must be AIConfig instance")
        if not isinstance(self.format, FormatConfig):
            raise ValueError("Format config must be FormatConfig instance")
        if not isinstance(self.diff, DiffConfig):
            raise ValueError("Diff config must be DiffConfig instance")
