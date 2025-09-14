#!/usr/bin/env python3
"""
Git Auto Commit - automatic commit creation using AI

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

import argparse
import logging
import os
import sys
import time
from typing import Optional

from colorama import Fore, Style
from colorama import init as colorama_init
from dotenv import load_dotenv

from src import api_client, git_utils

load_dotenv()


def setup_logging(debug: bool = False):
    """Configure logging based on debug flag"""
    level = logging.DEBUG if debug else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" if debug else "%(message)s"

    # Reset any existing handlers
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

logger = logging.getLogger(__name__)


def show_confirmation(commit_msg: str, description: str | None, skip_confirm: bool = False) -> bool:
    """Shows confirmation before committing"""
    print(f"\n{Style.BRIGHT}--- Commit Preview ---{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Message:{Style.RESET_ALL} {Fore.GREEN}{commit_msg}")
    if description:
        print(f"{Fore.YELLOW}Description:{Style.RESET_ALL}\n{Fore.CYAN}{description}")
    print(f"{Style.BRIGHT}-----------------------------")

    if skip_confirm:
        return True

    confirm = input("Create commit? [Y/n]: ").lower()
    return confirm in ("", "y", "yes")


def main():
    """Main function"""
    colorama_init(autoreset=True)
    parser = argparse.ArgumentParser(description="Git Auto Commit - AI-powered commit message generation")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    parser.add_argument("--dry-run", action="store_true", help="Generate and print commit message without committing")
    parser.add_argument("--test-api", action="store_true", help="Test API connection")
    parser.add_argument("--test", action="store_true", help="Run a series of self-tests to check application health")
    parser.add_argument("--model", help="Override AI model from .env file (e.g., anthropic/claude-3.5-sonnet)")
    args = parser.parse_args()

    setup_logging(args.debug)

    if args.test_api:
        api_client.test_api_key()
        return

    if args.test:
        print("Running application self-tests...")
        all_passed = True

        # 1. Check for git repo
        print("\n1. Checking for Git repository...")
        _, code = git_utils.run_command(["git", "rev-parse", "--git-dir"])
        if code != 0:
            print(f"{Fore.RED}FAIL: Not a Git repository.")
            all_passed = False
        else:
            print(f"{Fore.GREEN}OK: Git repository found.")

        # 2. Check for API Key
        print("\n2. Checking for OPENROUTER_API_KEY...")
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print(f"{Fore.RED}FAIL: OPENROUTER_API_KEY environment variable not set.")
            all_passed = False
        else:
            print(f"{Fore.GREEN}OK: OPENROUTER_API_KEY is set.")

        # 3. Check git_utils.get_git_diff functionality
        print("\n3. Checking for staged files (via git_utils)...")
        staged_files, code = git_utils.run_command(["git", "diff", "--cached", "--name-only"])
        if code != 0:
            print(f"{Fore.RED}FAIL: Command 'git diff --cached --name-only' failed.")
            all_passed = False
        else:
            print(f"{Fore.GREEN}OK: Can check for staged files.")
            if not staged_files.strip():
                print(f"{Fore.YELLOW}NOTE: No files are currently staged.")

        if all_passed:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}All self-tests passed!{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"\n{Fore.RED}{Style.BRIGHT}Some self-tests failed.{Style.RESET_ALL}")
            sys.exit(1)

    if args.debug:
        logger.info("Git Auto Commit: generating commit for staged files...")

    # Check if we're in a git repository
    _, code = git_utils.run_command(["git", "rev-parse", "--git-dir"])
    if code != 0:
        print(f"{Fore.RED}Error: git repository not found.")
        sys.exit(1)

    model_name = args.model or os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    if args.debug:
        logger.debug(f"Using model: {model_name}")
    model_info = api_client.get_model_info(model_name)

    diff = git_utils.get_git_diff()
    if not diff:
        sys.exit(1)

    while True:
        result = api_client.generate_commit_message(diff, model_info)
        if not result:
            print(f"{Fore.RED}Failed to generate commit message.")
            print(f"{Fore.RED}Try: python3 main.py --test-api")
            sys.exit(1)

        commit_msg, description = result

        if args.dry_run:
            print(f"\n{Style.BRIGHT}--- Dry Run: Commit Message ---{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Message:{Style.RESET_ALL} {Fore.GREEN}{commit_msg}")
            if description:
                print(f"{Fore.YELLOW}Description:{Style.RESET_ALL}\n{Fore.CYAN}{description}")
            print(f"{Style.BRIGHT}---------------------------------")
            sys.exit(0)

        if show_confirmation(commit_msg, description, args.yes):
            success = git_utils.commit_changes(commit_msg, description)
            if success:
                print(f"{Fore.GREEN}Done!")
            else:
                sys.exit(1)
            break
        else:
            retry_input = input("Retry generating commit message? [y/N]: ").lower()
            if retry_input in ("y", "yes"):
                print(f"{Fore.YELLOW}Regenerating commit message...")
                continue
            else:
                print(f"{Fore.YELLOW}Commit cancelled.")
                sys.exit(0)


if __name__ == "__main__":
    main()
