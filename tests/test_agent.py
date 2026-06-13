"""
tests/test_agent.py

Integration tests for run_agent() — verifies the full planning loop.

Test 1: Happy path — valid query returns populated outfit_suggestion and fit_card
Test 2: No-results query — error is set, downstream fields are None
Test 3: Empty wardrobe — error is set after search, fit_card is None
Test 4: Price keywords trigger compare_prices (price_context is populated)
Test 5: max_price in query triggers compare_prices
Test 6: Neutral query without price concern leaves price_context as None
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── run_agent integration tests ───────────────────────────────────────────────

def test_happy_path_returns_full_session():
    """Valid query + real wardrobe → all output fields populated, no error."""
    session = run_agent("vintage graphic tee", wardrobe=get_example_wardrobe())
    assert session["error"] is None, f"Unexpected error: {session['error']}"
    assert len(session["search_results"]) > 0
    assert session["selected_item"] is not None
    assert isinstance(session["outfit_suggestion"], str) and session["outfit_suggestion"].strip()
    assert isinstance(session["fit_card"], str) and session["fit_card"].strip()
    print(f"PASS test_happy_path_returns_full_session")
    print(f"  Found: {session['selected_item']['title']}")
    print(f"  Fit card: {session['fit_card'][:80]}...")


def test_no_results_sets_error():
    """Impossible query → error message set, downstream fields stay None."""
    session = run_agent("designer ballgown size XXS under $5", wardrobe=get_example_wardrobe())
    assert session["error"] is not None, "Expected an error for no-results query"
    assert session["outfit_suggestion"] is None
    assert session["fit_card"] is None
    print(f"PASS test_no_results_sets_error → {session['error']}")


def test_empty_wardrobe_sets_error():
    """Valid search + empty wardrobe → error set, fit_card stays None."""
    session = run_agent("vintage graphic tee", wardrobe=get_empty_wardrobe())
    assert session["error"] is not None, "Expected error for empty wardrobe"
    assert len(session["search_results"]) > 0, "Search should still succeed"
    assert session["fit_card"] is None
    print(f"PASS test_empty_wardrobe_sets_error → {session['error']}")


def test_price_keyword_triggers_compare_prices():
    """Query containing a price-concern keyword → price_context is populated."""
    session = run_agent("is this flannel a good deal", wardrobe=get_example_wardrobe())
    assert session["error"] is None, f"Unexpected error: {session['error']}"
    assert session["price_context"] is not None, (
        "Expected price_context to be set when query contains 'good deal'"
    )
    print(f"PASS test_price_keyword_triggers_compare_prices → {session['price_context'][:60]}...")


def test_max_price_in_query_triggers_compare_prices():
    """Query with explicit max_price → price_context is populated."""
    session = run_agent("denim jacket under $50", wardrobe=get_example_wardrobe())
    assert session["error"] is None, f"Unexpected error: {session['error']}"
    assert session["parsed"]["max_price"] == 50.0
    assert session["price_context"] is not None, (
        "Expected price_context to be set when max_price is in query"
    )
    print(f"PASS test_max_price_in_query_triggers_compare_prices → {session['price_context'][:60]}...")


def test_neutral_query_skips_compare_prices():
    """Query with no price concern → price_context stays None."""
    session = run_agent("cozy cardigan", wardrobe=get_example_wardrobe())
    assert session["error"] is None, f"Unexpected error: {session['error']}"
    assert session["price_context"] is None, (
        f"Expected price_context to be None for neutral query, got: {session['price_context']}"
    )
    print("PASS test_neutral_query_skips_compare_prices")


if __name__ == "__main__":
    test_happy_path_returns_full_session()
    test_no_results_sets_error()
    test_empty_wardrobe_sets_error()
    test_price_keyword_triggers_compare_prices()
    test_max_price_in_query_triggers_compare_prices()
    test_neutral_query_skips_compare_prices()

    print("\nAll 6 tests passed.")
