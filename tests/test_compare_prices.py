"""
Four test cases for compare_prices.

Test 1: missing price in new_item → returns no-data message string (no exception)
Test 2: very cheap item vs explicit pool → rating is LOW
Test 3: no comparison_pool provided → falls back to load_listings(), still returns a string
Test 4: mid-range item vs explicit pool → rating is AVERAGE
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools import compare_prices

TOPS_ITEM_CHEAP = {
    "id": "lst_test_cheap",
    "title": "Basic White Tee",
    "category": "tops",
    "style_tags": ["basics"],
    "size": "M",
    "condition": "good",
    "price": 5.00,
    "colors": ["white"],
    "brand": None,
    "platform": "depop",
}

TOPS_ITEM_EXPENSIVE = {
    "id": "lst_test_exp",
    "title": "Designer Cashmere Sweater",
    "category": "tops",
    "style_tags": ["luxury"],
    "size": "M",
    "condition": "excellent",
    "price": 200.00,
    "colors": ["cream"],
    "brand": "Loro Piana",
    "platform": "poshmark",
}

SAMPLE_POOL = [
    {"id": "p1", "title": "Graphic Tee", "category": "tops", "price": 20.00, "platform": "depop"},
    {"id": "p2", "title": "Striped Tee", "category": "tops", "price": 25.00, "platform": "thredUp"},
    {"id": "p3", "title": "Band Tee",    "category": "tops", "price": 18.00, "platform": "depop"},
    {"id": "p4", "title": "Polo Shirt",  "category": "tops", "price": 30.00, "platform": "poshmark"},
    {"id": "p5", "title": "Crop Top",    "category": "tops", "price": 22.00, "platform": "depop"},
]


def test_missing_price_returns_no_data_string():
    """Item without a price key should return a no-data message, not raise."""
    no_price_item = {"id": "x", "title": "Mystery Item", "category": "tops"}
    result = compare_prices(no_price_item, SAMPLE_POOL)
    assert isinstance(result, str) and len(result.strip()) > 0, (
        "Expected a non-empty string for missing price"
    )
    assert "insufficient" in result.lower() or "no data" in result.lower(), (
        f"Expected no-data message, got: {result}"
    )
    print(f"PASS test_missing_price_returns_no_data_string\n  → {result}")


def test_cheap_item_rated_low():
    """An item priced well below pool average should get a LOW rating."""
    result = compare_prices(TOPS_ITEM_CHEAP, SAMPLE_POOL)
    assert isinstance(result, str) and result.strip(), "Expected non-empty string"
    assert "[LOW]" in result, (
        f"Expected [LOW] rating for $5 item vs pool avg ~$23. Got: {result}"
    )
    print(f"PASS test_cheap_item_rated_low\n  → {result}")


def test_fallback_to_load_listings_returns_string():
    """With no comparison_pool, function loads listings internally and still returns a string."""
    result = compare_prices(TOPS_ITEM_EXPENSIVE, None)
    assert isinstance(result, str) and result.strip(), (
        "Expected non-empty result when comparison_pool is None"
    )
    assert any(label in result for label in ["[LOW]", "[AVERAGE]", "[HIGH]"]), (
        f"Expected a rating label in result. Got: {result}"
    )
    print(f"PASS test_fallback_to_load_listings_returns_string\n  → {result}")


def test_average_priced_item_rated_average():
    """An item priced near the pool median should get an AVERAGE rating.

    Pool prices: 18, 20, 22, 25, 30 → sorted → $22 is at the 40th percentile,
    which falls between the 33rd and 66th thresholds → AVERAGE.
    """
    mid_item = {
        "id": "lst_test_mid",
        "title": "Vintage Knit Top",
        "category": "tops",
        "style_tags": ["vintage", "knitwear"],
        "size": "M",
        "condition": "good",
        "price": 22.00,
        "colors": ["cream"],
        "brand": None,
        "platform": "thredUp",
    }
    result = compare_prices(mid_item, SAMPLE_POOL)
    assert isinstance(result, str) and result.strip(), "Expected non-empty string"
    assert "[AVERAGE]" in result, (
        f"Expected [AVERAGE] rating for $22 item vs pool avg ~$23. Got: {result}"
    )
    print(f"PASS test_average_priced_item_rated_average\n  → {result}")


if __name__ == "__main__":
    test_missing_price_returns_no_data_string()
    test_cheap_item_rated_low()
    test_fallback_to_load_listings_returns_string()
    test_average_priced_item_rated_average()
    print("\nAll 4 tests passed.")
