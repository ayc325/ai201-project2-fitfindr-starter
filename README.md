# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

---

## Tool Inventory

### Tool 1: `search_listings`

**Purpose:** Searches the mock listings dataset for items matching a free-text description, with optional size and price filters. Returns an empty list if nothing matches — never raises an exception.

**Inputs:**

- `description` (str): Free-text keywords describing the item (e.g., "vintage graphic tee")
- `size` (str | None): Letter size to filter by (e.g., "M", "XL"); case-insensitive. Pass `None` to skip.
- `max_price` (float | None): Maximum price (inclusive). Pass `None` to skip.

**Output:** `list[dict]` — matching listing dicts sorted by keyword relevance score (highest first). Each dict has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`.

---

### Tool 2: `suggest_outfit`

**Purpose:** Given a thrifted item and the user's wardrobe, calls the LLM to suggest 1–2 complete outfits using specific pieces from the wardrobe. If the wardrobe is empty, returns general styling advice instead.

**Inputs:**

- `new_item` (dict): A listing dict from `search_listings` (the item the user is considering)
- `wardrobe` (dict): A wardrobe dict with an `"items"` key containing a list of wardrobe item dicts

**Output:** `str` — a non-empty string with outfit suggestions or general styling advice.

---

### Tool 3: `create_fit_card`

**Purpose:** Generates a short, shareable Instagram/TikTok-style caption for the outfit. Mentions the item name, price, and platform naturally. Uses a higher LLM temperature so each caption sounds different.

**Inputs:**

- `outfit` (str): The outfit suggestion string returned by `suggest_outfit`
- `new_item` (dict): The listing dict for the thrifted item

**Output:** `str` — a 2–4 sentence caption. Returns a descriptive error string if `outfit` is empty — does not raise an exception.

---

### Tool 4: `compare_prices`

**Purpose:** Compares the selected item's price against similar items in the same category. Returns a LOW / AVERAGE / HIGH rating with a casual explanation. Only called when price concern is detected — not on every run.

**Inputs:**

- `new_item` (dict): The listing dict to evaluate (must have a `price` field)
- `comparison_pool` (list[dict] | None): Items to compare against; falls back to the full dataset filtered by category if `None` or empty

**Output:** `str` — a rating string prefixed with `[LOW]`, `[AVERAGE]`, or `[HIGH]` followed by a 1–2 sentence explanation. Returns a no-data message string if comparison data is unavailable.

---

## How the Planning Loop Works

The loop runs top-to-bottom with early exits at two checkpoints:

1. **Parse the query** — regex extracts `max_price` (e.g., "under $30" → `30.0`), `size` (e.g., "size M" → `"M"`), and strips those tokens from the description. The cleaned description, size, and max_price are stored in `session["parsed"]`.

2. **Call `search_listings`** — if results come back empty, `session["error"]` is set with a helpful message and the loop returns immediately. `suggest_outfit` is never called with empty input.

3. **Select top result** — `results[0]` is stored as `session["selected_item"]` (highest relevance score).

4. **Check wardrobe** — if `wardrobe["items"]` is empty, `session["error"]` is set and the loop returns immediately. `create_fit_card` is never called without an outfit.

5. **Call `suggest_outfit`** — result stored in `session["outfit_suggestion"]`.

6. **Call `create_fit_card`** — result stored in `session["fit_card"]`.

7. **Conditionally call `compare_prices`** — only if `max_price` was parsed from the query **or** the query contains a price-concern keyword ("good deal", "worth it", "cheap", "expensive", "fair", "value", "price"). Result stored in `session["price_context"]`. If neither condition is true, `price_context` stays `None`.

8. **Return the session dict.**

---

## State Management

The agent maintains a single `session` dict that accumulates results across all tool calls. Nothing is re-fetched once stored.

| Key | Set when | Passed to |
| --- | -------- | --------- |
| `query` | Session start | Used for error messages and keyword detection |
| `parsed` | After query parsing | `search_listings` (description, size, max_price) |
| `search_results` | After `search_listings` | `compare_prices` (as comparison pool) |
| `selected_item` | After picking `results[0]` | `suggest_outfit`, `create_fit_card`, `compare_prices` |
| `wardrobe` | Session start (passed in) | `suggest_outfit` |
| `outfit_suggestion` | After `suggest_outfit` | `create_fit_card` |
| `fit_card` | After `create_fit_card` | Final output |
| `price_context` | After `compare_prices` (conditional) | Final output |
| `error` | On any early exit | Signals the caller that the run ended early |

---

## Error Handling Strategy

| Tool | Failure mode | Agent response |
| ---- | ------------ | -------------- |
| `search_listings` | No results match the query | Sets `session["error"]` and returns immediately. `suggest_outfit` is never called. |
| `suggest_outfit` | Wardrobe is empty (new user) | Sets `session["error"]` with a "not yet implemented" message and returns immediately. `create_fit_card` is never called. |
| `create_fit_card` | `outfit` string is empty or whitespace | Returns a descriptive error string — does not raise. Session continues. |
| `compare_prices` | No comparable listings or item price missing | Returns a no-data message string — does not block the rest of the output. |

**Concrete example from testing:**

Query: `"designer ballgown size XXS under $5"` — no listings in the dataset match all three constraints (category, size XXS, price ≤ $5). `search_listings` returns `[]`. The agent sets:

```python
session["error"]   = "No listings found matching \"designer ballgown size XXS under $5\". Try broader keywords, a higher budget, or a different size."
session["fit_card"] = None
```

`suggest_outfit` and `create_fit_card` were never called. Verified by running `python agent.py` and observing the no-results branch prints the error message and `Fit card: None`.

---

## Spec Reflection

**One way the spec helped:**
The error handling table in `planning.md` made it easy to identify exactly two early-exit points (no search results, empty wardrobe) before writing any code. Without that table, those short-circuits might have been added inconsistently or forgotten entirely.

**One way implementation diverged from the spec:**
`planning.md` specified that `suggest_outfit` should return a structured `dict` with fields like `top`, `bottom`, `shoes`, `total_price`, and `match_reason`, and that `create_fit_card` should accept that dict and return a structured dict with `caption`, `key_pieces`, and `price_summary`. In practice, both tools return plain strings — `suggest_outfit` returns LLM-generated text and `create_fit_card` returns a caption string directly. The structured dict approach was dropped because the LLM output doesn't reliably map to named fields like `top` and `bottom`, and the tests only check that the strings are non-empty, not their internal structure.

---

## AI Usage

**Instance 1 — Implementing the planning loop:**
I gave Claude the Planning Loop and State Management sections of `planning.md` along with the signatures of all four tools, and asked it to implement `run_agent()` in `agent.py`. The generated code correctly wired the tools together and handled the two early-exit cases. I reviewed the conditional logic for `compare_prices` and revised the price-keyword set to include multi-word phrases like `"good deal"` and `"worth it"` (the first draft only checked single words), then verified that `test_price_keyword_triggers_compare_prices` passed.

**Instance 2 — Verifying the no-results branch:**
I asked Claude to run `python agent.py` and confirm that the no-results path sets `session["error"]` and leaves `session["fit_card"]` as `None` without calling `suggest_outfit`. Claude ran the script, identified that the print statement for `fit_card` was missing from the CLI output block, added `print(f"Fit card: {session2['fit_card']}")`, re-ran the script, and confirmed the output showed `Fit card: None`. I kept the added print line because it makes the branch behavior visible during manual testing.
