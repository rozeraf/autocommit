"""
Tests for git utilities
"""

import subprocess
from unittest.mock import patch, MagicMock

from src import git_utils
from src.config import get_config


@patch("subprocess.run")
def test_run_command_success(mock_subprocess_run):
    """Test successful command execution"""
    mock_result = MagicMock()
    mock_result.stdout = "Success"
    mock_result.returncode = 0
    mock_subprocess_run.return_value = mock_result

    output, code = git_utils.run_command(["git", "status"])

    assert output == "Success"
    assert code == 0
    mock_subprocess_run.assert_called_once_with(
        ["git", "status"], capture_output=True, text=True, check=False, timeout=30
    )


@patch("subprocess.run")
def test_run_command_error(mock_subprocess_run):
    """Test command execution with a non-zero exit code"""
    mock_result = MagicMock()
    mock_result.stdout = "Error output"
    mock_result.returncode = 1
    mock_subprocess_run.return_value = mock_result

    output, code = git_utils.run_command(["git", "invalid-command"])

    assert output == "Error output"
    assert code == 1


@patch(
    "subprocess.run",
    side_effect=subprocess.TimeoutExpired(cmd="git status", timeout=10),
)
def test_run_command_timeout(mock_subprocess_run, caplog):
    """Test command timeout"""
    output, code = git_utils.run_command(["git", "status"])

    assert output == ""
    assert code == 124
    assert "Command timed out" in caplog.text


@patch("subprocess.run", side_effect=FileNotFoundError("git not found"))
def test_run_command_file_not_found(mock_subprocess_run, caplog):
    """Test command not found"""
    output, code = git_utils.run_command(["git", "status"])

    assert output == ""
    assert code == 127
    assert "Command not found: git" in caplog.text


@patch("src.git_utils.run_command")
def test_get_git_diff_success(mock_run_command):
    """Test get_git_diff when staged files exist"""
    mock_run_command.side_effect = [
        ("file1.py\nfile2.py", 0),  # First call for name-only
        ("diff content", 0),  # Second call for full diff
    ]

    diff = git_utils.get_git_diff()

    assert diff == "diff content"
    assert mock_run_command.call_count == 2


@patch("src.git_utils.run_command")
def test_get_git_diff_no_staged_files(mock_run_command):
    """Test get_git_diff when no files are staged"""
    mock_run_command.return_value = ("", 0)

    diff = git_utils.get_git_diff()

    assert diff is None
    mock_run_command.assert_called_once_with(["git", "diff", "--cached", "--name-only"])


@patch("src.git_utils.run_command")
def test_commit_changes_success(mock_run_command):
    """Test successful commit"""
    mock_run_command.return_value = ("", 0)

    success = git_utils.commit_changes("feat: new feature", "description")

    assert success is True
    mock_run_command.assert_called_once_with(
        ["git", "commit", "-m", "feat: new feature\n\ndescription"],
        show_output=True,
        timeout=120,
    )


@patch("src.git_utils.run_command")
def test_commit_changes_failure(mock_run_command):
    """Test failed commit"""
    mock_run_command.return_value = ("Error", 1)

    success = git_utils.commit_changes("feat: new feature", None)

    assert success is False
    mock_run_command.assert_called_once_with(
        ["git", "commit", "-m", "feat: new feature"], show_output=True, timeout=120
    )


def test_calculate_diff_limits_with_context():
    """Test diff limit calculation with a given context length"""
    config = get_config()
    context_length = 16000
    # available = 16000 - 4000 = 12000
    # char_limit = 12000 * 0.8 = 9600
    # line_limit = 9600 / 80 = 120
    expected_char_limit = int((context_length - config.diff.context_reserve) * 0.8)
    expected_line_limit = expected_char_limit // config.diff.char_per_line_ratio

    line_limit, char_limit = git_utils.calculate_diff_limits(context_length)

    assert line_limit == expected_line_limit
    assert char_limit == expected_char_limit


def test_calculate_diff_limits_no_context():
    """Test diff limit calculation without a given context length"""
    config = get_config()
    expected_char_limit = 8000
    expected_line_limit = expected_char_limit // config.diff.char_per_line_ratio

    line_limit, char_limit = git_utils.calculate_diff_limits(None)

    assert line_limit == expected_line_limit
    assert char_limit == expected_char_limit
