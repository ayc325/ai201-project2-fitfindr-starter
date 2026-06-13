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
- `new_item` (dict): Optional. The newly found listing (from search_listings) that anchors the outfit. Same item object shape as above. Used so the caption can highlight the new piece (e.g., reference its source or price).
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
- `comparison_pool` (list[dict]) — Optional. Explicit list of items to compare against; same item shape as above. If omitted, use available listings/wardrobe data.
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

## Planning Loop

**How does your agent decide which tool to call next?**

1. **Always start with `search_listings`** — parse `description`, `size`, and `max_price` from the user's query. This runs on every interaction.
2. **If results=[]** → stop. Tell the user what to adjust. Do not proceed to `suggest_outfit`.
3. **If results found** → save `results[0]` as `selected_item` and call `suggest_outfit(selected_item, wardrobe)`.
4. **If wardrobe=[]** → stop. Prompt the user to add wardrobe items. Do not proceed to `create_fit_card`.
5. **If outfit returned** → always call `create_fit_card(outfit, selected_item)` to generate the caption.
6. **After `create_fit_card`** → check if `max_price` was specified in the query, or if the user asked about value (e.g., "good deal", "worth it", "is this cheap"). If either is true, call `compare_prices(selected_item)`. Otherwise, stop.
7. **Done** — return all results to the user.

---

## State Management

**How does information from one tool get passed to the next?**

The agent maintains a session dictionary that accumulates results across tool calls:

- `wardrobe`: loaded once at session start using `get_example_wardrobe()` (or `get_empty_wardrobe()` for new users). Available to every tool call without the user re-entering it.
- `selected_item`: set after `search_listings` returns results; passed as `new_item` to `suggest_outfit` and as `new_item` to `create_fit_card`.
- `outfit_suggestion`: set after `suggest_outfit` returns; passed as `outfit` to `create_fit_card`.
- `fit_card`: set after `create_fit_card` returns; included in the final output to the user.
- `price_context`: set if `compare_prices` is called; appended to the final output as a pricing note.

No tool re-fetches data that a previous tool already returned. Each tool reads from the session and writes its result back to it.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Tell the user: "No listings found matching [query]. Try broader keywords, a higher budget, or a different category." Stop — do not call `suggest_outfit`. |
| suggest_outfit | Wardrobe is empty | Tell the user: "Your wardrobe is empty. Add some pieces to get outfit suggestions." Stop — do not call `create_fit_card`. |
| suggest_outfit | Wardrobe has items but no style match | Fall back to listings for complementary pieces. Tell the user: "Your wardrobe didn't have a great match — here's a suggestion from available listings instead." Continue to `create_fit_card`. |
| create_fit_card | Outfit is missing required pieces (top, bottom, or shoes) | Return error object listing the missing fields. Tell the user the fit card couldn't be generated and which pieces were missing. |
| compare_prices | No comparable listings / item price missing | Return `{ "rating": "no data", "message": "Not enough data to rate this price." }` Append as a note — do not block the rest of the output. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

User query
    │
    ▼
Planning Loop
    │
    ├─► search_listings(description, size, max_price)
    │       │
    │       ├── results=[]
    │       │       └──► [STOP] "No listings found. Try broader keywords or a higher budget."
    │       │
    │       └── results=["Graphic Tee — 2003 Tour Bootleg Style — $24, Depop, Good condition.", ...]
    │                   │
    │               selected_item = results[0]          ◄── state
    │                   │
    ├─► suggest_outfit(selected_item, wardrobe)
    │       │
    │       ├── wardrobe=[]
    │       │       └──► [STOP] "No wardrobe items found. Add some pieces to get outfit suggestions."
    │       │
    │       └── outfit = { top: <graphic tee>, bottom: <baggy jeans w_001>, shoes: <chunky sneakers w_007> }
    │                   │
    │               outfit_suggestion = outfit          ◄── state
    │                   │
    ├─► create_fit_card(outfit_suggestion, selected_item)
    │       │
    │       └── fit_card = "found this boxy graphic tee on depop for $24..."
    │                   │
    │               fit_card                            ◄── state
    │                   │
    └─► compare_prices(selected_item)   [only if max_price is specified or user asks about value]
            │
            └── { rating: "high"/"average"/"low", message: "Slightly above average for a vintage top..." }
                    │
                    ▼
            Final output to user


---

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


**Milestone 4 — Planning loop and state management:**


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

