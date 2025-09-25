#!/usr/bin/env python3
"""
Git Auto Commit - automatic commit creation using AI
"""

import argparse
import logging
import os
import sys
from dataclasses import asdict

from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv
from halo import Halo

from src.api.factory import ProviderFactory
from src.api.commit_generator import CommitGenerator
from src.api.manager import AIProviderManager
from src import git_utils, ui
from src.config.loader import get_config
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
    logging.basicConfig(
        level=level, format=format_str, handlers=[logging.StreamHandler(sys.stdout)]
    )


logger = logging.getLogger(__name__)


def main():
    """Main function"""
    colorama_init(autoreset=True)
    config = get_config()
    manager = AIProviderManager(config)

    parser = argparse.ArgumentParser(description="AI-powered commit message generation")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and print commit message without committing",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a series of self-tests to check application health",
    )
    parser.add_argument(
        "--test-providers",
        action="store_true",
        help="Test connection for all configured providers",
    )
    parser.add_argument(
        "--list-providers", action="store_true", help="List available AI providers"
    )
    parser.add_argument(
        "--provider-info",
        help="Show detailed information for a specific provider",
        metavar="PROVIDER_NAME",
    )
    parser.add_argument(
        "--provider",
        help=f"Force a specific provider (e.g., {', '.join(ProviderFactory.get_available_providers())})",
    )
    parser.add_argument("--model", help="Override AI model from config")
    parser.add_argument(
        "-c", "--context", help="Provide a preset context for the commit"
    )
    parser.add_argument("-i", "--hint", help="Provide a custom hint to the AI model")
    parser.add_argument(
        "--auto-context",
        action="store_true",
        default=config.context.auto_detect,
        help="Enable auto-detection of context",
    )

    args = parser.parse_args()
    setup_logging(args.debug)

    if args.provider_info:
        provider_name = args.provider_info
        try:
            provider = manager._get_or_create_provider(provider_name)
            model_info = provider.get_model_info()
            env_vars = provider.get_required_env_vars()
            provider_config = config.ai.providers.get(provider_name)

            ui.show_provider_info(
                provider_name,
                model_info,
                env_vars,
                asdict(provider_config) if provider_config else None,
            )
            sys.exit(0)
        except ValueError as e:
            ui.show_error(str(e))
            sys.exit(1)

    if args.test:
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
                    else "OPENROUTER_API_KEY not set"
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
                "message": "Can check for staged files",
                "note": (
                    "No files are currently staged"
                    if not staged_files.strip()
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

    if args.list_providers:
        ui.show_info("Available AI Providers:")
        for provider_name in ProviderFactory.get_available_providers():
            print(f"- {provider_name}")
        sys.exit(0)

    if args.debug:
        logger.info("Git Auto Commit: generating commit for staged files...")

    if git_utils.run_command(["git", "rev-parse", "--git-dir"])[1] != 0:
        ui.show_error("Not a git repository.")
        sys.exit(1)

    diff = git_utils.get_git_diff()
    if not diff:
        ui.show_warning("No staged changes found!")
        sys.exit(1)

    if args.provider:
        provider = manager._get_or_create_provider(args.provider)
        # Когда выбран провайдер через флаг, используем его имя прямо
        provider_name = args.provider
    else:
        provider = manager.get_provider_for_context(diff)
        # Попытка получить имя провайдера из объекта; запасные варианты на случай разных реализаций
        provider_name = (
            getattr(provider, "name", None)
            or getattr(provider, "provider_name", None)
            or provider.__class__.__name__
        )

    if provider is None:
        ui.show_error("No AI provider could be initialized.")
        sys.exit(1)

    # Override model from command line if provided
    if args.model:
        # защита на случай, если у провайдера нет атрибута model
        if hasattr(provider, "model"):
            provider.model = args.model
        else:
            logger.warning(
                "Selected provider does not support overriding model via --model"
            )

    if args.test_providers:
        results = manager.test_all_providers()
        ui.show_provider_tests(results)
        sys.exit(0)

    init_spinner = Halo(
        text=f"{Fore.CYAN}Initializing provider '{provider_name}'{Style.RESET_ALL}",
        spinner="dots",
    )
    init_spinner.start()
    model_info = provider.get_model_info()
    if model_info:
        init_spinner.succeed(
            f"{Fore.GREEN}Provider initialized with model '{model_info.name}'.{Style.RESET_ALL}"
        )
    else:
        init_spinner.fail(f"{Fore.RED}Failed to initialize provider.{Style.RESET_ALL}")
        sys.exit(1)

    diff = git_utils.get_git_diff()
    if not diff:
        ui.show_warning("No staged changes found!")
        sys.exit(1)

    context_hints = []
    if args.hint:
        context_hints.append(args.hint)
    elif args.context:
        context_hints.append(args.context.lower())
    elif args.auto_context:
        diff_parser = DiffParser()
        smart_diff = diff_parser.parse_diff(
            diff, model_info.context_length if model_info else None
        )
        detector = ContextDetector(config.context.wip_keywords)
        context_hints.extend(detector.detect(diff, smart_diff.stats))

    prompt_context = (
        ", ".join(sorted(list(set(context_hints)))) if context_hints else None
    )

    generator = CommitGenerator(provider)

    while True:
        spinner = Halo(
            text=f"{Fore.CYAN}Generating commit message...{Style.RESET_ALL}",
            spinner="dots",
        )
        spinner.start()

        result = generator.generate(diff, prompt_context)

        if result:
            spinner.succeed(f"{Fore.GREEN}Commit message generated.{Style.RESET_ALL}")
        else:
            spinner.fail(
                f"{Fore.RED}Failed to generate commit message.{Style.RESET_ALL}"
            )
            sys.exit(1)

        if args.dry_run:
            ui.show_info("Dry Run: Commit Message")
            ui.show_success(f"Message: {result.subject}")
            if result.description:
                ui.show_info(f"Description:\n{result.description}")
            sys.exit(0)

        confirmation = ui.show_confirmation(
            result.subject, result.description, args.yes
        )

        if confirmation is True:
            if git_utils.commit_changes(result.subject, result.description):
                ui.show_success("Done!")
            else:
                sys.exit(1)
            break
        elif confirmation is None:
            ui.show_info("Regenerating commit message...")
            continue
        else:
            ui.show_info("Commit cancelled.")
            sys.exit(0)


if __name__ == "__main__":
    main()
