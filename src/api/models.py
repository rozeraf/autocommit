"""
API response models for Git Auto Commit

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
from typing import Optional


@dataclass
class ModelInfo:
    """Model information from OpenRouter API"""
    id: str
    name: str
    context_length: Optional[int] = None
    pricing: Optional[dict] = None
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ModelInfo':
        """Create ModelInfo from API response dictionary"""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            context_length=data.get('context_length'),
            pricing=data.get('pricing'),
            description=data.get('description')
        )


@dataclass
class CommitMessage:
    """Structured commit message"""
    subject: str
    description: Optional[str] = None
    
    def to_git_format(self) -> str:
        """Convert to git commit format"""
        if self.description:
            return f"{self.subject}\n\n{self.description}"
        return self.subject
