"""
Tests for the ContextDetector
"""

from src.context.detector import ContextDetector
from src.models.diff import DiffStats


def test_detect_wip_keywords():
    """Test that WIP keywords like TODO are detected from the diff."""
    detector = ContextDetector()
    diff = """diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,2 +1,3 @@
 def main():
+    # TODO: implement this function
     return 0
"""
    stats = DiffStats(
        files_changed=1,
        lines_added=1,
        lines_removed=0,
        file_types={"py": 1},
        has_tests=False,
        has_docs=False,
        has_config=False,
        has_dependencies=False,
    )

    hints = detector.detect(diff, stats)

    assert "wip_keyword_todo" in hints


def test_detect_from_stats():
    """Test that context is detected from DiffStats."""
    detector = ContextDetector()
    diff = ""  # Empty diff
    stats = DiffStats(
        files_changed=4,
        lines_added=10,
        lines_removed=2,
        file_types={"py": 1, "md": 1, "toml": 1, "txt": 1},
        has_tests=True,
        has_docs=True,
        has_config=True,
        has_dependencies=True,
    )

    hints = detector.detect(diff, stats)

    assert "tests_modified" in hints
    assert "docs_modified" in hints
    assert "config_modified" in hints
    assert "deps_modified" in hints


def test_detect_large_feature():
    """Test that a large number of additions is detected as a feature."""
    detector = ContextDetector()
    diff = ""  # Empty diff
    stats = DiffStats(
        files_changed=1,
        lines_added=150,
        lines_removed=10,
        file_types={"py": 1},
        has_tests=False,
        has_docs=False,
        has_config=False,
        has_dependencies=False,
    )

    hints = detector.detect(diff, stats)

    assert "large_feature" in hints
