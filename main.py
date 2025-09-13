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
from typing import Optional

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
    logger.info("\n--- Commit Preview ---")
    logger.info(f"Message: {commit_msg}")
    if description:
        logger.info(f"Description:\n{description}")
    logger.info("-----------------------------")
    
    if skip_confirm:
        return True
    
    confirm = input("Create commit? [Y/n]: ").lower()
    return confirm in ("", "y", "yes")


def main():
    parser = argparse.ArgumentParser(description="Git Auto Commit - AI-powered commit message generation")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    parser.add_argument("--test-api", action="store_true", help="Test API connection")
    parser.add_argument("--model", help="Override AI model from .env file (e.g., anthropic/claude-3.5-sonnet)")
    args = parser.parse_args()
    
    setup_logging(args.debug)
    
    if args.test_api:
        api_client.test_api_key()
        return
    
    if args.debug:
        logger.info("Git Auto Commit: generating commit for staged files...")
    
    # Check if we're in a git repository
    _, code = git_utils.run_command(["git", "rev-parse", "--git-dir"])
    if code != 0:
        logger.error("Error: git repository not found.")
        sys.exit(1)

    model_name = args.model or os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    if args.debug:
        logger.debug(f"Using model: {model_name}")
    model_info = api_client.get_model_info(model_name)
    
    diff = git_utils.get_git_diff()
    if not diff:
        sys.exit(1)
    
    result = api_client.generate_commit_message(diff, model_info)
    if not result:
        logger.error("Failed to generate commit message.")
        logger.error("Try: python3 main.py --test-api")
        sys.exit(1)
    
    commit_msg, description = result

    if show_confirmation(commit_msg, description, args.yes):
        success = git_utils.commit_changes(commit_msg, description)
        if success:
            logger.info("Done!")
        else:
            sys.exit(1)
    else:
        logger.info("Commit cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
