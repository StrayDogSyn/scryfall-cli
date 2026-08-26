"""
Scryfall API client for MyManaBox.

Every network call in the application goes through this module.
Scryfall is free, requires no API key, and follows the same
one-request-per-record pattern as the CTD pre-work Option 3 (PokeAPI).

Base URL: https://api.scryfall.com
Rate limit: ~10 req/sec; we sleep 100ms between requests to stay polite.
Timeout: 10 seconds per request -- requests has no default, so a hung
         socket would freeze the CLI forever without this.
"""

import time

import requests

USER_AGENT = "MyManaBox/1.0 (github.com/StrayDogSyn/MyManaBox)"
BASE_URL = "https://api.scryfall.com"
TIMEOUT = 10  # seconds


class CardNotFoundError(Exception):
    """Raised when Scryfall returns 404 for a card lookup.

    Scryfall uses 404 for two distinct cases:
      - No card matched the name at all.
      - The fuzzy name matched multiple cards (ambiguous).
    The ``ambiguous`` attribute lets the caller give a targeted message.
    """

    def __init__(self, message: str, ambiguous: bool = False) -> None:
        super().__init__(message)
        self.ambiguous = ambiguous


def _headers() -> dict:
    """Return standard request headers including User-Agent."""
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def fetch_card_by_name(name: str) -> dict:
    """Fetch one card by name using Scryfall fuzzy matching.

    Args:
        name: Card name, tolerant of minor misspellings.

    Returns:
        Raw Scryfall card object as a dict.

    Raises:
        CardNotFoundError: On 404 (no match or ambiguous match).
        requests.exceptions.Timeout: When the server does not respond in time.
        requests.exceptions.ConnectionError: When the host is unreachable.
        requests.exceptions.HTTPError: On non-404 server errors.
        requests.exceptions.RequestException: On any other network failure.
    """
    time.sleep(0.1)  # Respect Scryfall's documented rate limit
    try:
        response = requests.get(
            f"{BASE_URL}/cards/named",
            params={"fuzzy": name},
            headers=_headers(),
            timeout=TIMEOUT,
        )
        if response.status_code == 404:
            body = response.json()
            details = body.get("details", "")
            # Scryfall uses "too many cards" wording for ambiguous matches
            ambiguous = "too many" in details.lower() or "ambiguous" in details.lower()
            raise CardNotFoundError(
                details or f"No card found: {name}",
                ambiguous=ambiguous,
            )
        response.raise_for_status()
        return response.json()
    except CardNotFoundError:
        raise
    except requests.exceptions.Timeout:
        raise requests.exceptions.Timeout(
            f"Scryfall did not respond within {TIMEOUT}s. Check your connection."
        )
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError(
            "Could not reach Scryfall. Check your internet connection."
        )
    except requests.exceptions.HTTPError as exc:
        raise requests.exceptions.HTTPError(
            f"Scryfall returned an error: {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise requests.exceptions.RequestException(
            f"Unexpected network error: {exc}"
        ) from exc


def search_cards(query: str) -> list[dict]:
    """Search for cards matching a Scryfall query string.

    Returns the first page of results (up to 175 cards per page).

    Args:
        query: Full Scryfall search syntax, e.g. ``"t:goblin c:r"``.

    Returns:
        List of raw Scryfall card dicts.

    Raises:
        CardNotFoundError: When the query matches nothing.
        requests.exceptions.Timeout: When the server does not respond in time.
        requests.exceptions.ConnectionError: When the host is unreachable.
        requests.exceptions.HTTPError: On non-404 server errors.
        requests.exceptions.RequestException: On any other network failure.
    """
    time.sleep(0.1)
    try:
        response = requests.get(
            f"{BASE_URL}/cards/search",
            params={"q": query},
            headers=_headers(),
            timeout=TIMEOUT,
        )
        if response.status_code == 404:
            raise CardNotFoundError(f"No cards found for query: {query}")
        response.raise_for_status()
        data = response.json()
        # TODO: pagination via data["has_more"] and data["next_page"]
        return data.get("data", [])
    except CardNotFoundError:
        raise
    except requests.exceptions.Timeout:
        raise requests.exceptions.Timeout(
            f"Scryfall did not respond within {TIMEOUT}s. Check your connection."
        )
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError(
            "Could not reach Scryfall. Check your internet connection."
        )
    except requests.exceptions.HTTPError as exc:
        raise requests.exceptions.HTTPError(
            f"Scryfall returned an error: {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise requests.exceptions.RequestException(
            f"Unexpected network error: {exc}"
        ) from exc
