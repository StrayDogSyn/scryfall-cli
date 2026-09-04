# Scryfall Card Lookup CLI

A command-line tool for looking up Magic: The Gathering cards using the Scryfall API. You type a card name, a query, or two card names to compare, and the tool fetches live data and prints it in a readable format. It handles the things that actually go wrong: misspelled names, ambiguous matches, missing prices, cards without power and toughness, and network failures.

Built as the Code The Dream Python Advanced pre-work submission.

## Requirements

- Python 3.10 or newer

## API

[Scryfall](https://scryfall.com/docs/api) -- free, no API key, no rate-limit registration. The same one-request-per-record pattern as the CTD Option 3 (PokeAPI). The base URL is `https://api.scryfall.com`. Requests are separated by a 100ms sleep to stay within Scryfall's documented guidelines.

### API exploration notes

These observations were recorded from live JSON responses on September 4, 2026.
The API root, `https://api.scryfall.com/`, returns an error object explaining
that it does not serve card data directly. The working endpoints explored for
this project were:

- `https://api.scryfall.com/cards/search?q=t%3Agoblin+c%3Ar`
- `https://api.scryfall.com/cards/named?exact=sol%20ring`
- `https://api.scryfall.com/cards/named?exact=grizzly%20bears`

Answers to the four exploration questions:

1. A search response is a top-level dictionary with its records in the `data`
   list. It also contains `object`, `total_cards`, `has_more`, and sometimes
   `next_page`. A named-card response is one top-level card dictionary. The
   `search` command therefore parses `data` into a list of card dictionaries.
2. Card records have many fields. This tool uses `name`, `mana_cost`, `cmc`,
   `type_line`, `rarity`, `set_name`, `oracle_text`, `artist`, `released_at`,
   `power`, `toughness`, and `prices`.
3. Several values are nested. `prices`, `legalities`, `image_uris`, and
   `related_uris` are dictionaries; `colors`, `games`, `keywords`, and
   `multiverse_ids` are lists. Multi-faced cards can also contain a
   `card_faces` list whose elements are dictionaries.
4. Optional values do vary. Non-creature cards such as Sol Ring omit `power`
   and `toughness`; digital-only or unavailable printings can have a null
   `prices.usd`; and multi-faced cards may omit top-level `mana_cost`,
   `oracle_text`, or `image_uris` because those values live in `card_faces`.
   The program uses `.get()` and display fallbacks for these cases.

### Project plan

A user will run MyManaBox with an `argparse` subcommand to look up one Magic:
The Gathering card by fuzzy name, compare two cards side by side, or search
with Scryfall query syntax. The tool will request live Scryfall JSON, transform
card records into display-ready data using fields including name, mana cost,
type, rarity, set, price, and power/toughness, and print labeled details,
aligned comparison columns, or a concise result list rather than raw
dictionaries. Fetching, transformation, display, and command orchestration
will remain in separate modules. Empty input, missing or ambiguous matches,
network failures, bad HTTP responses, missing fields, null prices, and
malformed optional values will produce helpful output instead of tracebacks.

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

Search output is intentionally limited to Scryfall's first page (up to 175
cards), keeping broad queries fast and terminal output bounded.

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

## Rubric confirmation

Checked against the [Python Advanced Pre-Work Rubric](https://codethedream.org/wp-content/uploads/2026/06/python_advanced_prework_rubric.pdf):

- **API integration:** `api_client.py` uses `requests` in dedicated functions,
  with URLs separated from query parameters and a timeout on every call.
- **Data transformation:** search JSON is parsed into a list of dictionaries;
  `card_data.py` extracts more than three relevant fields in dedicated
  functions and handles missing keys safely.
- **CLI tool:** `main.py` accepts user input through `argparse` and provides
  three meaningful interactions: lookup, comparison, and search. All output
  is formatted for people rather than printed as raw dictionaries.
- **Error handling:** network and HTTP errors are caught at the API boundary;
  empty input, no matches, ambiguous matches, missing values, malformed 404
  bodies, incomplete P/T data, and invalid prices are handled gracefully.
- **Code organization:** fetching, transformation, display, and orchestration
  are separated into focused modules and functions.
- **Version control:** the repository has multiple descriptive commits. Submit
  the final work through a pull request to satisfy the rubric's full workflow.
- **Deliverables:** the repository includes `main.py`, supporting modules,
  `requirements.txt`, tests, and this README with setup and run instructions.
