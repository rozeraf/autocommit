import os
from unittest.mock import patch

import pytest
from src import ui
from src.parsers.commit_parser import CommitParser

# --- UI Tests ---


def test_resolve_editor_visual():
    with patch.dict(os.environ, {"VISUAL": "visual_editor", "EDITOR": "editor"}):
        assert ui._resolve_editor() == "visual_editor"


def test_resolve_editor_editor():
    with patch.dict(os.environ, {"VISUAL": "", "EDITOR": "editor"}):
        assert ui._resolve_editor() == "editor"


def test_resolve_editor_fallback():
    with patch.dict(os.environ, {"VISUAL": "", "EDITOR": ""}):
        with patch("shutil.which", side_effect=lambda x: x if x == "vim" else None):
            assert ui._resolve_editor() == "vim"


def test_resolve_editor_none():
    with patch.dict(os.environ, {"VISUAL": "", "EDITOR": ""}):
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="No suitable editor found"):
                ui._resolve_editor()


@patch("subprocess.run")
def test_open_in_editor_code(mock_run):
    with patch("src.ui._resolve_editor", return_value="code"):
        ui.open_in_editor("test")
        # Check that --wait was added
        args = mock_run.call_args[0][0]
        assert "code" in args
        assert "--wait" in args
        # Check temp file path is last arg
        assert args[-1].endswith(".txt")


@patch("subprocess.run")
def test_open_in_editor_subl(mock_run):
    with patch("src.ui._resolve_editor", return_value="subl"):
        ui.open_in_editor("test")
        args = mock_run.call_args[0][0]
        assert "subl" in args
        assert "--wait" in args


@patch("subprocess.run")
def test_open_in_editor_vim(mock_run):
    with patch("src.ui._resolve_editor", return_value="vim"):
        ui.open_in_editor("test")
        args = mock_run.call_args[0][0]
        assert "vim" in args
        assert "--wait" not in args


@patch("subprocess.run")
def test_open_in_editor_existing_wait(mock_run):
    with patch("src.ui._resolve_editor", return_value="code --wait"):
        ui.open_in_editor("test")
        args = mock_run.call_args[0][0]
        assert args.count("--wait") == 1


# --- Parser Tests ---


def test_parse_edited_split():
    parser = CommitParser()
    text = "feat: subject\n\ndescription body"
    result = parser.parse_edited(text)
    assert result.subject == "feat: subject"
    assert result.description == "description body"
    assert result.is_valid


def test_parse_edited_no_desc():
    parser = CommitParser()
    text = "feat: subject"
    result = parser.parse_edited(text)
    assert result.subject == "feat: subject"
    assert result.description is None
    assert result.is_valid


def test_parse_edited_empty():
    parser = CommitParser()
    result = parser.parse_edited("")
    assert not result.is_valid
    assert "Empty commit message" in result.warnings


def test_parse_edited_subject_newline():
    parser = CommitParser()
    text = "feat: subject\\nwith newline\\n\\ndescription"
    # Using \\n to ensure it is interpreted as newline char in the string
    # Actually, simpler is to just use a multiline string for the input
    text = """feat: subject
with newline

description"""
    result = parser.parse_edited(text)
    # The parser replaces \n in subject with space
    assert result.subject == "feat: subject with newline"
    assert result.description == "description"
