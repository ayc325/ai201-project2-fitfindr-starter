"""
Three test cases for create_fit_card.

Test 1: empty outfit string → returns an error message string (no exception)
Test 2: valid inputs → returns a non-empty string that mentions item name, price, and platform
Test 3: different inputs produce different captions (temperature > 0 gives variety)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools import create_fit_card

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


def test_empty_outfit_returns_error_string():
    """Empty or whitespace outfit must return an error string, not raise."""
    for bad_input in ["", "   ", "\n"]:
        result = create_fit_card(bad_input, SAMPLE_ITEM)
        assert isinstance(result, str) and len(result.strip()) > 0, (
            f"Expected non-empty error string for empty outfit, got: {repr(result)}"
        )
        assert "error" in result.lower() or "no outfit" in result.lower(), (
            f"Expected error message for empty outfit, got: {result}"
        )
    print("PASS test_empty_outfit_returns_error_string")


def test_valid_inputs_mention_item_details():
    """Caption should reference the item name, price, and platform."""
    result = create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM)
    assert isinstance(result, str) and len(result.strip()) > 0, (
        "Expected non-empty caption string"
    )
    result_lower = result.lower()
    title_words = [w.lower() for w in SAMPLE_ITEM["title"].split() if len(w) > 3]
    assert any(w in result_lower for w in title_words), (
        f"Expected item name words in caption. Title words: {title_words}\nCaption: {result}"
    )
    assert str(int(SAMPLE_ITEM["price"])) in result or f"{SAMPLE_ITEM['price']:.2f}" in result, (
        f"Expected price ${SAMPLE_ITEM['price']} mentioned in caption.\nCaption: {result}"
    )
    assert SAMPLE_ITEM["platform"].lower() in result_lower, (
        f"Expected platform '{SAMPLE_ITEM['platform']}' mentioned in caption.\nCaption: {result}"
    )
    print(f"PASS test_valid_inputs_mention_item_details\n  → {result[:120]}...")


def test_different_inputs_produce_different_captions():
    """Two calls with meaningfully different outfits should produce different captions."""
    outfit_a = (
        "Grunge look: graphic tee tucked into dark jeans with combat boots and denim jacket."
    )
    outfit_b = (
        "Soft aesthetic: graphic tee knotted over a floral midi skirt with white ballet flats."
    )
    result_a = create_fit_card(outfit_a, SAMPLE_ITEM)
    result_b = create_fit_card(outfit_b, SAMPLE_ITEM)
    assert result_a != result_b, (
        "Expected different captions for different outfit inputs, got identical results."
    )
    print(f"PASS test_different_inputs_produce_different_captions")
    print(f"  Caption A: {result_a[:80]}...")
    print(f"  Caption B: {result_b[:80]}...")


if __name__ == "__main__":
    test_empty_outfit_returns_error_string()
    test_valid_inputs_mention_item_details()
    test_different_inputs_produce_different_captions()
    print("\nAll 3 tests passed.")
