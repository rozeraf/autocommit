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

from colorama import Fore, Style
from colorama import init as colorama_init
from dotenv import load_dotenv
from halo import Halo

from src import api, git_utils, ui
from src.config import get_config
from src.context.detector import ContextDetector
from src.parsers.diff_parser import DiffParser

load_dotenv()


def setup_logging(debug: bool = False):
    """Configure logging based on debug flag"""
    level = logging.DEBUG if debug else logging.INFO
    format_str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        if debug
        else "%(message)s"
    )

    # Reset any existing handlers
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    logging.basicConfig(
        level=level, format=format_str, handlers=[logging.StreamHandler(sys.stdout)]
    )


logger = logging.getLogger(__name__)


def main():
    """Main function"""
    colorama_init(autoreset=True)
    parser = argparse.ArgumentParser(
        description="Git Auto Commit - AI-powered commit message generation"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and print commit message without committing",
    )
    parser.add_argument("--test-api", action="store_true", help="Test API connection")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a series of self-tests to check application health",
    )
    parser.add_argument(
        "--model",
        help="Override AI model from .env file (e.g., anthropic/claude-3.5-sonnet)",
    )
    parser.add_argument(
        "-c", "--context", help="Provide a preset context for the commit (e.g., 'wip')"
    )
    parser.add_argument("-i", "--hint", help="Provide a custom hint to the AI model")
    parser.add_argument(
        "--auto-context",
        action="store_true",
        default=True,
        help="Enable auto-detection of context from changes (default: True)",
    )
    args = parser.parse_args()

    setup_logging(args.debug)

    if args.test:
        # Prepare test results
        test_results = []

        # 1. Check for git repo
        _, code = git_utils.run_command(["git", "rev-parse", "--git-dir"])
        test_results.append(
            {
                "name": "Checking for Git repository",
                "passed": code == 0,
                "message": (
                    "Git repository found" if code == 0 else "Not a Git repository"
                ),
            }
        )

        # 2. Check for API Key
        api_key = os.getenv("OPENROUTER_API_KEY")
        test_results.append(
            {
                "name": "Checking for OPENROUTER_API_KEY",
                "passed": bool(api_key),
                "message": (
                    "OPENROUTER_API_KEY is set"
                    if api_key
                    else "OPENROUTER_API_KEY environment variable not set"
                ),
            }
        )

        # 3. Check git_utils.get_git_diff functionality
        staged_files, code = git_utils.run_command(
            ["git", "diff", "--cached", "--name-only"]
        )
        test_results.append(
            {
                "name": "Checking for staged files",
                "passed": code == 0,
                "message": (
                    "Can check for staged files"
                    if code == 0
                    else "Command 'git diff --cached --name-only' failed"
                ),
                "note": (
                    "No files are currently staged"
                    if code == 0 and not staged_files.strip()
                    else None
                ),
            }
        )

        # 4. Run unit tests
        _, code = git_utils.run_command(["pytest"], show_output=True)
        test_results.append(
            {
                "name": "Running unit tests with pytest",
                "passed": code == 0,
                "message": (
                    "Unit test suite passed" if code == 0 else "Unit test suite failed"
                ),
            }
        )

        all_passed = ui.show_test_results(test_results)
        sys.exit(0 if all_passed else 1)

    if args.debug:
        logger.info("Git Auto Commit: generating commit for staged files...")

    # Check if we're in a git repository
    _, code = git_utils.run_command(["git", "rev-parse", "--git-dir"])
    if code != 0:
        ui.show_error("git repository not found.")
        sys.exit(1)

    config = get_config()
    model_name = (
        args.model
        or config.ai.model
        or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3.1:free")
    )
    if args.debug:
        logger.debug(f"Using model: {model_name}")

    try:
        with api.OpenRouterClient(model=model_name) as client:
            if args.test_api:
                client.test_api_key()
                return

            # Initialize spinner with consistent styling
            init_spinner = Halo(
                text=f"{Fore.CYAN}Initializing model{Style.RESET_ALL} '{model_name}'",
                spinner="dots",
            )
            init_spinner.start()

            model_info = client.get_model_info(model_name)
            if model_info:
                model_details = f"({model_info.context_length or 'unknown'} tokens)"
                init_spinner.succeed(
                    f"{Fore.GREEN}Model initialized{Style.RESET_ALL} {Fore.CYAN}{model_details}{Style.RESET_ALL}"
                )
            else:
                init_spinner.fail(
                    f"{Fore.RED}Failed to initialize model{Style.RESET_ALL}"
                )
                sys.exit(1)

            # Check for staged changes with nice formatting
            diff = git_utils.get_git_diff()
            if not diff:
                ui.show_warning("No staged changes found!")
                ui.show_tip("Stage your changes first with: git add <files>")
                ui.show_info("git add -p # to stage specific changes")
                sys.exit(1)

            # Determine context based on priority: hint > context > auto-context
            context_hints = []
            if args.hint:
                context_hints.append(args.hint)
            elif args.context:
                context_hints.append(args.context.lower())
            elif config.context.auto_detect and args.auto_context:
                diff_parser = DiffParser()
                smart_diff = diff_parser.parse_diff(
                    diff, model_info.context_length if model_info else None
                )
                detector = ContextDetector(config.context.wip_keywords)
                context_hints.extend(detector.detect(diff, smart_diff.stats))

            prompt_context_str = None
            if context_hints:
                prompt_context_str = (
                    f"Context hints: {', '.join(sorted(list(set(context_hints))))}"
                )

            if prompt_context_str and args.debug:
                logger.debug(f"Using context: {prompt_context_str}")

            while True:
                # Show AI thinking animation
                spinner = Halo(
                    text=f"{Fore.CYAN}Analyzing changes{Style.RESET_ALL} and generating commit message",
                    spinner="dots",
                )
                spinner.start()
                result = client.generate_commit_message(
                    diff, model_info, prompt_context=prompt_context_str
                )

                if result:
                    commit_msg = result.subject
                    description = result.description
                    word_count = len(commit_msg.split()) + (
                        len(description.split()) if description else 0
                    )
                    char_count = len(commit_msg) + (
                        len(description) if description else 0
                    )

                    stats = f"[{word_count} words, {char_count} chars]"
                    spinner.succeed(
                        f"{Fore.GREEN}Commit message generated{Style.RESET_ALL} {Fore.CYAN}{stats}{Style.RESET_ALL}"
                    )

                    if args.debug:
                        logger.debug(f"Subject: '{commit_msg}'")
                        if description:
                            logger.debug(f"Body: '{description[:100]}...'")
                else:
                    spinner.fail(
                        f"{Fore.RED}Failed to generate commit message{Style.RESET_ALL}"
                    )

                if not result:
                    ui.show_error("Try: python3 main.py --test-api")
                    sys.exit(1)

                commit_msg = result.subject
                description = result.description

                if args.dry_run:
                    ui.show_info("Dry Run: Commit Message")
                    ui.show_success(f"Message: {commit_msg}")
                    if description:
                        ui.show_info(f"Description:\n{description}")
                    sys.exit(0)

                confirmation = ui.show_confirmation(commit_msg, description, args.yes)

                if confirmation is True:
                    # User confirmed - create commit
                    success = git_utils.commit_changes(commit_msg, description)
                    if success:
                        ui.show_success("Done!")
                    else:
                        sys.exit(1)
                    break
                elif confirmation is None:
                    # User wants to regenerate - continue loop
                    ui.show_info("Regenerating commit message...")
                    continue
                else:
                    # User declined - exit
                    ui.show_info("Commit cancelled.")
                    sys.exit(0)
    except (ValueError, ConnectionError) as e:
        ui.show_error(f"Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
