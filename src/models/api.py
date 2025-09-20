"""
API response models for Git Auto Commit
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
