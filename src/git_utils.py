"""
Git utilities for interacting with git repositories

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

import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

def run_command(cmd_parts: list[str], timeout: int = 30, show_output: bool = False) -> tuple[str, int]:
    """Executes a command as list of arguments and returns the output and return code.
    
    Args:
        cmd_parts: List of command and arguments (e.g., ['git', 'diff', '--cached'])
        show_output: If True, shows output in real-time instead of capturing it
        timeout: Timeout in seconds for the command
    """
    error_occurred = False
    exit_code = 1
    
    try:
        if show_output:
            # Show real-time output for commands that may have interactive output (e.g., git hooks)
            # Don't capture output, let it go directly to terminal
            result = subprocess.run(
                cmd_parts,
                text=True,
                check=False,
                timeout=timeout,
                stderr=subprocess.STDOUT if show_output else None
            )
            return "", result.returncode
        else:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout
            )
            return result.stdout.strip(), result.returncode
            
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout}s: {' '.join(cmd_parts)}"
        logger.error(f"Error: {error_msg}")
        exit_code = 124
        error_occurred = True
    except FileNotFoundError:
        cmd_name = cmd_parts[0] if cmd_parts else "unknown"
        error_msg = f"Command not found: {cmd_name}"
        logger.error(f"Error: {error_msg}")
        exit_code = 127
        error_occurred = True
    except (subprocess.SubprocessError, OSError) as e:
        error_msg = f"Subprocess error executing {' '.join(cmd_parts)}: {str(e)}"
        logger.error(f"Error: {error_msg}")
        exit_code = 1
        error_occurred = True
    except Exception as e:
        # Fallback for any unexpected errors
        error_msg = f"Unexpected error executing {' '.join(cmd_parts)}: {type(e).__name__}: {str(e)}"
        logger.error(f"Error: {error_msg}")
        import traceback
        traceback.print_exc()
        exit_code = 1
        error_occurred = True
    
    # Return empty string for stdout when show_output=True or error occurred
    # This prevents error messages from being passed to shell
    if show_output or error_occurred:
        return "", exit_code
    else:
        # For normal captured output with errors, return the error message
        return error_msg, exit_code


def get_git_diff() -> str | None:
    """Gets git diff --cached for staged files"""
    staged_files, code = run_command(["git", "diff", "--cached", "--name-only"])
    if code != 0:
        logger.error("Error checking staged files")
        return None

    if not staged_files.strip():
        logger.warning("No staged files to commit.")
        logger.info("First, add files: git add <files>")
        return None

    logger.debug(f"Staged files: {staged_files.replace(chr(10), ', ')}")
    
    diff, code = run_command(["git", "diff", "--cached"])
    if code != 0:
        logger.error("Error getting diff")
        return None

    return diff


def commit_changes(message: str, description: str | None = None) -> bool:
    """Creates a commit with the specified message"""
    logger.debug("\nCreating commit...")
    
    # Use subject as main message, description as body
    if description:
        # Git commit format: subject on first line, body after blank line
        full_message = f"{message}\n\n{description}"
    else:
        full_message = message
    
    logger.debug(f"Commit subject: {message}")
    if description:
        logger.debug(f"Commit body: {description[:100]}...")
    
    # Use show_output=True to see git hooks output, and longer timeout for commit operations
    _, code = run_command(
        ["git", "commit", "-m", full_message], 
        show_output=True, 
        timeout=120
    )
    
    if code == 0:
        logger.info("Commit created successfully")
        return True
    else:
        logger.error(f"Error creating commit (exit code: {code})")
        return False


def calculate_diff_limits(context_length: int | None) -> tuple[int, int]:
    """Calculate limits for diff based on model context length"""
    # Default values if model information is unavailable
    char_limit = 8000
    line_limit = 100
    
    if context_length:
        # Reserve space for prompt and response
        available_for_diff = context_length - 4000  # Conservative estimate
        if available_for_diff > 0:
            char_limit = min(available_for_diff * 0.8, 20000)  # 80% for diff, max 20k
            # Heuristic: 1 line ~ 80 characters.
            line_limit = char_limit // 80
        logger.debug(f"Dynamic limits (context {context_length}): {line_limit} lines, {char_limit} characters")
    else:
        logger.debug(f"Using default limits: {line_limit} lines, {char_limit} characters")
    
    return line_limit, char_limit


def get_smart_diff(diff: str, context_length: int | None) -> str:
    """Gets a smart diff that respects context length limits"""
    if not diff:
        return ""
    
    line_limit, char_limit = calculate_diff_limits(context_length)
    
    # Split diff into lines
    lines = diff.split("\n")
    
    # If within limits, return full diff
    if len(lines) <= line_limit and len(diff) <= char_limit:
        return diff
    
    # Otherwise, take important parts:
    # 1. File headers (lines starting with 'diff --git')
    # 2. Chunk headers (@@ markers)
    # 3. Added/removed lines (+/-) up to limits
    smart_lines = []
    in_file_header = False
    
    for line in lines:
        if len("\n".join(smart_lines)) >= char_limit:
            break
            
        if line.startswith("diff --git"):
            in_file_header = True
            smart_lines.append(line)
        elif in_file_header and line.startswith("index "):
            smart_lines.append(line)
        elif line.startswith("@@"):
            in_file_header = False
            smart_lines.append(line)
        elif line.startswith("+") or line.startswith("-"):
            if len(smart_lines) < line_limit:
                smart_lines.append(line)
    
    return "\n".join(smart_lines)