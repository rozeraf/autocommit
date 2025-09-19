"""
Diff parser for Git Auto Commit

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

import re
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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
    context_hints: List[str]
    is_large: bool


class DiffParser:
    """Parser for git diffs with smart analysis and context detection"""
    
    # File type patterns
    TEST_PATTERNS = [r'test', r'spec', r'__test__', r'\.test\.', r'\.spec\.']
    DOC_PATTERNS = [r'readme', r'changelog', r'license', r'\.md$', r'\.txt$', r'\.rst$']
    CONFIG_PATTERNS = [r'\.json$', r'\.yaml$', r'\.yml$', r'\.toml$', r'\.ini$', r'\.cfg$', r'\.conf$']
    DEPENDENCY_PATTERNS = [r'package\.json', r'requirements\.txt', r'pyproject\.toml', r'poetry\.lock', r'pom\.xml', r'Cargo\.toml']
    
    # Context keywords
    WIP_KEYWORDS = ['TODO', 'FIXME', 'WIP', 'HACK', 'XXX', 'NOTE']
    
    def __init__(self, max_lines: int = 100, max_chars: int = 8000):
        """
        Initialize diff parser
        
        Args:
            max_lines: Maximum lines to include in smart diff
            max_chars: Maximum characters to include in smart diff
        """
        self.max_lines = max_lines
        self.max_chars = max_chars
    
    def parse_diff(self, diff: str, context_length: Optional[int] = None) -> SmartDiff:
        """
        Parse git diff and create smart diff with context analysis
        
        Args:
            diff: Raw git diff content
            context_length: Model context length for dynamic limits
            
        Returns:
            SmartDiff with parsed content and analysis
        """
        if not diff:
            return self._create_empty_diff()
        
        # Calculate dynamic limits based on context length
        if context_length:
            self._calculate_dynamic_limits(context_length)
        
        # Analyze the diff
        stats = self._analyze_diff_stats(diff)
        context_hints = self._extract_context_hints(diff)
        
        # Create smart diff content
        smart_content = self._create_smart_diff(diff)
        
        # Determine if diff is large
        is_large = (stats.lines_added + stats.lines_removed) > 50 or stats.files_changed > 10
        
        return SmartDiff(
            content=smart_content,
            stats=stats,
            context_hints=context_hints,
            is_large=is_large
        )
    
    def _create_empty_diff(self) -> SmartDiff:
        """Create empty diff for when no changes are present"""
        return SmartDiff(
            content="",
            stats=DiffStats(
                files_changed=0,
                lines_added=0,
                lines_removed=0,
                file_types={},
                has_tests=False,
                has_docs=False,
                has_config=False,
                has_dependencies=False
            ),
            context_hints=[],
            is_large=False
        )
    
    def _calculate_dynamic_limits(self, context_length: int):
        """Calculate limits based on model context length"""
        # Reserve space for prompt and response
        available_for_diff = context_length - 4000  # Conservative estimate
        if available_for_diff > 0:
            self.max_chars = min(available_for_diff * 0.8, 20000)  # 80% for diff, max 20k
            # Heuristic: 1 line ~ 80 characters
            self.max_lines = self.max_chars // 80
        logger.debug(f"Dynamic limits: {self.max_lines} lines, {self.max_chars} characters")
    
    def _analyze_diff_stats(self, diff: str) -> DiffStats:
        """Analyze diff and extract statistics"""
        lines = diff.split('\n')
        
        files_changed = len([line for line in lines if line.startswith('diff --git')])
        lines_added = len([line for line in lines if line.startswith('+') and not line.startswith('+++')])
        lines_removed = len([line for line in lines if line.startswith('-') and not line.startswith('---')])
        
        # Analyze file types
        file_types = {}
        has_tests = False
        has_docs = False
        has_config = False
        has_dependencies = False
        
        for line in lines:
            if line.startswith('diff --git'):
                # Extract filename from diff line
                filename = self._extract_filename_from_diff_line(line)
                if filename:
                    file_ext = self._get_file_extension(filename)
                    file_types[file_ext] = file_types.get(file_ext, 0) + 1
                    
                    # Check for special file types
                    if self._is_test_file(filename):
                        has_tests = True
                    if self._is_doc_file(filename):
                        has_docs = True
                    if self._is_config_file(filename):
                        has_config = True
                    if self._is_dependency_file(filename):
                        has_dependencies = True
        
        return DiffStats(
            files_changed=files_changed,
            lines_added=lines_added,
            lines_removed=lines_removed,
            file_types=file_types,
            has_tests=has_tests,
            has_docs=has_docs,
            has_config=has_config,
            has_dependencies=has_dependencies
        )
    
    def _extract_filename_from_diff_line(self, line: str) -> Optional[str]:
        """Extract filename from diff --git line"""
        # Format: diff --git a/path/to/file b/path/to/file
        parts = line.split()
        if len(parts) >= 4:
            # Remove 'a/' prefix from first filename
            filename = parts[2][2:] if parts[2].startswith('a/') else parts[2]
            return filename
        return None
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        if '.' in filename:
            return filename.split('.')[-1].lower()
        return 'no_extension'
    
    def _is_test_file(self, filename: str) -> bool:
        """Check if file is a test file"""
        filename_lower = filename.lower()
        return any(re.search(pattern, filename_lower) for pattern in self.TEST_PATTERNS)
    
    def _is_doc_file(self, filename: str) -> bool:
        """Check if file is a documentation file"""
        filename_lower = filename.lower()
        return any(re.search(pattern, filename_lower) for pattern in self.DOC_PATTERNS)
    
    def _is_config_file(self, filename: str) -> bool:
        """Check if file is a configuration file"""
        filename_lower = filename.lower()
        return any(re.search(pattern, filename_lower) for pattern in self.CONFIG_PATTERNS)
    
    def _is_dependency_file(self, filename: str) -> bool:
        """Check if file is a dependency file"""
        filename_lower = filename.lower()
        return any(re.search(pattern, filename_lower) for pattern in self.DEPENDENCY_PATTERNS)
    
    def _extract_context_hints(self, diff: str) -> List[str]:
        """Extract context hints from diff content"""
        hints = []
        
        # Check for WIP keywords in added lines
        for line in diff.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                content = line[1:]  # Remove the + prefix
                for keyword in self.WIP_KEYWORDS:
                    if keyword in content.upper():
                        hints.append(f"Contains {keyword} keyword")
                        break
        
        # Check for test-related changes
        if any(line.startswith('+') and ('test' in line.lower() or 'spec' in line.lower()) 
               for line in diff.split('\n')):
            hints.append("Test-related changes detected")
        
        # Check for configuration changes
        if any(line.startswith('+') and any(pattern in line.lower() 
               for pattern in ['config', 'setting', 'option', 'parameter']) 
               for line in diff.split('\n')):
            hints.append("Configuration changes detected")
        
        return hints
    
    def _create_smart_diff(self, diff: str) -> str:
        """Create smart diff that respects limits"""
        lines = diff.split('\n')
        
        # If within limits, return full diff
        if len(lines) <= self.max_lines and len(diff) <= self.max_chars:
            return diff
        
        # Otherwise, take important parts:
        # 1. File headers (lines starting with 'diff --git')
        # 2. Chunk headers (@@ markers)
        # 3. Added/removed lines (+/-) up to limits
        smart_lines = []
        in_file_header = False
        
        for line in lines:
            if len('\n'.join(smart_lines)) >= self.max_chars:
                break
                
            if line.startswith('diff --git'):
                in_file_header = True
                smart_lines.append(line)
            elif in_file_header and line.startswith('index '):
                smart_lines.append(line)
            elif line.startswith('@@'):
                in_file_header = False
                smart_lines.append(line)
            elif line.startswith('+') or line.startswith('-'):
                if len(smart_lines) < self.max_lines:
                    smart_lines.append(line)
        
        return '\n'.join(smart_lines)
