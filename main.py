#!/usr/bin/env python3
"""
Git Auto Commit - automatic commit creation using AI
"""

import subprocess
import os
import sys
import requests
import json
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

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
    except Exception as e:
        return str(e), 1

def get_model_info(model_name: str) -> Optional[dict]:
    """Gets model information from the OpenRouter API"""
    api_url = "https://openrouter.ai/api/v1/models"
    print("Getting model information...")
    try:
        response = requests.get(api_url, timeout=15)
        if response.status_code != 200:
            print(f"Failed to get model list (status: {response.status_code})")
            return None
        
        models_data = response.json().get("data", [])
        for model in models_data:
            if model.get("id") == model_name:
                print(f"Model information for {model_name} received.")
                return model
        
        print(f"Model '{model_name}' not found.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error requesting model information: {e}")
        return None

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

def parse_ai_response(full_message: str) -> Tuple[str, Optional[str]]:
    """Splits the full commit message into a subject and description."""
    lines = full_message.strip().split('\n', 1)
    commit_msg = lines[0].strip()
    description = None
    if len(lines) > 1 and lines[1].strip():
        description = lines[1].strip()
    return commit_msg, description

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

def generate_commit_message(diff: str, model_info: Optional[dict]) -> Optional[Tuple[str, Optional[str]]]:
    """Generates a commit message via the OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key:
        print("Error: OPENROUTER_API_KEY is not set in the .env file.")
        print("Create a .env file with OPENROUTER_API_KEY=your_key")
        return None
    
    print(f"Using API key: {api_key[:8]}...")
    print(f"URL: {api_url}")
    print(f"Model: {model}")
    
    context_length = None
    if model_info and "context_length" in model_info:
        context_length = int(model_info["context_length"])
        print(f"Model context length: {context_length} tokens")
    else:
        print("Could not determine context length, using default values.")

    smart_diff = get_smart_diff(diff, context_length)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/rozeraf/git-auto-commit",
        "X-Title": "Git Auto Commit"
    }
    
    system_prompt = '''Your task is to generate a commit message based on the provided diff, following the Conventional Commits specification.

RULES:
1. The output must be ONLY the commit message text, without any extra words or explanations.
2. The message must be in English.
3. The format is: `type(scope): subject`
    - Followed by an optional longer body.
    - Followed by an optional `BREAKING CHANGE:` footer.
4. Use the following types:
    - `feat`: A new feature.
    - `fix`: A bug fix.
    - `docs`: Documentation only changes.
    - `style`: Code style changes (formatting, etc).
    - `refactor`: A code change that neither fixes a bug nor adds a feature.
    - `perf`: A code change that improves performance.
    - `test`: Adding missing tests or correcting existing tests.
    - `build`: Changes that affect the build system or external dependencies.
    - `ci`: Changes to CI configuration files and scripts.
    - `chore`: Other changes that don't modify src or test files.
    - `revert`: Reverts a previous commit.
5. The body, if present, should have a header, a list of changes starting with `-`, and an optional footer.'''

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Create a commit message for these changes:\n{smart_diff}"
            }
        ],
        "max_tokens": 250, 
        "temperature": 0.4
    }
    
    try:
        print("Generating commit message...")
        print("Sending request to API...")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=45
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except json.JSONDecodeError:
                print(f"Response body: {response.text}")
            return None
        
        response_text = response.text.strip()
        if not response_text:
            print("Empty response from API")
            return None
            
        print(f"Received response ({len(response_text)} characters)")
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"First 200 characters of response: {response_text[:200]}")
            return None
        
        if "choices" not in data or len(data["choices"]) == 0:
            print(f"Invalid response format: {data}")
            return None
        
        if "message" not in data["choices"][0]:
            print(f"Missing message field: {data['choices'][0]}")
            return None
            
        ai_response = data["choices"][0]["message"]["content"].strip()
        print(f"AI Response:\n{ai_response}")
        
        return parse_ai_response(ai_response)
        
    except requests.exceptions.Timeout:
        print("Request timeout (45s). Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        print("API connection error. Check your internet connection.")
        return None
    except KeyboardInterrupt:
        print("\nRequest cancelled by user")
        return None
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

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

def show_confirmation(commit_msg: str, description: Optional[str]) -> bool:
    """Shows confirmation before committing"""
    print("\n--- Commit Preview ---")
    print(f"Message: {commit_msg}")
    if description:
        print(f"Description:\n{description}")
    print("-----------------------------")
    
    if len(sys.argv) > 1 and sys.argv[1] in ["-y", "--yes"]:
        return True
    
    confirm = input("Create commit? [Y/n]: ").lower()
    return confirm in ( "", "y", "yes")

def test_api_key():
    api_key = os.getenv("OPENROUTER_API_KEY")
    api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key:
        print("Error: OPENROUTER_API_KEY is not set in the .env file.")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    try:
        print("Testing API key...")
        print(f"URL: {api_url}")
        print(f"Model: {model}")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("API key is working!")
            return True
        else:
            print(f"Problem with API key: {response.text}")
            return False
            
    except Exception as e:
        print(f"Testing error: {e}")
        return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test-api":
        test_api_key()
        return
    
    print("Git Auto Commit: generating commit for staged files...")
    
    _, code = run_command("git rev-parse --git-dir")
    if code != 0:
        print("Error: git repository not found.")
        sys.exit(1)

    model_name = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    model_info = get_model_info(model_name)
    
    diff = get_git_diff()
    if not diff:
        sys.exit(1)
    
    result = generate_commit_message(diff, model_info)
    if not result:
        print("Failed to generate commit message.")
        print("Try: python3 main.py --test-api")
        sys.exit(1)
    
    commit_msg, description = result

    if show_confirmation(commit_msg, description):
        success = commit_changes(commit_msg, description)
        if success:
            print("Done!")
        else:
            sys.exit(1)
    else:
        print("Commit cancelled.")
        sys.exit(1)

if __name__ == "__main__":
    main()
