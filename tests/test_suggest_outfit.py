"""
Three test cases for suggest_outfit.

Test 1: empty wardrobe → returns general styling advice (non-empty string)
Test 2: populated wardrobe → response mentions at least one wardrobe piece by name
Test 3: return type is always a non-empty string regardless of input
"""

from tools import suggest_outfit
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

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


def test_empty_wardrobe_returns_general_advice():
    """With an empty wardrobe the function should still return a non-empty suggestion."""
    empty = get_empty_wardrobe()
    result = suggest_outfit(SAMPLE_ITEM, empty)
    assert isinstance(result, str), "Expected a string return value"
    assert len(result.strip()) > 0, "Expected non-empty styling advice for empty wardrobe"
    print(f"PASS test_empty_wardrobe_returns_general_advice\n  → {result[:120]}...")


def test_populated_wardrobe_references_wardrobe_items():
    """With a real wardrobe the response should mention at least one named piece."""
    wardrobe = get_example_wardrobe()
    wardrobe_names = [item["name"].lower() for item in wardrobe["items"]]
    result = suggest_outfit(SAMPLE_ITEM, wardrobe)
    assert isinstance(result, str) and len(result.strip()) > 0, "Expected non-empty string"
    result_lower = result.lower()
    matched = [name for name in wardrobe_names if any(word in result_lower for word in name.split())]
    assert len(matched) > 0, (
        f"Expected at least one wardrobe item referenced in response.\n"
        f"Wardrobe items: {wardrobe_names}\nResponse: {result}"
    )
    print(f"PASS test_populated_wardrobe_references_wardrobe_items\n  → matched items: {matched[:3]}")


def test_return_is_always_string():
    """Result must be a non-empty string for both empty and populated wardrobes."""
    for wardrobe, label in [(get_empty_wardrobe(), "empty"), (get_example_wardrobe(), "populated")]:
        result = suggest_outfit(SAMPLE_ITEM, wardrobe)
        assert isinstance(result, str) and result.strip(), (
            f"Expected non-empty string for {label} wardrobe, got: {repr(result)}"
        )
    print("PASS test_return_is_always_string — both empty and populated wardrobes return strings")


if __name__ == "__main__":
    test_empty_wardrobe_returns_general_advice()
    test_populated_wardrobe_references_wardrobe_items()
    test_return_is_always_string()
    print("\nAll 3 tests passed.")
