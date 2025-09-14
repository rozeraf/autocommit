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
    """Shows a beautifully formatted commit preview with smart text wrapping"""
    
    def get_terminal_width():
        """Get terminal width or fallback to safe default"""
        try:
            import shutil
            width = shutil.get_terminal_size().columns
            # Leave some margin for terminal decorations
            return min(width - 2, 100)  # Cap at 100 for better readability, -2 for margin
        except Exception:  # Handle any potential exceptions more specifically
            return 78  # Safe fallback (80 - 2)
    
    def wrap_text(text: str, width: int, first_line: bool = False) -> list[str]:
        """Wrap text to fit within width, preserving words and handling bullet points"""
        import textwrap
        # For commit messages, try to keep first line shorter if it's long content
        target_width = width - 4  # Basic padding
        
        # Handle bullet points with proper indentation
        if text.lstrip().startswith('- '):
            indent = len(text) - len(text.lstrip())
            bullet_text = text[indent:]
            subsequent_indent = ' ' * (indent + 2)  # Align with text after bullet
            wrapped = textwrap.wrap(
                bullet_text,
                width=target_width - indent,
                initial_indent='',
                subsequent_indent=' ' * 2,  # Indent continuation lines
                break_long_words=True,
                break_on_hyphens=True
            )
            return [(' ' * indent + line) for line in wrapped]
        
        # Handle first line length for commit messages
        if first_line and len(text) > target_width - 10:
            target_width = min(target_width, 50)  # Limit first line to 50 chars
            
        return textwrap.wrap(text, width=target_width, break_long_words=True, break_on_hyphens=True)
    
    term_width = get_terminal_width()
    
    # Calculate word and char counts
    msg_words = len(commit_msg.split())
    desc_words = len(description.split()) if description else 0
    total_words = msg_words + desc_words
    total_chars = len(commit_msg) + (len(description) if description else 0)
    
    # We'll add the stats near the command preview at the end
    print()
    
    # Message box with adaptive width
    msg_lines = []
    first_line = True
    for line in commit_msg.split('\n'):
        wrapped = wrap_text(line, term_width, first_line)
        msg_lines.extend(wrapped)
        first_line = False
    
    # Calculate optimal width for commit message (shorter for long content)
    max_len = max(len(line) for line in msg_lines) if msg_lines else 0
    if len(msg_lines) > 2 or max_len > 50:  # If content is long
        width = min(max(40, min(max_len + 4, 60)), term_width)  # Limit width for readability
    else:
        width = min(max(max_len + 4, 40), term_width)
    
    # Top border with left-aligned "Message" label
    label = "Message"
    label_padding = " " * (4 - len(label) // 2)  # Center the label slightly
    top_border = f"╭─{label_padding}{label}─{'─' * (width - len(label) - 6)}╮"
    print(f"{Style.BRIGHT}{top_border}{Style.RESET_ALL}")
    
    # Content lines with proper padding
    for line in msg_lines:
        padded_line = line.ljust(width - 2)
        print(f"{Style.BRIGHT}│{padded_line}│{Style.RESET_ALL}")
    
    # Bottom border
    print(f"{Style.BRIGHT}╰{'─' * (width - 2)}╯{Style.RESET_ALL}")
    
    # Description box if present - label on left side of border with structured content
    if description:
        # Add elegant separator between message and description
        separator_width = min(50, term_width - 10)  # Keep separator reasonable
        half_sep = (separator_width - 3) // 2  # -3 for the center dot
        print(f"\n{' ' * ((term_width - separator_width) // 2)}"
              f"{Style.DIM}{'─' * half_sep}●{'─' * half_sep}{Style.RESET_ALL}\n")
        desc_lines = []
        
        # Structure description into sections
        changes = []
        details = []
        current_list = changes
        
        # Parse sections more intelligently
        for line in description.split('\n'):
            line = line.strip()
            if line.lower().startswith(('changes:', 'details:', 'impact:', 'notes:')):
                current_list = details
                continue
            if line:
                current_list.append(line)
        
        # Format main changes first with proper indentation
        if changes:
            desc_lines.append(f"{Fore.CYAN}Changes:{Style.RESET_ALL}")
            for line in changes:
                if not line.startswith('-'):
                    line = '- ' + line
                desc_lines.extend(wrap_text(line, term_width))
        
        # Then additional details if any
        if details:
            if changes:  # Add visual separator between sections
                desc_lines.append("")
            desc_lines.append(f"{Fore.CYAN}Details:{Style.RESET_ALL}")
            for line in details:
                if not line.startswith('-'):
                    line = '- ' + line
                desc_lines.extend(wrap_text(line, term_width))
        
        def strip_color_codes(text: str) -> str:
            """Remove color codes from string to get true visible length"""
            for code in [f"{Fore.CYAN}", f"{Fore.GREEN}", f"{Fore.YELLOW}", 
                        f"{Style.BRIGHT}", f"{Style.RESET_ALL}", f"{Style.DIM}"]:
                text = text.replace(code, "")
            return text
            
        # Calculate optimal width based on visible content length
        max_len = max(len(strip_color_codes(line)) for line in desc_lines) if desc_lines else 0
        width = min(max(max_len + 6, 45), term_width - 4)  # Add more padding, min 45 chars
        
        # Top border with centered "Description" label and accent color
        label = "Description"
        label_padding = " " * (4 - len(label) // 2)
        top_border = f"╭─{label_padding}{Fore.CYAN}{label}{Style.RESET_ALL}─{'─' * (width - len(label) - 6)}╮"
        print(f"{Style.BRIGHT}{top_border}{Style.RESET_ALL}")
        
        # Content lines with proper padding and color preservation
        for line in desc_lines:
            # Calculate correct padding based on visible length
            visible_len = len(strip_color_codes(line))
            padding = " " * (width - 2 - visible_len)
            print(f"{Style.BRIGHT}│ {line}{padding}│{Style.RESET_ALL}")
        
        # Bottom border
        print(f"{Style.BRIGHT}╰{'─' * (width - 2)}╯{Style.RESET_ALL}")
    
    # Show command preview and stats
    preview_width = min(term_width - 4, 100)  # Keep reasonable width with margin
    
    # Format stats with colors
    stats_parts = []
    if msg_words > 0:
        stats_parts.append(f"{Fore.GREEN}{msg_words}{Style.RESET_ALL} words")
    if desc_words > 0:
        stats_parts.append(f"+{Fore.CYAN}{desc_words}{Style.RESET_ALL} in desc")
    stats_parts.append(f"{Fore.BLUE}{total_chars}{Style.RESET_ALL} chars")
    stats = f"({', '.join(stats_parts)})"
    
    # Show length warning if needed
    if len(msg_lines[0]) > 50:
        print(f"\n{Fore.YELLOW}Note:{Style.RESET_ALL} First line is {len(msg_lines[0])} chars - consider keeping under 50 for readability")
    
    # Preview section with aligned stats
    print(f"\n{Fore.CYAN}Command:{Style.RESET_ALL} {stats}")
    commit_preview = f"git commit -m \"{commit_msg}\""
    if description:
        first_desc_line = description.split('\n')[0].strip()
        # Truncate long description lines nicely
        if len(first_desc_line) > 40:
            first_desc_line = first_desc_line[:37] + "..."
        commit_preview += f' -m "{first_desc_line}"'
    
    # Ensure preview doesn't exceed terminal width
    if len(commit_preview) > preview_width:
        visible_width = preview_width - 5  # Account for ellipsis
        commit_preview = commit_preview[:visible_width] + "..."
    
    print(f"  {commit_preview}")
    
    if skip_confirm:
        return True

    print()
    confirmation = f"\n{Fore.CYAN}Create this commit? {Style.RESET_ALL}"
    options = [
        f"{Fore.GREEN}[Y]{Style.RESET_ALL}es",
        f"{Fore.RED}[N]{Style.RESET_ALL}o",
        f"{Fore.YELLOW}[R]{Style.RESET_ALL}egenerate"
    ]
    print(confirmation + " / ".join(options) + ": ", end="")
    
    confirm = input().strip().lower()
    if confirm in ("r", "regenerate"):
        return None
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
            print(f"{Fore.RED}✗ FAIL: Not a Git repository.")
            all_passed = False
        else:
            print(f"{Fore.GREEN}✓ OK: Git repository found.")

        # 2. Check for API Key
        print("\n2. Checking for OPENROUTER_API_KEY...")
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print(f"{Fore.RED}✗ FAIL: OPENROUTER_API_KEY environment variable not set.")
            all_passed = False
        else:
            print(f"{Fore.GREEN}✓ OK: OPENROUTER_API_KEY is set.")

        # 3. Check git_utils.get_git_diff functionality
        print("\n3. Checking for staged files (via git_utils)...")
        staged_files, code = git_utils.run_command(["git", "diff", "--cached", "--name-only"])
        if code != 0:
            print(f"{Fore.RED}✗ FAIL: Command 'git diff --cached --name-only' failed.")
            all_passed = False
        else:
            print(f"{Fore.GREEN}✓ OK: Can check for staged files.")
            if not staged_files.strip():
                print(f"{Fore.YELLOW}NOTE: No files are currently staged.")

        # 4. Run unit tests
        print("\n4. Running unit tests with pytest...")
        _, code = git_utils.run_command(["pytest"], show_output=True)
        if code != 0:
            print(f"{Fore.RED}✗ FAIL: Unit test suite failed.{Style.RESET_ALL}")
            all_passed = False
        else:
            print(f"{Fore.GREEN}✓ OK: Unit test suite passed.{Style.RESET_ALL}")

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

    # Initialize spinner with consistent styling
    init_spinner = Halo(text=f"{Fore.CYAN}Initializing model{Style.RESET_ALL} '{model_name}'", spinner="dots")
    init_spinner.start()
    model_info = api_client.get_model_info(model_name)
    if model_info:
        model_details = f"({model_info.get('context_length', 'unknown')} tokens)"
        init_spinner.succeed(f"{Fore.GREEN}Model initialized{Style.RESET_ALL} {Fore.CYAN}{model_details}{Style.RESET_ALL}")
    else:
        init_spinner.fail(f"{Fore.RED}Failed to initialize model{Style.RESET_ALL}")
        sys.exit(1)

    # Check for staged changes with nice formatting
    diff = git_utils.get_git_diff()
    if not diff:
        print(f"\n{Fore.YELLOW}No staged changes found!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Tip:{Style.RESET_ALL} Stage your changes first with:")
        print(f"  git add <files>")
        print(f"  git add -p {Fore.CYAN}# to stage specific changes{Style.RESET_ALL}")
        sys.exit(1)

    while True:
        # Show AI thinking animation
        spinner = Halo(text=f"{Fore.CYAN}Analyzing changes{Style.RESET_ALL} and generating commit message", spinner="dots")
        spinner.start()
        result = api_client.generate_commit_message(diff, model_info)
        
        if result:
            commit_msg, description = result
            word_count = len(commit_msg.split()) + (len(description.split()) if description else 0)
            char_count = len(commit_msg) + (len(description) if description else 0)
            
            stats = f"[{word_count} words, {char_count} chars]"
            spinner.succeed(f"{Fore.GREEN}Commit message generated{Style.RESET_ALL} {Fore.CYAN}{stats}{Style.RESET_ALL}")
            
            if args.debug:
                logger.debug(f"Subject: '{commit_msg}'")
                if description:
                    logger.debug(f"Body: '{description[:100]}...'")
        else:
            spinner.fail(f"{Fore.RED}Failed to generate commit message{Style.RESET_ALL}")

        if not result:
            print(f"{Fore.RED}Try: python3 main.py --test-api")
            sys.exit(1)

        commit_msg, description = result

        if args.dry_run:
            print(f"\n{Style.BRIGHT}╭─ Dry Run: Commit Message ─╮")
            print(f"│ {Fore.YELLOW}Message:{Style.RESET_ALL} {Fore.GREEN}{commit_msg}")
            if description:
                print(f"│ {Fore.YELLOW}Description:{Style.RESET_ALL}\n{Fore.CYAN}{description}")
            print(f"{Style.BRIGHT}╰──────────────────────────╯")
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
