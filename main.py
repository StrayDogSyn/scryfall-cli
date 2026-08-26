"""
MyManaBox CLI -- Magic: The Gathering card lookup via Scryfall.

Orchestration only. This module calls into api_client, card_data,
and display. It contains no request logic, no parsing, and no formatting.

Commands:
  lookup <name>             Look up one card by name (fuzzy matching)
  compare <name_a> <name_b> Compare two cards side by side
  search <query>            Search cards using Scryfall syntax

Examples:
  python main.py lookup "lightning bolt"
  python main.py lookup "sol ring"
  python main.py compare "black lotus" "mox pearl"
  python main.py search "t:goblin c:r"
"""

import argparse
import sys

import requests

# Windows consoles default to cp1252; Scryfall artist names may contain
# accented characters. Reconfigure stdout to UTF-8 so they print instead
# of crashing. errors='replace' ensures robustness on terminals that truly
# cannot handle UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import display
from api_client import CardNotFoundError, fetch_card_by_name, search_cards
from card_data import compare_cards, extract_card_summary


def _validate_nonempty(value: str, label: str) -> bool:
    """Return True when value is non-empty; print an error and return False otherwise."""
    if not value or not value.strip():
        display.print_error(f"{label} cannot be empty.")
        return False
    return True


def cmd_lookup(args: argparse.Namespace) -> int:
    """Fetch one card by name and print its detail block."""
    name = args.name
    if not _validate_nonempty(name, "Card name"):
        return 1

    try:
        card = fetch_card_by_name(name)
        summary = extract_card_summary(card)
        display.print_card_detail(summary)
        return 0
    except CardNotFoundError as exc:
        if exc.ambiguous:
            display.print_error(
                f'"{name}" matched several cards. Try a more specific name '
                f'or add a set code (e.g. "lightning bolt" -> "lightning bolt lea").'
            )
        else:
            display.print_error(f'No card found for "{name}".')
        return 1
    except requests.exceptions.RequestException as exc:
        display.print_error(str(exc))
        return 1


def cmd_compare(args: argparse.Namespace) -> int:
    """Fetch two cards by name and print them side by side."""
    name_a, name_b = args.name_a, args.name_b
    if not _validate_nonempty(name_a, "First card name"):
        return 1
    if not _validate_nonempty(name_b, "Second card name"):
        return 1

    try:
        card_a = fetch_card_by_name(name_a)
        card_b = fetch_card_by_name(name_b)
        comparison = compare_cards(card_a, card_b)
        display.print_comparison(comparison)
        return 0
    except CardNotFoundError as exc:
        if exc.ambiguous:
            display.print_error("One of those names matched several cards. Be more specific.")
        else:
            display.print_error("One or both cards were not found.")
        return 1
    except requests.exceptions.RequestException as exc:
        display.print_error(str(exc))
        return 1


def cmd_search(args: argparse.Namespace) -> int:
    """Search for cards and print the result list."""
    query = args.query
    if not _validate_nonempty(query, "Search query"):
        return 1

    try:
        cards = search_cards(query)
        display.print_card_list(cards)
        return 0
    except CardNotFoundError:
        display.print_error(f'No cards found for query: "{query}".')
        return 1
    except requests.exceptions.RequestException as exc:
        display.print_error(str(exc))
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="mymanabox",
        description="MyManaBox: Magic: The Gathering card lookup via Scryfall",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py lookup \"lightning bolt\"\n"
            "  python main.py compare \"black lotus\" \"mox pearl\"\n"
            "  python main.py search \"t:goblin c:r\"\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    lookup_p = subparsers.add_parser(
        "lookup",
        help="Look up a card by name (fuzzy matching supported)",
    )
    lookup_p.add_argument("name", help='Card name, e.g. "lightning bolt"')

    compare_p = subparsers.add_parser(
        "compare",
        help="Compare two cards side by side",
    )
    compare_p.add_argument("name_a", help="First card name")
    compare_p.add_argument("name_b", help="Second card name")

    search_p = subparsers.add_parser(
        "search",
        help="Search cards using Scryfall syntax",
    )
    search_p.add_argument(
        "query",
        help='Scryfall query, e.g. "t:goblin c:r" or "set:lea"',
    )

    return parser


def main() -> int:
    """Parse arguments and dispatch to the appropriate command handler.

    Returns 0 on success, 1 on any error. Exit codes propagate to the shell
    so scripts can detect failures without parsing output.
    """
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "lookup": cmd_lookup,
        "compare": cmd_compare,
        "search": cmd_search,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
