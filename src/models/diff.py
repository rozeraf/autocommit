"""
Diff models
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class DiffStats:
    """Statistics about a diff"""

    files_changed: int
    lines_added: int
    lines_removed: int
    file_types: Dict[str, int]  # extension -> count
    has_tests: bool
    has_docs: bool
    has_config: bool
    has_dependencies: bool


@dataclass
class SmartDiff:
    """Smart diff with context analysis"""

    content: str
    stats: DiffStats
    is_large: bool
