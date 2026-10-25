"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3 — state. Any matching query; what's checked is the
        # session: selected_item is search_results[0], and its platform
        # reaches the fit card.
        "name": "selected item reaches the fit card",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4 says "5 different matching queries", so each try runs a
        # different one (try i uses queries[i-1]) — five different items.
        "name": "fit card is 2-4 sentences and states the price",
        "query": "vintage graphic tee under $30",
        "queries": [
            "vintage graphic tee under $30",
            "90s track jacket in size M",
            "silk slip dress in midi length under $40",
            "platform sneakers size 8",
            "denim jacket under $50",
        ],
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5 — five different price ceilings, phrased five ways
        # ("under", "less than", "max"). Two of them have a listing priced at
        # exactly the ceiling, so the inclusive boundary gets tested.
        "name": "price ceiling is respected",
        "query": "vintage graphic tee under $30",
        "queries": [
            "vintage graphic tee under $30",
            "silk slip dress in midi length under $40",
            "denim jacket under $50",
            "y2k top for less than $20",
            "oversized sweater max $25",
        ],
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
]


def query_for(scenario: dict, attempt: int) -> str:
    """The query for try `attempt` (1-based): cycles through "queries" if given."""
    queries = scenario.get("queries")
    if queries:
        return queries[(attempt - 1) % len(queries)]
    return scenario["query"]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
