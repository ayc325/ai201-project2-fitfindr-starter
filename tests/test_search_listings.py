"""
Three test cases for search_listings.

Test 1: keyword match returns relevant results
Test 2: max_price filter excludes expensive items
Test 3: size filter restricts results
"""

from tools import search_listings


def test_keyword_match():
    """Searching 'vintage graphic tee' should return tops with matching tags."""
    results = search_listings("vintage graphic tee")
    assert len(results) > 0, "Expected results for 'vintage graphic tee'"
    titles = [r["title"].lower() for r in results]
    assert any("tee" in t or "graphic" in t for t in titles), (
        f"Expected a graphic tee in results, got: {titles}"
    )
    print(f"PASS test_keyword_match — {len(results)} results, top: {results[0]['title']}")


def test_max_price_filter():
    """All returned items must be at or below max_price."""
    max_price = 25.0
    results = search_listings("jacket denim vintage", max_price=max_price)
    for item in results:
        assert item["price"] <= max_price, (
            f"Item '{item['title']}' costs ${item['price']} > max ${max_price}"
        )
    print(f"PASS test_max_price_filter — {len(results)} results under ${max_price}")


def test_size_filter():
    """All returned items must contain the requested size string (case-insensitive)."""
    size = "M"
    results = search_listings("streetwear outerwear", size=size)
    for item in results:
        assert size.lower() in item["size"].lower(), (
            f"Item '{item['title']}' has size '{item['size']}', expected to contain '{size}'"
        )
    print(f"PASS test_size_filter — {len(results)} results in size '{size}'")


if __name__ == "__main__":
    test_keyword_match()
    test_max_price_filter()
    test_size_filter()
    print("\nAll 3 tests passed.")
