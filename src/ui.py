"""
UI utilities for Git Auto Commit

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
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)
console = Console()


def show_confirmation(
    commit_msg: str, description: str | None, skip_confirm: bool = False
) -> bool | None:
    """Shows a beautifully formatted commit preview using rich library

    Returns:
        True: User confirmed
        False: User declined
        None: User wants to regenerate
    """

    # Calculate stats
    msg_words = len(commit_msg.split())
    desc_words = len(description.split()) if description else 0
    total_chars = len(commit_msg) + (len(description) if description else 0)

    print()

    # Create message panel
    message_text = Text(commit_msg)
    message_panel = Panel(
        message_text,
        title="[cyan]Message[/cyan]",
        title_align="left",
        border_style="bright_white",
        expand=False,
        padding=(0, 1),
    )

    console.print(message_panel)

    # Create description panel if present
    if description:
        print()

        # Parse and format description
        desc_lines = _format_description(description)

        description_text = Text.from_markup("\n".join(desc_lines))
        description_panel = Panel(
            description_text,
            title="[cyan]Description[/cyan]",
            title_align="left",
            border_style="bright_white",
            expand=False,
            padding=(0, 1),
        )

        console.print(description_panel)

    # Show stats and warnings
    _show_stats_and_warnings(msg_words, desc_words, total_chars, commit_msg)

    # Show command preview
    _show_command_preview(commit_msg, description)

    if skip_confirm:
        return True

    return _get_user_confirmation()


def _format_description(description: str) -> list[str]:
    """Formats the commit description into structured sections with headers."""
    desc_lines = []
    changes = []
    details = []
    current_list = changes

    for line in description.split("\n"):
        line = line.strip()
        if line.lower().startswith(("changes:", "details:", "impact:", "notes:")):
            current_list = details
            continue
        if line:
            current_list.append(line)

    # Format sections
    if changes:
        desc_lines.append("[cyan]Changes:[/cyan]")
        for line in changes:
            if not line.startswith("-"):
                line = "- " + line
            desc_lines.append(line)

    if details:
        if changes:
            desc_lines.append("")  # Add separator
        desc_lines.append("[cyan]Details:[/cyan]")
        for line in details:
            if not line.startswith("-"):
                line = "- " + line
            desc_lines.append(line)

    return desc_lines


def _show_stats_and_warnings(
    msg_words: int, desc_words: int, total_chars: int, commit_msg: str
):
    """Show statistics and warnings about commit message"""
    # Format stats
    stats_parts = []
    if msg_words > 0:
        stats_parts.append(f"[green]{msg_words}[/green] words")
    if desc_words > 0:
        stats_parts.append(f"+[cyan]{desc_words}[/cyan] in desc")
    stats_parts.append(f"[blue]{total_chars}[/blue] chars")

    stats = f"({', '.join(stats_parts)})"

    # Show length warning if needed
    first_line_length = len(commit_msg.split("\n")[0])
    if first_line_length > 50:
        console.print(
            f"\n[yellow]Note:[/yellow] First line is {first_line_length} chars - consider keeping under 50 for readability"
        )

    console.print(f"\n[cyan]Command:[/cyan] {stats}")


def _show_command_preview(commit_msg: str, description: str | None):
    """Show git command preview"""
    commit_preview = f'git commit -m "{commit_msg}"'

    if description:
        first_desc_line = description.split("\n")[0].strip()
        if len(first_desc_line) > 40:
            first_desc_line = first_desc_line[:37] + "..."
        commit_preview += f' -m "{first_desc_line}"'

    # Truncate if too long
    terminal_width = console.size.width
    preview_width = min(terminal_width - 4, 100)
    if len(commit_preview) > preview_width:
        visible_width = preview_width - 5
        commit_preview = commit_preview[:visible_width] + "..."

    console.print(f"  {commit_preview}")


def _get_user_confirmation() -> bool | None:
    """Get user confirmation for commit"""
    console.print()

    prompt_text = Text()
    prompt_text.append("Create this commit? ", style="cyan")
    prompt_text.append("[Y]", style="green bold")
    prompt_text.append("es / ", style="white")
    prompt_text.append("[N]", style="red bold")
    prompt_text.append("o / ", style="white")
    prompt_text.append("[R]", style="yellow bold")
    prompt_text.append("egenerate: ", style="white")

    console.print(prompt_text, end="")

    confirm = input().strip().lower()
    if confirm in ("r", "regenerate"):
        return None
    return confirm in ("", "y", "yes")


def show_error(message: str):
    """Show error message with consistent styling"""
    console.print(f"[red]Error:[/red] {message}")


def show_warning(message: str):
    """Show warning message with consistent styling"""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def show_success(message: str):
    """Show success message with consistent styling"""
    console.print(f"[green]{message}[/green]")


def show_info(message: str):
    """Show info message with consistent styling"""
    console.print(f"[cyan]{message}[/cyan]")


def show_tip(message: str):
    """Show tip message with consistent styling"""
    console.print(f"[cyan]Tip:[/cyan] {message}")


def show_provider_tests(results: dict[str, bool]):
    """Show provider test results in a formatted way"""
    console.print("\nRunning provider connectivity tests...")
    all_passed = True
    for name, passed in results.items():
        if passed:
            console.print(f"[green]✓ {name}:[/green] Connection successful")
        else:
            console.print(f"[red]✗ {name}:[/red] Connection failed")
            all_passed = False
    if all_passed:
        console.print("\n[green bold]All providers are reachable![/green bold]")
    else:
        console.print("\n[red bold]Some providers are not reachable.[/red bold]")


def show_test_results(results: list[dict]):
    """Show test results in a formatted way"""
    console.print("\nRunning application self-tests...")

    all_passed = True

    for i, test in enumerate(results, 1):
        console.print(f"\n{i}. {test['name']}...")

        if test["passed"]:
            console.print(f"[green]✓ OK:[/green] {test['message']}")
        else:
            console.print(f"[red]✗ FAIL:[/red] {test['message']}")
            all_passed = False

        if test.get("note"):
            console.print(f"[yellow]NOTE:[/yellow] {test['note']}")

    if all_passed:
        console.print("\n[green bold]All self-tests passed![/green bold]")
    else:
        console.print("\n[red bold]Some self-tests failed.[/red bold]")

    return all_passed
