"""
Commit message models
"""

from dataclasses import dataclass
from typing import Optional


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
