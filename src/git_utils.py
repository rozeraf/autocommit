"""
Git utilities for interacting with git repositories
"""

import subprocess
from typing import Optional


def run_command(cmd: str, show_output: bool = False) -> tuple[str, int]:
    """Executes a command and returns the output and return code"""
    try:
        if show_output:
            # Show real-time output for commands that may have interactive output (e.g., git hooks)
            result = subprocess.run(
                cmd, 
                shell=True, 
                text=True, 
                check=False
            )
            return "", result.returncode
        else:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=False
            )
            return result.stdout.strip(), result.returncode
    except FileNotFoundError:
        error_msg = f"Command not found: {cmd.split()[0] if cmd.split() else 'unknown'}"
        print(f"Error: {error_msg}")
        return error_msg, 127  # 127 is a common exit code for command not found
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out: {cmd}"
        print(f"Error: {error_msg}")
        return error_msg, 124  # 124 is a common exit code for timeout
    except (subprocess.SubprocessError, OSError) as e:
        error_msg = f"Subprocess error executing '{cmd}': {str(e)}"
        print(f"Error: {error_msg}")
        return error_msg, 1
    except Exception as e:
        # Fallback for any unexpected errors
        error_msg = f"Unexpected error executing '{cmd}': {type(e).__name__}: {str(e)}"
        print(f"Error: {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg, 1


def get_git_diff() -> Optional[str]:
    """Gets git diff --cached for staged files"""
    staged_files, code = run_command("git diff --cached --name-only")
    if code != 0:
        print("Error checking staged files")
        return None
    
    if not staged_files.strip():
        print("No staged files to commit.")
        print("First, add files: git add <files>")
        return None
    
    print(f"Staged files: {staged_files.replace(chr(10), ', ')}")
    
    diff, code = run_command("git diff --cached")
    if code != 0:
        print("Error getting diff")
        return None
    
    return diff


def commit_changes(message: str, description: Optional[str] = None) -> bool:
    """Creates a commit with the specified message"""
    full_message = message
    if description:
        full_message = f"{message}\n\n{description}"
    
    escaped_message = full_message.replace('"', '"').replace('`', '`')
    
    print("\nCreating commit...")
    
    # Use show_output=True to see git hooks output
    _, code = run_command(f'git commit -m "{escaped_message}"', show_output=True)
    
    if code == 0:
        print("Commit created successfully!")
        return True
    else:
        print(f"Error creating commit (code: {code})")
        return False


def get_smart_diff(diff: str, context_length: Optional[int]) -> str:
    """Gets a smart, compressed diff for large changes based on the model's context."""
    lines = diff.split('\n')
    diff_lines = len(lines)
    diff_chars = len(diff)
    
    print(f"Diff size: {diff_lines} lines, {diff_chars} characters")
    
    # Default values if model information is unavailable
    line_limit = 1000
    char_limit = 10000

    if context_length:
        # Calculating limits based on model context length.
        # Using 50% of the context for the diff to leave space for the prompt and response.
        # Heuristic: 1 token ~ 4 characters.
        char_limit = int(context_length * 0.5 * 4)
        # Heuristic: 1 line ~ 80 characters.
        line_limit = char_limit // 80
        print(f"Dynamic limits (context {context_length}): {line_limit} lines, {char_limit} characters")
    else:
        print(f"Using default limits: {line_limit} lines, {char_limit} characters")

    if diff_lines > line_limit:
        print(f"Diff is too large ({diff_lines} > {line_limit} lines), using a brief summary.")
        
        stats_output, _ = run_command("git diff --cached --stat")
        name_status_output, _ = run_command("git diff --cached --name-status")
        
        return f'''=== CHANGE STATISTICS ===
{stats_output}

=== MODIFIED FILES ===
{name_status_output}

=== CHANGE EXAMPLES ===
{chr(10).join(lines[:50])}
...
{chr(10).join(lines[-20:])}

(Showing the first 50 and last 20 lines out of {diff_lines} total)'''
    
    elif diff_chars > char_limit:
        print(f"Diff is large ({diff_chars} > {char_limit} characters), shortening...")
        return diff[:char_limit] + f"\n...(showing the first {char_limit} characters)"
    
    return diff