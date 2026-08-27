# Scryfall Card Lookup CLI

A command-line tool for looking up Magic: The Gathering cards using the Scryfall API. You type a card name, a query, or two card names to compare, and the tool fetches live data and prints it in a readable format. It handles the things that actually go wrong: misspelled names, ambiguous matches, missing prices, cards without power and toughness, and network failures.

Built as the Code The Dream Python Advanced pre-work submission.

## Requirements

- Python 3.10 or newer

## API

[Scryfall](https://scryfall.com/docs/api) -- free, no API key, no rate-limit registration. The same one-request-per-record pattern as the CTD Option 3 (PokeAPI). The base URL is `https://api.scryfall.com`. Requests are separated by a 100ms sleep to stay within Scryfall's documented guidelines.

## Module layout

| File | Responsibility |
|------|----------------|
| `api_client.py` | All network calls. `requests`-based, 10s timeout on every request, 100ms rate-limit delay, `User-Agent` header, explicit exception handling for each failure mode, `CardNotFoundError` distinguishing "no match" from "ambiguous match". |
| `card_data.py` | Data transformation. No network calls, no printing. Takes raw Scryfall dicts and returns clean Python data. Every field access uses `.get()` because some fields are genuinely absent -- Sol Ring has no `power`, Arena-only cards have no `usd` price. |
| `display.py` | Output formatting. Standard library only. f-string width specifiers for alignment. `None` and empty strings never reach the output; they print as `n/a`. |
| `main.py` | Orchestration. `argparse` CLI with three subcommands. Calls `api_client`, `card_data`, and `display` only -- no request logic, no parsing, no formatting of its own. Non-zero exit code on any error. |

## Installation

```bash
git clone https://github.com/StrayDogSyn/scryfall-cli.git
cd scryfall-cli

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Tests

Run the complete offline test suite from the project root:

```bash
python -m unittest discover -s tests -v
```

The tests use mocked Scryfall responses, so they do not require internet access.

## Usage

```bash
python main.py lookup "lightning bolt"
python main.py lookup "sol ring"
python main.py compare "black lotus" "mox pearl"
python main.py search "t:goblin c:r"
```

## Example output

`lookup "lightning bolt"`:
```text
  Lightning Bolt
  ----------------------------------------
  Mana Cost      {R}
  Type           Instant
  Rarity         Uncommon
  Set            Marvel Super Heroes Commander
  Released       2026-06-26
  Price (USD)    $0.79

  Lightning Bolt deals 3 damage to any target.

  Artist         Milivoj Ceran
```

`lookup "sol ring"` -- Sol Ring is an artifact; no P/T row appears because the field is absent in the Scryfall response, not null:
```text
  Sol Ring
  ----------------------------------------
  Mana Cost      {1}
  Type           Artifact
  Rarity         Uncommon
  Set            Marvel Super Heroes Commander
  Released       2026-06-26
  Price (USD)    $1.47

  {T}: Add {C}{C}.

  Artist         Myles Wohl
```

`compare "black lotus" "mox pearl"`:
```text
  CARD A                                 | CARD B
  -------------------------------------------------------------------------------
  Name: Black Lotus                      | Name: Mox Pearl
  Mana Cost: {0}                         | Mana Cost: {0}
  Type: Artifact                         | Type: Artifact
  Rarity: Bonus                          | Rarity: Bonus
  Set: Vintage Masters                   | Set: Vintage Masters
  Price (USD): n/a                       | Price (USD): n/a
```

Both cards are digital-only reprints; no USD price exists. That is a real case `card_data.get_price()` handles.

## Error handling

All errors are caught before they reach the user. No stack traces print. The program exits with code 1 on any failure.

| Scenario | Output |
|----------|--------|
| Empty or whitespace input | `Error: Card name cannot be empty.` No request is made. |
| No card matches the name | `Error: No card found for "zzzzzzzz".` |
| Ambiguous fuzzy match | `Error: "jace" matched several cards. Try a more specific name or add a set code.` |
| Network timeout (10s) | `Error: Scryfall did not respond within 10s. Check your connection.` |
| No internet connection | `Error: Could not reach Scryfall. Check your internet connection.` |
| HTTP error from Scryfall | `Error: Scryfall returned an error: <status>` |

## Contributors

- **StrayDogSyn** — project creator and maintainer
- **Codex by OpenAI** — test suite, verification, and repository preparation
