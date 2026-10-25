"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config  # noqa: F401 — MAX_ITERATIONS is read through trace.check_iterations
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    # Each pass runs one step, and the step decides the next one from what it
    # just put in the session. Values go in and back out through `session`.
    step = "parse"
    count = 0
    while step != "done":
        count += 1
        trace.check_iterations(count)

        if step == "parse":
            session["parsed"] = parse_query(session["query"])
            step = "search"

        elif step == "search":
            p = session["parsed"]
            session["search_results"] = search_listings(
                p["description"], size=p["size"], max_price=p["max_price"]
            )
            # THE BRANCH: nothing found → say what to change and stop here.
            if not session["search_results"]:
                session["error"] = no_results_message(session["parsed"])
                step = "done"
            else:
                step = "select"

        elif step == "select":
            session["selected_item"] = session["search_results"][0]
            step = "suggest"

        elif step == "suggest":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            step = "fit_card"

        elif step == "fit_card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            step = "done"

    return session


# ── query parsing (regex) ─────────────────────────────────────────────────────

_PRICE = re.compile(
    r"\b(?:under|below|less than|up to|max|at most)\s*\$?\s*(\d+(?:\.\d+)?)"
    r"|\$\s*(\d+(?:\.\d+)?)",
    re.I,
)
_SIZE = re.compile(r"\b(?:in\s+)?size\s+(us\s*\d+(?:\.\d+)?|[a-z0-9./]+)", re.I)
_FILLER = re.compile(r"\b(?:i'?m\s+)?(?:looking for|i want|i need|find me|show me)\b", re.I)


def parse_query(query: str) -> dict:
    """
    Pull a description, a size and a max_price out of plain language.

    "vintage graphic tee under $30, size M"
        → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}

    Size and price are None when the query doesn't state them. Whatever is
    left after removing them (and filler like "looking for") is the description.
    """
    text = query or ""

    max_price = None
    price_match = _PRICE.search(text)
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))
        text = text[: price_match.start()] + " " + text[price_match.end():]

    size = None
    size_match = _SIZE.search(text)
    if size_match:
        size = " ".join(size_match.group(1).upper().split())
        # A bare number is a shoe size, and the data writes those as "US 8".
        if re.fullmatch(r"\d+(?:\.\d+)?", size):
            size = f"US {size}"
        elif re.fullmatch(r"US\d+(?:\.\d+)?", size):
            size = f"US {size[2:]}"
        text = text[: size_match.start()] + " " + text[size_match.end():]

    text = _FILLER.sub(" ", text)
    description = " ".join(re.sub(r"[,;]+", " ", text).split())
    return {"description": description, "size": size, "max_price": max_price}


def no_results_message(parsed: dict) -> str:
    """
    Say what the user could change, not just that nothing matched.

    Re-runs the search with one filter dropped at a time, so the message can
    point at the filter that's actually in the way.
    """
    description, size, max_price = parsed["description"], parsed["size"], parsed["max_price"]

    asked = f"'{description}'" if description else "an empty description"
    if size:
        asked += f" in size {size}"
    if max_price is not None:
        asked += f" under ${max_price:g}"

    if not description:
        return (
            f"Nothing matched {asked}. Add a few words describing the item — "
            f"for example 'denim jacket' or 'graphic tee'."
        )

    hints = []
    if max_price is not None:
        found = search_listings(description, size=size)
        if found:
            cheapest = min(item["price"] for item in found)
            hints.append(
                f"raise your price limit — the cheapest match is ${cheapest:g}"
            )
    if size:
        found = search_listings(description, max_price=max_price)
        if found:
            sizes = sorted({item["size"] for item in found})[:4]
            hints.append(
                f"drop the size — matches come in {', '.join(sizes)}"
            )

    if hints:
        return f"Nothing matched {asked}. To find something, " + ", or ".join(hints) + "."
    return (
        f"No listing mentions {description!r}, even with size and price ignored. "
        f"Try broader words — a category like 'dress', 'jacket' or 'tee', or a "
        f"style like 'vintage' or 'y2k'."
    )


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
