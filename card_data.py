"""
Card data processing for MyManaBox.

This module transforms raw Scryfall dicts into clean Python data.
No network calls. No printing. Pure data transformation.

Every field access uses .get() with an explicit default because the
Scryfall API contains genuinely absent fields, not just None values:
  - Creatures have 'power' and 'toughness'; Sol Ring does not.
  - Arena-only cards often have no 'usd' price at all.
  - 'mana_cost' is an empty string (not null) on lands and some artifacts.
"""


def extract_card_summary(card: dict) -> dict:
    """Extract display-ready fields from a raw Scryfall card dict.

    Always included: name, mana_cost, cmc, type_line, rarity, set_name,
                     oracle_text, artist, released_at, price_usd.
    Conditional:     power and toughness (present on creature cards only).

    Args:
        card: Raw Scryfall card object dict.

    Returns:
        Flat dict with normalized fields ready for the display layer.
    """
    summary = {
        "name": card.get("name", "Unknown"),
        "mana_cost": card.get("mana_cost", ""),       # "" on Sol Ring, lands
        "cmc": card.get("cmc", 0),
        "type_line": card.get("type_line", "Unknown"),
        "rarity": (card.get("rarity") or "unknown").capitalize(),
        "set_name": card.get("set_name", "Unknown"),
        "oracle_text": card.get("oracle_text", ""),
        "artist": card.get("artist", "Unknown"),
        "released_at": card.get("released_at", "Unknown"),
        "price_usd": get_price(card),
    }

    # power and toughness are absent entirely on non-creatures; do not default
    # them to a placeholder -- their absence is meaningful to display.
    if card.get("power") is not None:
        summary["power"] = card["power"]
    if card.get("toughness") is not None:
        summary["toughness"] = card["toughness"]

    return summary


def get_price(card: dict) -> float | None:
    """Return the USD market price as a float, or None if unavailable.

    Scryfall's prices values are strings or JSON null; we normalize to
    float so the display layer always receives a consistent type.

    Args:
        card: Raw Scryfall card object dict.

    Returns:
        Price in USD as a float, or None when absent or null.
    """
    prices = card.get("prices") or {}
    usd = prices.get("usd")
    if usd is None:
        return None
    try:
        return float(usd)
    except (ValueError, TypeError):
        return None


def get_legality(card: dict, fmt: str) -> str:
    """Return the card's legality status in the given format.

    Args:
        card: Raw Scryfall card object dict.
        fmt: Format name, e.g. "standard", "commander", "modern".

    Returns:
        One of: "legal", "not_legal", "banned", "restricted",
        or "unknown" when the format is not in the legalities dict.
    """
    legalities = card.get("legalities") or {}
    return legalities.get(fmt, "unknown")


def compare_cards(card_a: dict, card_b: dict) -> dict:
    """Build a structure for side-by-side display of two cards.

    Args:
        card_a: Raw Scryfall card object dict.
        card_b: Raw Scryfall card object dict.

    Returns:
        Dict with 'a' and 'b' keys, each containing an extract_card_summary.
    """
    return {
        "a": extract_card_summary(card_a),
        "b": extract_card_summary(card_b),
    }
