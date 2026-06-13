# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool will search through a mock dataset to look for an item that most closely matches the parameters. If there are no items that closely match the item with the parameters, "No items found" will be returned.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Required. Free-text search keywords describing the clothing item (e.g., "vintage graphic tee, short-sleeve, black"). Include category keywords like top, bottom, pants, jeans, skirt, shoes, socks, accessory, outerwear, and attributes like color, pattern, material, and fit.
- `size` (str): Optional. Letter sizes (XS, S, M, L, XL) or numeric pant sizes (24, 26, 28, 30, 32, 34, 36) or US sizes (00, 0, 2, 4, 6, 8, 10, 12). Used to filter results by fit/size compatibility.
- `max_price` (float): Optional. Maximum budget for the item; listings with price > max_price should be excluded or deprioritized.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
The result should contain a list of matching items sorted by relevance. Each item contains: `id` (e.g., "lst_006"), `title`, `size`, `price`, `platform` (e.g., "depop", "poshmark", "thredUp"), `condition` (one of: "excellent", "good", "fair"), `brand` (str or null), and a `match_reason` describing how the item matches the search.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
Return a list with one element: "No items found"

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Tool suggests an outfit based on the mock dataset. The outfit should include a top, bottom, and shoes at minimum. Include socks and accessories (like hair accessories and jewelry) as optional.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): 
     Required:
          description (str): free-text keywords (e.g., "vintage graphic tee, short-sleeve").
          category (str): one of tops, bottoms, shoes, outerwear, accessories.
     Optional:
          size (str): XS/S/M/L/XL or numeric pant sizes (24, 26, …) or US sizes (0, 2, …).
          color (str)
          pattern (str) (e.g., striped, graphic)
          material (str)
          max_price (float): budget cap for this item
          occasion (str): casual, work, evening, athleisure, etc.
          fit (str): slim, regular, oversized
          required (bool): if true, outfit must include this item

- `wardrobe` (list[dict]):
     Each item object:
          id (str): unique id (e.g., "w_001")
          name (str): short description of the piece
          category (str): one of tops, bottoms, shoes, outerwear, accessories
          colors (list[str])
          style_tags (list[str]) — style descriptors like vintage, denim, streetwear
          notes (str, optional): fit notes or how the user styles it
     Semantics: match by category, colors, and style_tags; use notes for additional styling context.

**What it returns:**
<!-- Describe the return value -->
outfit (dict) with:
     top, bottom, shoes (each either an item object from wardrobe or a listing result)
     optional socks (item), accessories (list[item])
     total_price (float)
     match_reason (str): short explanation of why pieces were chosen together
     styling_tips (str): practical wearing advice (e.g., "Roll the sleeves once and tuck the front corner slightly for shape")
     match_scores (dict): per-item match confidence 0..1



**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

- Wardrobe empty → return `{ "error": "No outfit found", "reason": "wardrobe empty" }`. Agent tells the user to add wardrobe items and stops.
- Wardrobe has items but no style match (e.g., all cottagecore, new item is grunge) → return `{ "error": "No outfit found", "reason": "no style match" }`. Agent falls back to searching listings for complementary pieces instead of using the wardrobe, and notes this to the user: "Your wardrobe didn't have a great match — here's a suggestion from available listings instead."
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generates a short, shareable description of a complete outfit — the kind of thing someone would caption an Instagram post with. Must produce something different each time for different inputs. List all the key pieces of the outfit.


**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (dict): 
     Required. Complete outfit object produced by suggest_outfit.
     Required fields: top, bottom, shoes — each an item object.
     Optional fields: socks (item), accessories (list[item]).
     Item object shape: id (str), title (str), category (str), price (float), size (str), colors (list[str]), brand (str or null), platform (str), origin (str: "wardrobe" or "listing"), match_score (0..1, optional).
     Metadata: total_price (float), match_reason (str), match_scores (dict).
- `new_item` (dict): The newly found listing (from search_listings) that anchors the outfit. Same item object shape as above. Used so the caption can highlight the new piece (e.g., reference its source or price).
- `style_tone` (str): Optional. Tone for caption (playful, minimal, edgy, romantic). Default: casual.
- `length` (str): Optional. short or long caption. Default: short.

**What it returns:**
<!-- Describe the return value -->
`fit_card` (dict):
     - caption (str): single human-friendly caption summarizing the look.
     - key_pieces (list[dict]): short entries for each piece: { "role": "top", "title": "...", "id": "...", "price": 0.0 }.
     - price_summary (str): e.g., "Total: $xx (affordable/average/expensive)".
     - tags (list[str]): style tags like vintage, casual, date-night.
     - share_text (str, optional): alternate phrasing for sharing.
     - debug (dict, optional): source info and match_scores.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
     Failure modes & responses:
          - If outfit missing required pieces → return { "error": "incomplete_outfit", "missing": ["top","shoes"] }.
          - If input invalid → return { "error": "invalid_input", "reason": "explain reason" }.
          - Always return a concise human-readable caption when at least top+bottom+shoes exist; otherwise return the error object.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

### Tool 4: compare_prices

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Shows the user a rating of "high, average, low" for pricing compared to other similar items. Called only when the user signals price concern — if the query mentions "good deal", "worth it", "is this cheap", or includes a tight max_price, the agent calls it. Otherwise it doesn't.

The requirements say the loop should "respond to what it receives" — so the most defensible approach for your planning.md is the second or third option, where something in the context actually triggers the call. That way compare_prices has a clear reason to exist in the loop rather than just always running at the end.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `item` (dict) — Required. Item to evaluate.
id (str), title (str), category (str), price (float), style_tags (list[str], optional), size (str, optional), colors (list[str], optional), brand (str or null, optional), platform (str, optional)
- `comparison_pool` (list[dict]) — Explicit list of items to compare against; same item shape as above. If omitted, use available listings data.
- `granularity` (str) — Optional. One of category, category+tags, or global. Default: category.
- `thresholds` (dict) — Optional. Numeric cutoffs for mapping percentile → rating, e.g. { "low": 0.33, "high": 0.66 } (default uses thirds).

**What it returns:**
<!-- Describe the return value -->
- `rating` (str): "low" | "average" | "high"
- `message` (str): short, casual explanation the user will see (e.g., "Average priced like most vintage tees here.")
- `source_count` (int, optional): number of comparison items used (helpful transparency)

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the input data is incomplete? -->
- If comparison_pool is empty or item.price missing → return:
{ "rating": "no data", "message": "Insufficient comparison data to rate this item." }


---

## How the Planning Loop Works

The loop runs top-to-bottom with early exits at two checkpoints:

1. **Always start with `search_listings`** — regex extracts `description`, `size`, and `max_price` from the user's query (e.g., "under $30" → `30.0`, "size M" → `"M"`). This runs on every interaction, regardless of wardrobe state. Results stored in `session["search_results"]`.

2. **If results=[]** → stop. `session["error"]` is set with a helpful message. Do not proceed further.

3. **If results found** → save `results[0]` as `session["selected_item"]` (highest relevance score).

4. **Check wardrobe** — if `wardrobe["items"]` is empty, set `session["error"]` with a message telling the user to describe what they own, and return immediately. The listing is still shown (via `session["selected_item"]`); only the outfit and fit card panels are skipped. Do not call `suggest_outfit` or `create_fit_card`.

5. **If wardrobe has items** → call `suggest_outfit(selected_item, wardrobe)`. Result stored in `session["outfit_suggestion"]`.

6. **If outfit returned** → always call `create_fit_card(outfit, selected_item)` to generate the caption. Result stored in `session["fit_card"]`.

7. **Conditionally call `compare_prices`** — only if `max_price` was parsed from the query **or** the query contains a price-concern keyword ("good deal", "worth it", "cheap", "expensive", "fair", "value", "price"). Result stored in `session["price_context"]`. If neither condition is true, `price_context` stays `None`.

8. **Done** — return the session dict to the caller.

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
| `search_listings` | No results match the query | Sets `session["error"]` and returns immediately. `selected_item` stays `None`. `suggest_outfit` is never called. |
| `suggest_outfit` | Wardrobe is empty | Sets `session["error"]` with a prompt to describe owned items. Returns immediately — the listing is still shown via `selected_item`. `create_fit_card` is never called. |
| `create_fit_card` | `outfit` string is empty or whitespace | Returns a descriptive error string — does not raise. Session continues. |
| `compare_prices` | No comparable listings or item price missing | Returns a no-data message string — does not block the rest of the output. |


## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

- I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement search_listings() using load_listings() from the data loader - then test it against 3 queries before trusting it.

- I'll give Claude my Tool 2 spec (inputs, return value, failure mode) and ask it to implement suggest_outfit() using load_wardrobe() from the data loader and from the output of search_listings - then test it against 3 queries before trusting it.

- I'll give Claude my Tool 3 spec (inputs, return value, failure mode) and ask it to implement create_fit_card() using the outfit from suggest_outfit() and the new_item output of search_listings - then test it against 3 queries before trusting it.

- I'll give Claude my Tool 4 spec (inputs, return value, failure mode) and ask it to implement compare_prices() using the output of search_listings, specifically the price and using load_listings() from the data loader to find similar items' prices - then test it against 3 queries before trusting it.

**Milestone 4 — Planning loop and state management:**

- I'll give Claude my planning loop and architecture and ask it to implement the planning loop using the tools already implemented from Milestone 3 then iterating on the output of the changes before finalizing the edits.

- I'll give Claude the state management and ask it to revise the planning loop to include state management then iterating on the output of the changes before finalizing the edits.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

2-3 sentence description of what FitFindr needs to do:
The agent should call the search_listings tool to find a vintage graphic tee under $30 then calls the suggest_outfit tool to suggest an outfit that fits the vintage graphic tee that the search_listings tool picked out. Then, the create_fit tool is called to provide a user-friendly caption about the outfit. Lastly, the compare_prices tool is called since the user showed price sensitivity for wanting it to be under $30. 

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent calls `search_listings("vintage graphic tee", max_price=30.0)`.

Returns 2 results sorted by relevance (no third close match exists in the dataset):

    [
      "Graphic Tee — 2003 Tour Bootleg Style — $24, Depop, Good condition.",
      "Vintage Band Tee — Faded Grey — $19, Depop, Fair condition."
    ]

The agent picks the top result (lst_006) — better condition, stronger tag match.

**Step 2:**
The agent calls `suggest_outfit(new_item=<lst_006>, wardrobe=<user's wardrobe>)`.

The user's wardrobe includes:

- w_001: Baggy straight-leg jeans, dark wash (bottoms)
- w_007: Chunky white sneakers (shoes)

Returns:

    "Pair this with your baggy dark-wash jeans and chunky sneakers for an easy 90s streetwear look.
    Leave the tee untucked and let it drape — the boxy fit does the work."

**Step 3:**
The agent calls `create_fit_card(outfit=<suggest_outfit result>, new_item=<lst_006>)`.

Returns:

    "found this boxy graphic tee on depop for $24 and it was basically made for my baggy jeans.
    full look: graphic tee + dark-wash straights + chunky sneakers."

**Step 4:**
The agent calls `compare_prices(item=<lst_006>)`, comparing against all tops in the listings dataset (15 items, prices ranging $15–$35).

Returns:

    { "rating": "high", "message": "Slightly above average for a vintage top, but fair for a graphic tee in good condition." }

**Final output to user:**

    Found 2 vintage graphic tees under $30:
      • Graphic Tee — 2003 Tour Bootleg Style — $24, Depop, Good condition.
      • Vintage Band Tee — Faded Grey — $19, Depop, Fair condition.

    Top pick: the $24 graphic tee. Pair it with your baggy dark-wash jeans and chunky sneakers
    for an easy 90s streetwear look. Leave it untucked — the boxy fit does the work.

    Pricing note: slightly above average for tops, but fair for a graphic tee in good condition.

