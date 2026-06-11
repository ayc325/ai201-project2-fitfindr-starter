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
The result should contain a list of matching items sorted by relevance. Each item contains: a unique itemID, item name, size, price, source (e.g., "Depop", "Poshmark"), condition (e.g., "Good condition", "Like new"), and a description of how the item matches the search description from the user.

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
          category (str): one of top, bottom, shoes, socks, accessory, outerwear.
     Optional:
          size (str): XS/S/M/L/XL or numeric pant sizes (24, 26, …) or US sizes (0, 2, …).
          color (str)
          pattern (str) (e.g., striped, graphic)
          material (str)
          max_price (float): budget cap for this item
          occasion (str): casual, work, evening, athleisure, etc.
          fit (str): slim, regular, oversized
          required (bool): if true, outfit must include this item

- `wardrobe` (dict): 
     Each item object:
          id (str): unique id
          name (str)
          category (str)
          size (str or list[str])
          colors (list[str])
          price (float)
          tags (list[str]) — searchable keywords like vintage, graphic, denim
          available (bool)
          rating (float, optional) — user preference score
          image_url (str, optional)
     Semantics: prefer items with available=true; match by category, size, colors, and tags.

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
     Failure: return "No outfit found" or { "error": "No outfit found", "reason": "wardrobe empty" }.
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
     Item object shape: id (str), name (str), category (str), price (float), size (str), colors (list[str]), image_url (str, optional), source (str: "wardrobe" or "listing"), match_score (0..1, optional).
     Metadata: total_price (float), match_reason (str), match_scores (dict).
- `new_item` (dict): Optional. The newly found listing (from search_listings) that anchors the outfit. Same item object shape as above. Used so the caption can highlight the new piece (e.g., reference its source or price).
- `style_tone` (str): Optional. Tone for caption (playful, minimal, edgy, romantic). Default: casual.
- `length` (str): Optional. short or long caption. Default: short.

**What it returns:**
<!-- Describe the return value -->
`fit_card` (dict):
     - caption (str): single human-friendly caption summarizing the look.
     - key_pieces (list[dict]): short entries for each piece: { "role": "top", "name": "...", "id": "...", "price": 0.0 }.
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
shows the user a rating of "high, average, low" for pricing compared to other similar items. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `item` (dict) — Required. Item to evaluate.
id (str), name (str), category (str), price (float), tags (list[str], optional), size (str, optional), colors (list[str], optional), source (str: "wardrobe" or "listing", optional)
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
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

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

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

**Step 3:**
<!-- Continue until the full interaction is complete -->

**Final output to user:**
<!-- What does the user actually see at the end? -->
