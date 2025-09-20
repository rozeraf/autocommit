"""
Tests for diff parser functionality

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

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers import DiffParser


def test_parse_empty_diff():
    """Test parsing empty diff"""
    parser = DiffParser()
    result = parser.parse_diff("")

    assert result.content == ""
    assert result.stats.files_changed == 0
    assert result.stats.lines_added == 0
    assert result.stats.lines_removed == 0
    assert not result.is_large


def test_parse_simple_diff():
    """Test parsing simple diff"""
    diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("hello")
+    print("hello world")
+    print("goodbye")
"""
    parser = DiffParser()
    result = parser.parse_diff(diff)

    assert result.stats.files_changed == 1
    assert result.stats.lines_added == 2
    assert result.stats.lines_removed == 1
    assert result.stats.file_types["py"] == 1
    assert not result.is_large


def test_parse_diff_with_multiple_files():
    """Test parsing diff with multiple files"""
    diff = """diff --git a/src/main.py b/src/main.py
index 1111111..2222222 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,2 +1,3 @@
 def main():
+    print("Hello")
     return 0

diff --git a/tests/test_main.py b/tests/test_main.py
index 3333333..4444444 100644
--- a/tests/test_main.py
+++ b/tests/test_main.py
@@ -1,2 +1,3 @@
 def test_main():
+    assert main() == 0
     pass
"""
    parser = DiffParser()
    result = parser.parse_diff(diff)

    assert result.stats.files_changed == 2
    assert result.stats.lines_added == 2
    assert result.stats.lines_removed == 0
    assert result.stats.file_types["py"] == 2
    assert result.stats.has_tests


def test_parse_diff_with_docs():
    """Test parsing diff with documentation files"""
    diff = """diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Project
+This is a test project.
"""
    parser = DiffParser()
    result = parser.parse_diff(diff)

    assert result.stats.has_docs
    assert result.stats.file_types["md"] == 1


def test_parse_diff_with_config():
    """Test parsing diff with configuration files"""
    diff = """diff --git a/package.json b/package.json
index 1111111..2222222 100644
--- a/package.json
+++ b/package.json
@@ -1,3 +1,4 @@
 {
   "name": "test",
+  "version": "1.0.0",
   "dependencies": {}
 }
"""
    parser = DiffParser()
    result = parser.parse_diff(diff)

    assert result.stats.has_config
    assert result.stats.file_types["json"] == 1


def test_parse_diff_with_dependencies():
    """Test parsing diff with dependency files"""
    diff = """diff --git a/requirements.txt b/requirements.txt
index 1111111..2222222 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,3 @@
 requests
+flask
"""
    parser = DiffParser()
    result = parser.parse_diff(diff)

    assert result.stats.has_dependencies


def test_parse_diff_with_wip_keywords():
    """Test parsing diff with WIP keywords"""
    diff = """diff --git a/src/main.py b/src/main.py
index 1111111..2222222 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,2 +1,3 @@
 def main():
+    # TODO: implement this function
     return 0
"""
    parser = DiffParser()
    result = parser.parse_diff(diff)

    assert "Contains TODO keyword" in result.context_hints


def test_parse_large_diff():
    """Test parsing large diff"""
    # Create a large diff
    lines = ["diff --git a/test.py b/test.py", "index 1111111..2222222 100644"]
    for i in range(100):
        lines.append(f"+    print('line {i}')")

    diff = "\n".join(lines)
    parser = DiffParser(max_lines=50, max_chars=1000)
    result = parser.parse_diff(diff)

    assert result.is_large
    assert len(result.content.split("\n")) <= 50


def test_parse_diff_with_context_length():
    """Test parsing diff with context length"""
    diff = """diff --git a/test.py b/test.py
index 1111111..2222222 100644
--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 def main():
+    print("Hello")
     return 0
"""
    parser = DiffParser()
    result = parser.parse_diff(diff, context_length=10000)

    # Should use dynamic limits
    assert result.stats.files_changed == 1
