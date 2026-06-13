"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card, compare_prices


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "price_context": None,       # string returned by compare_prices (optional)
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query into description, size, max_price using regex
    price_match = re.search(
        r'\b(?:under|below|max|less\s+than|up\s+to)\s*\$?\s*(\d+(?:\.\d+)?)',
        query, re.IGNORECASE,
    )
    size_match = re.search(
        r'\b(?:size\s+|in\s+)?(XXL|XL|XS|S/M|S|M|L)\b',
        query, re.IGNORECASE,
    )
    max_price = float(price_match.group(1)) if price_match else None
    size = size_match.group(1).upper() if size_match else None
    desc = query
    for match in filter(None, [price_match, size_match]):
        desc = desc[:match.start()] + " " + desc[match.end():]
    desc = re.sub(r'\b(?:size|in)\b', ' ', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\s+', ' ', desc).strip(' ,.')
    session["parsed"] = {"description": desc, "size": size, "max_price": max_price}

    # Step 3: Search listings
    session["search_results"] = search_listings(
        description=desc,
        size=size,
        max_price=max_price,
    )
    if not session["search_results"]:
        session["error"] = (
            f"No listings found matching \"{query}\". "
            "Try broader keywords, a higher budget, or a different size."
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = session["search_results"][0]
    item = session["selected_item"]

    # Step 5: Suggest outfit — empty wardrobe → show what was found, skip outfit/fit card
    if not wardrobe.get("items"):
        session["error"] = (
            "No wardrobe items found. To get outfit ideas, describe what you own in your query — "
            "e.g. 'I mostly wear baggy jeans and chunky sneakers.'"
        )
        return session

    session["outfit_suggestion"] = suggest_outfit(item, wardrobe)
    raw_suggestion = session["outfit_suggestion"].strip()

    # Reject if the LLM signalled no match
    no_match = raw_suggestion.startswith("[NO_MATCH]")

    # Reject if the suggestion doesn't actually mention any real wardrobe item by name
    # (catches hallucination even when the LLM ignores the [NO_MATCH] instruction)
    wardrobe_names = [w["name"].lower() for w in wardrobe.get("items", [])]
    references_real_item = any(name in raw_suggestion.lower() for name in wardrobe_names)

    if no_match or not references_real_item:
        session["outfit_suggestion"] = None
        session["error"] = (
            "Your wardrobe doesn't have enough pieces to build a complete outfit with this item "
            "(needs at least a top, bottom, and shoes). "
            "Try describing more of what you own in your query."
        )
        return session

    # Step 6: Create fit card
    session["fit_card"] = create_fit_card(session["outfit_suggestion"], item)

    # Step 6b: Compare prices if max_price was given or user signals price concern
    _price_keywords = {"good deal", "worth it", "cheap", "expensive", "fair", "value", "price"}
    if max_price is not None or any(kw in query.lower() for kw in _price_keywords):
        session["price_context"] = compare_prices(item, session["search_results"])

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
    print(f"Fit card: {session2['fit_card']}")
