"""
app.py

Gradio interface for FitFindr. The layout and wiring are already set up —
your job is to fill in handle_query() so it calls run_agent() and maps
the session results to the three output panels.

Run with:
    python app.py

Then open the localhost URL shown in your terminal (usually http://localhost:7860,
but check your terminal — the port may differ).
"""

import json

import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe
from tools import _get_groq_client


# ── wardrobe parser ───────────────────────────────────────────────────────────

def parse_wardrobe_from_query(query: str) -> dict:
    """
    Extract wardrobe items a user mentions in their query and return a wardrobe dict.

    e.g. "looking for a graphic tee, I mostly wear baggy jeans and chunky sneakers"
         → wardrobe with two items: baggy jeans (bottoms) + chunky sneakers (shoes)

    Falls back to an empty wardrobe if no clothing items are mentioned.
    """
    client = _get_groq_client()
    prompt = (
        "A user typed this query into a thrift-shopping app:\n\n"
        f"\"{query}\"\n\n"
        "Extract any clothing items they mention owning or usually wearing "
        "(ignore what they are searching for). "
        "Return ONLY a valid JSON object with this structure:\n"
        '{\n  "items": [\n    {\n      "id": "w_001",\n      "name": "item name",\n'
        '      "category": "tops|bottoms|shoes|outerwear|accessories",\n'
        '      "colors": ["color1"],\n      "style_tags": ["tag1"],\n      "notes": ""\n    }\n  ]\n}\n\n'
        "Rules:\n"
        "- Only include items the user says they own or wear — not what they want to buy\n"
        "- category must be one of: tops, bottoms, shoes, outerwear, accessories\n"
        "- style_tags should be descriptors like: vintage, casual, streetwear, minimal, grunge\n"
        "- Generate sequential ids: w_001, w_002, etc.\n"
        "- If no wardrobe items are mentioned, return {\"items\": []}\n"
        "- Return only the JSON, no explanation."
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return get_empty_wardrobe()


# ── query handler ─────────────────────────────────────────────────────────────

def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    """
    Called by Gradio when the user submits a query.

    Args:
        user_query:      The text the user typed into the search box.
        wardrobe_choice: Either "Example wardrobe" or "My wardrobe (describe in query)".

    Returns:
        A tuple of three strings:
            (listing_text, outfit_suggestion, fit_card)
        Each string maps to one of the three output panels in the UI.
    """
    # Step 1: Guard against empty query
    if not user_query or not user_query.strip():
        return "Please enter a search query.", "", ""

    # Step 2: Select wardrobe — for new users, extract wardrobe items from the query itself
    if wardrobe_choice == "Example wardrobe":
        wardrobe = get_example_wardrobe()
    else:
        wardrobe = parse_wardrobe_from_query(user_query)

    # Step 3: Run the agent
    session = run_agent(query=user_query, wardrobe=wardrobe)

    # Step 4: Surface errors in the first panel
    if session["error"]:
        return session["error"], "", ""

    # Step 5: Format the top listing and return all three panels
    item = session["selected_item"]
    listing_text = (
        f"{item['title']}\n"
        f"Price: ${item['price']:.2f}  |  Platform: {item['platform']}\n"
        f"Size: {item['size']}  |  Condition: {item['condition']}\n"
        f"Colors: {', '.join(item['colors'])}\n"
        f"Tags: {', '.join(item['style_tags'])}\n\n"
        f"{item['description']}"
    )
    if session.get("price_context"):
        listing_text += f"\n\n💰 Price check: {session['price_context']}"

    return listing_text, session["outfit_suggestion"], session["fit_card"]


# ── interface ─────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "flowy midi skirt under $40",
    "black combat boots size 8",
    "designer ballgown size XXS under $5",   # deliberate no-results test
]

def build_interface():
    with gr.Blocks(title="FitFindr") as demo:
        gr.Markdown("""
# FitFindr 🛍️
Find secondhand pieces and get outfit ideas based on your wardrobe.
Describe what you're looking for — include size and price if you want to filter.
        """)

        with gr.Row():
            query_input = gr.Textbox(
                label="What are you looking for?",
                placeholder="e.g. vintage graphic tee under $30, size M",
                lines=2,
                scale=3,
            )
            wardrobe_choice = gr.Radio(
                choices=["Example wardrobe", "My wardrobe (describe in query)"],
                value="Example wardrobe",
                label="Wardrobe",
                info="Select 'My wardrobe' and mention what you own in your query — e.g. 'I mostly wear baggy jeans and chunky sneakers'",
                scale=1,
            )

        submit_btn = gr.Button("Find it", variant="primary")

        with gr.Row():
            listing_output = gr.Textbox(
                label="🛍️ Top listing found",
                lines=8,
                interactive=False,
            )
            outfit_output = gr.Textbox(
                label="👗 Outfit idea",
                lines=8,
                interactive=False,
            )
            fitcard_output = gr.Textbox(
                label="✨ Your fit card",
                lines=8,
                interactive=False,
            )

        gr.Examples(
            examples=[
                *[[q, "Example wardrobe"] for q in EXAMPLE_QUERIES],
                [
                    "I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.",
                    "My wardrobe (describe in query)",
                ],
            ],
            inputs=[query_input, wardrobe_choice],
            label="Try these queries",
        )

        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )
        query_input.submit(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()
