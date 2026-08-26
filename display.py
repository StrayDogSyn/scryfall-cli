"""
Output formatting for MyManaBox CLI.

No network calls. No user input. No business logic.
Every function takes data and prints formatted text.
Standard library only -- no rich, no tabulate.

None and empty-string values from card_data are handled here:
  - price_usd of None  -> prints as "n/a"
  - mana_cost of ""    -> prints as "n/a"
  - missing power/toughness -> row is omitted entirely
"""

_COL = 38  # column width for side-by-side display
_WRAP = 62  # oracle text wrap width


def _fmt_price(price: float | None) -> str:
    """Format a price value for display."""
    if price is None:
        return "n/a"
    return f"${price:.2f}"


def _fmt_field(value: str | None, fallback: str = "n/a") -> str:
    """Return value if non-empty and non-None, otherwise fallback."""
    if value is None or str(value).strip() == "":
        return fallback
    return str(value)


def _wrap_text(text: str, width: int = _WRAP) -> list[str]:
    """Wrap text to width, returning a list of lines."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            if current:
                lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    return lines


def print_card_detail(summary: dict) -> None:
    """Print one card as an aligned, labeled block.

    Args:
        summary: Dict from card_data.extract_card_summary().
    """
    name = summary.get("name", "Unknown")
    bar = "-" * max(len(name) + 4, 40)

    print()
    print(f"  {name}")
    print(f"  {bar}")
    print(f"  {'Mana Cost':<14} {_fmt_field(summary.get('mana_cost'))}")
    print(f"  {'Type':<14} {_fmt_field(summary.get('type_line'))}")
    print(f"  {'Rarity':<14} {_fmt_field(summary.get('rarity'))}")
    print(f"  {'Set':<14} {_fmt_field(summary.get('set_name'))}")
    print(f"  {'Released':<14} {_fmt_field(summary.get('released_at'))}")
    print(f"  {'Price (USD)':<14} {_fmt_price(summary.get('price_usd'))}")

    if "power" in summary and "toughness" in summary:
        print(f"  {'P/T':<14} {summary['power']}/{summary['toughness']}")

    oracle = summary.get("oracle_text", "")
    if oracle:
        print()
        for line in _wrap_text(oracle):
            print(f"  {line}")

    print(f"\n  {'Artist':<14} {_fmt_field(summary.get('artist'))}")
    print()


def print_comparison(comparison: dict) -> None:
    """Print two cards in aligned side-by-side columns.

    Args:
        comparison: Dict with 'a' and 'b' keys from card_data.compare_cards().
    """
    a = comparison.get("a", {})
    b = comparison.get("b", {})

    divider = f"  {'-' * (_COL + 3 + _COL)}"
    header = f"  {'CARD A':<{_COL}} | CARD B"
    print()
    print(header)
    print(divider)

    fields = [
        ("Name",        "name",      _fmt_field),
        ("Mana Cost",   "mana_cost", _fmt_field),
        ("Type",        "type_line", _fmt_field),
        ("Rarity",      "rarity",    _fmt_field),
        ("Set",         "set_name",  _fmt_field),
        ("Price (USD)", "price_usd", _fmt_price),
    ]

    for label, key, fmt in fields:
        val_a = fmt(a.get(key))
        val_b = fmt(b.get(key))
        cell_a = f"{label}: {val_a}"
        cell_b = f"{label}: {val_b}"
        print(f"  {cell_a:<{_COL}} | {cell_b}")

    # P/T row: show if either card has it
    if "power" in a or "power" in b:
        pt_a = f"{a['power']}/{a['toughness']}" if "power" in a else "n/a"
        pt_b = f"{b['power']}/{b['toughness']}" if "power" in b else "n/a"
        cell_a = f"P/T: {pt_a}"
        cell_b = f"P/T: {pt_b}"
        print(f"  {cell_a:<{_COL}} | {cell_b}")

    print()


def print_card_list(cards: list[dict]) -> None:
    """Print a numbered, column-aligned list of cards.

    Accepts raw Scryfall card dicts, not summaries. The list view
    shows only the fields useful for scanning a result set.

    Args:
        cards: List of raw Scryfall card dicts.
    """
    if not cards:
        print("\n  No cards to display.\n")
        return

    print()
    print(f"  {'#':<4} {'Name':<35} {'Type':<28} {'Rarity':<10} {'Price'}")
    print(f"  {'-' * 90}")

    for i, card in enumerate(cards, start=1):
        name = (card.get("name") or "Unknown")[:34]
        type_line = (card.get("type_line") or "")[:27]
        rarity = (card.get("rarity") or "").capitalize()[:9]
        prices = card.get("prices") or {}
        usd = prices.get("usd")
        price = f"${float(usd):.2f}" if usd else "n/a"
        print(f"  {i:<4} {name:<35} {type_line:<28} {rarity:<10} {price}")

    print(f"\n  {len(cards)} result(s) returned.\n")


def print_error(message: str) -> None:
    """Print a user-facing error in a consistent style.

    Args:
        message: Plain-language error description. No tracebacks here.
    """
    print(f"\n  Error: {message}\n")
