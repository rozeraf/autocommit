#!/usr/bin/env python3
"""
Git Auto Commit - automatic commit creation using AI
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv
from src import git_utils, api_client

load_dotenv()


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
    return confirm in ("", "y", "yes")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test-api":
        api_client.test_api_key()
        return
    
    print("Git Auto Commit: generating commit for staged files...")
    
    # Check if we're in a git repository
    _, code = git_utils.run_command(["git", "rev-parse", "--git-dir"])
    if code != 0:
        print("Error: git repository not found.")
        sys.exit(1)

    model_name = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    model_info = api_client.get_model_info(model_name)
    
    diff = git_utils.get_git_diff()
    if not diff:
        sys.exit(1)
    
    result = api_client.generate_commit_message(diff, model_info)
    if not result:
        print("Failed to generate commit message.")
        print("Try: python3 main.py --test-api")
        sys.exit(1)
    
    commit_msg, description = result

    if show_confirmation(commit_msg, description):
        success = git_utils.commit_changes(commit_msg, description)
        if success:
            print("Done!")
        else:
            sys.exit(1)
    else:
        print("Commit cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
