"""
tests/test_tools.py

Consolidated pytest tests for all four FitFindr tools:
  - search_listings
  - suggest_outfit
  - create_fit_card
  - compare_prices
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools import search_listings, suggest_outfit, create_fit_card, compare_prices
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

# ── Shared fixtures ───────────────────────────────────────────────────────────

SAMPLE_ITEM = {
    "id": "lst_006",
    "title": "Graphic Tee — 2003 Tour Bootleg Style",
    "description": "Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton.",
    "category": "tops",
    "style_tags": ["graphic tee", "vintage", "grunge", "streetwear", "band tee"],
    "size": "L",
    "condition": "good",
    "price": 24.00,
    "colors": ["black"],
    "brand": None,
    "platform": "depop",
}

SAMPLE_OUTFIT = (
    "Outfit 1: Pair the Graphic Tee with baggy straight-leg jeans (dark wash), "
    "black combat boots, and a vintage black denim jacket for a grunge-streetwear look. "
    "Outfit 2: Tuck it loosely into wide-leg khaki trousers with chunky white sneakers "
    "and a brown leather belt for a relaxed daytime vibe."
)

PRICE_POOL = [
    {"id": "p1", "title": "Graphic Tee",  "category": "tops", "price": 20.00, "platform": "depop"},
    {"id": "p2", "title": "Striped Tee",  "category": "tops", "price": 25.00, "platform": "thredUp"},
    {"id": "p3", "title": "Band Tee",     "category": "tops", "price": 18.00, "platform": "depop"},
    {"id": "p4", "title": "Polo Shirt",   "category": "tops", "price": 30.00, "platform": "poshmark"},
    {"id": "p5", "title": "Crop Top",     "category": "tops", "price": 22.00, "platform": "depop"},
]


# ── search_listings ───────────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

# Failure case: No matches for a very specific query with tight filters
def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

def test_search_keyword_match():
    results = search_listings("vintage graphic tee")
    assert len(results) > 0
    titles = [r["title"].lower() for r in results]
    assert any("tee" in t or "graphic" in t for t in titles)

def test_search_size_filter():
    size = "M"
    results = search_listings("streetwear outerwear", size=size)
    assert all(size.lower() in item["size"].lower() for item in results)


# ── suggest_outfit ────────────────────────────────────────────────────────────

# Failure case: Empty wardrobe should still return some advice, not an error
def test_suggest_empty_wardrobe_returns_advice():
    result = suggest_outfit(SAMPLE_ITEM, get_empty_wardrobe())
    assert isinstance(result, str) and len(result.strip()) > 0

def test_suggest_populated_wardrobe_references_pieces():
    wardrobe = get_example_wardrobe()
    wardrobe_names = [item["name"].lower() for item in wardrobe["items"]]
    result = suggest_outfit(SAMPLE_ITEM, wardrobe)
    assert isinstance(result, str) and len(result.strip()) > 0
    result_lower = result.lower()
    matched = [n for n in wardrobe_names if any(w in result_lower for w in n.split())]
    assert len(matched) > 0

def test_suggest_always_returns_string():
    for wardrobe in [get_empty_wardrobe(), get_example_wardrobe()]:
        result = suggest_outfit(SAMPLE_ITEM, wardrobe)
        assert isinstance(result, str) and result.strip()


# ── create_fit_card ───────────────────────────────────────────────────────────

# Failure case: Empty outfit description should return an error message, not a card
def test_fit_card_empty_outfit_returns_error():
    for bad in ["", "   ", "\n"]:
        result = create_fit_card(bad, SAMPLE_ITEM)
        assert isinstance(result, str) and len(result.strip()) > 0
        assert "error" in result.lower() or "no outfit" in result.lower()

def test_fit_card_mentions_item_details():
    result = create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM)
    assert isinstance(result, str) and len(result.strip()) > 0
    result_lower = result.lower()
    title_words = [w.lower() for w in SAMPLE_ITEM["title"].split() if len(w) > 3]
    assert any(w in result_lower for w in title_words)
    assert str(int(SAMPLE_ITEM["price"])) in result or f"{SAMPLE_ITEM['price']:.2f}" in result
    assert SAMPLE_ITEM["platform"].lower() in result_lower

def test_fit_card_varies_with_different_outfits():
    outfit_a = "Grunge look: graphic tee tucked into dark jeans with combat boots and denim jacket."
    outfit_b = "Soft aesthetic: graphic tee knotted over a floral midi skirt with white ballet flats."
    assert create_fit_card(outfit_a, SAMPLE_ITEM) != create_fit_card(outfit_b, SAMPLE_ITEM)


# ── compare_prices ────────────────────────────────────────────────────────────

# Failure case: If item has no price, should return a message about insufficient data, not an error or empty string
def test_compare_missing_price_returns_no_data():
    result = compare_prices({"id": "x", "title": "Mystery Item", "category": "tops"}, PRICE_POOL)
    assert isinstance(result, str) and len(result.strip()) > 0
    assert "insufficient" in result.lower() or "no data" in result.lower()

def test_compare_cheap_item_rated_low():
    cheap = {**SAMPLE_ITEM, "price": 5.00}
    result = compare_prices(cheap, PRICE_POOL)
    assert "[LOW]" in result

def test_compare_average_item_rated_average():
    # $22 is at the 40th percentile of pool (18, 20, 22, 25, 30) → AVERAGE
    mid = {**SAMPLE_ITEM, "price": 22.00}
    result = compare_prices(mid, PRICE_POOL)
    assert "[AVERAGE]" in result

def test_compare_fallback_loads_listings():
    expensive = {**SAMPLE_ITEM, "price": 200.00}
    result = compare_prices(expensive, None)
    assert isinstance(result, str) and result.strip()
    assert any(label in result for label in ["[LOW]", "[AVERAGE]", "[HIGH]"])
