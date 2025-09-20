
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers import CommitParser


def test_parse_ai_response_subject_only():
    """Tests parsing a commit message with only a subject line."""
    message = "feat(scope): this is the subject"
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == "feat(scope): this is the subject"
    assert result.description is None

def test_parse_ai_response_with_description():
    """Tests parsing a commit message with a subject and description."""
    message = "fix(api): resolve issue with parsing\n\nThis is the longer description body."
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == "fix(api): resolve issue with parsing"
    assert result.description == "This is the longer description body."

def test_parse_ai_response_with_multiline_description():
    """Tests parsing a commit message with a multi-line description."""
    message = "refactor(core): simplify logic\n\n- Removed complex conditional.\n- Improved readability."
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == "refactor(core): simplify logic"
    assert result.description == "- Removed complex conditional.\n- Improved readability."

def test_parse_ai_response_with_extra_whitespace():
    """Tests parsing a message with leading/trailing whitespace."""
    message = "  docs(readme): update usage instructions  \n\n  This description has whitespace.  \n"
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == "docs(readme): update usage instructions"
    assert result.description == "This description has whitespace."

def test_parse_ai_response_empty_description():
    """Tests parsing a message with an empty line between subject and description."""
    message = "chore: release new version\n\n"
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == "chore: release new version"
    assert result.description is None

def test_parse_ai_response_empty_input():
    """Tests parsing an empty string."""
    message = ""
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == ""
    assert result.description is None

def test_parse_ai_response_whitespace_input():
    """Tests parsing a string with only whitespace."""
    message = "   \n\n   "
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == ""
    assert result.description is None

def test_parse_ai_response_with_mermaid():
    """Tests parsing response with mermaid diagram."""
    message = """```mermaid
graph TD
    A --> B
```
Looking at the diff, this represents initial setup.

feat: initial project setup

This is the project initialization."""
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == "feat: initial project setup"
    assert result.description == "This is the project initialization."

def test_parse_ai_response_with_markdown():
    """Tests parsing response with markdown formatting."""
    message = """**feat**(api): **add** new endpoint

This is a *description* with `code` and **bold** text."""
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == "feat(api): add new endpoint"
    assert result.description == "This is a description with code and bold text."

def test_parse_ai_response_complex_cleanup():
    """Tests complex cleanup scenarios."""
    message = """## Analysis

Looking at the diff, this represents:

### Changes
- **feat**: new feature
- **fix**: bug resolution

**chore**(setup): initial configuration

Setup project structure and dependencies."""
    parser = CommitParser()
    result = parser.parse_ai_response(message)
    assert result.subject == "chore(setup): initial configuration"
    assert result.description == "Setup project structure and dependencies."
