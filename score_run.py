#!/usr/bin/env python3
"""
Mark each try in a run_eval.py log PASS or FAIL against criteria.md.

    python score_run.py results/run_2026-10-25_1600_before.json

run_eval.py leaves the verdict blank on purpose. This is where I wrote down
what each criterion means as a check, so the marking is the same every time
and anyone can read exactly what counted as a pass.
"""

import json
import re
import sys

from tools import EMPTY_OUTFIT_MESSAGE

TARGETS = {1: 4, 2: 5, 3: 5, 4: 4, "4r": 4, 5: 5}  # passes needed out of 5, from criteria.md
NAMES = {
    1: "A matching query completes all three tools",
    2: "An impossible query stops before the second tool",
    3: "Selected item is search_results[0] and its platform reaches the fit card",
    4: "Fit card is 2–4 sentences and contains the price with a $",
    5: "Every search result is within the stated price ceiling",
    "4r": "Fit card is 2–4 sentences, has the $ price, and is in the shopper's voice",
}

# Criterion 4, revised in unit 4: phrases that only make sense if the poster is
# selling the item — claiming the listing as theirs, or telling readers to buy.
SELLER_VOICE = re.compile(
    r"\bmy (depop|poshmark|thredup|shop|closet)\b"
    r"|\b(listed|listing|live on|up on|in the shop|just dropped)\b"
    r"|\b(grab|snag) (it|this|them)\b|head over|check out my|run, don.t walk"
    r"|before (i|someone else) |keep (it|them) (for myself|both)",
    re.I,
)


def sentences(text: str) -> list[str]:
    """Split on . ! ? followed by whitespace. A piece counts if it has 3+ words."""
    pieces = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in pieces if len(re.findall(r"[A-Za-z]+", p)) >= 3]


def price_in(text: str, price: float) -> bool:
    forms = {f"{price:g}", f"{price:.2f}"}
    return any(re.search(rf"\${re.escape(f)}(?!\d)", text) for f in forms)


def completed(s: dict) -> tuple[bool, str]:
    if s.get("error"):
        return False, f"stopped early: {s['error'][:80]}"
    if not s.get("outfit_suggestion"):
        return False, "no outfit suggestion"
    card = s.get("fit_card") or ""
    if not card.strip() or card == EMPTY_OUTFIT_MESSAGE:
        return False, f"no fit card: {card!r}"
    return True, ""


def check(criterion: int, record: dict) -> tuple[bool, str]:
    if record.get("crashed"):
        return False, f"crashed: {record['crashed']}"
    s = record["session"]

    if criterion == 1:
        ok, why = completed(s)
        return ok, why or f"fit card {len(s['fit_card'])} chars"

    if criterion == 2:
        if not s.get("error"):
            return False, "did not stop"
        if s.get("outfit_suggestion") is not None or s.get("fit_card") is not None:
            return False, "stopped, but a later tool had already run"
        if not re.search(r"\b(Try|raise|drop|Add)\b", s["error"]):
            return False, f"message doesn't say what to change: {s['error']!r}"
        return True, s["error"][:80]

    ok, why = completed(s)
    if criterion in (3, 4) and not ok:
        return False, why

    if criterion == 3:
        sel, first = s["selected_item"]["id"], s["search_results"][0]["id"]
        platform = s["selected_item"]["platform"]
        if sel != first:
            return False, f"selected {sel} but search_results[0] is {first}"
        if platform.lower() not in s["fit_card"].lower():
            return False, f"{sel} matches, but fit card never says {platform!r}"
        return True, f"{sel} == {first}; card names {platform}"

    if criterion == 4:
        item = s["selected_item"]
        n = len(sentences(s["fit_card"]))
        has_price = price_in(s["fit_card"], item["price"])
        why = f"{item['id']}: {n} sentences, ${item['price']:g} {'found' if has_price else 'MISSING'}"
        return (2 <= n <= 4 and has_price), why

    if criterion == "4r":
        ok, why = check(4, record)
        seller = SELLER_VOICE.search(s["fit_card"])
        if seller:
            return False, f"{why}; seller voice: {seller.group(0)!r}"
        return ok, f"{why}; shopper voice"

    if criterion == 5:
        # The ceiling comes from what the user typed, not from the parser —
        # otherwise a parser bug would mark itself correct.
        ceiling = float(re.search(r"\$(\d+(?:\.\d+)?)", record["query"]).group(1))
        prices = [r["price"] for r in s.get("search_results") or []]
        over = [p for p in prices if p > ceiling]
        if over:
            return False, f"ceiling ${ceiling:g}, results over it: {over}"
        return True, f"ceiling ${ceiling:g}: {len(prices)} results, max ${max(prices, default=0):g}"

    raise ValueError(criterion)


def main(path: str) -> None:
    rows = json.load(open(path, encoding="utf-8"))
    table = ["| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |",
             "|---|---|---|---|---|---|---|---|"]
    details = []
    for row in rows:
        c = row["scenario"].get("criterion")
        if not c:
            continue
        for crit in ([c, "4r"] if c == 4 else [c]):
            results = [check(crit, r) for r in row["tries"]]
            passes = sum(ok for ok, _ in results)
            verdict = "MET" if passes >= TARGETS[crit] else "MISSED"
            cells = " | ".join("PASS" if ok else "FAIL" for ok, _ in results)
            label = "4 (revised)" if crit == "4r" else f"{crit}."
            table.append(f"| {label} {NAMES[crit]} | {TARGETS[crit]} of 5 | {cells} | {verdict} ({passes}/5) |")
            details.append(f"\nCriterion {label}:")
            for i, ((ok, why), r) in enumerate(zip(results, row["tries"]), 1):
                details.append(f"  try {i} {'PASS' if ok else 'FAIL'}  [{r['query']}]  {why}")
    cards = [r["session"]["fit_card"] for row in rows for r in row["tries"]
             if not r.get("crashed") and (r["session"] or {}).get("fit_card")]
    seller = sum(bool(SELLER_VOICE.search(c)) for c in cards)
    print("\n".join(table))
    print("\n".join(details))
    print(f"\nAcross every scenario: {seller} of {len(cards)} fit cards in seller voice.")


if __name__ == "__main__":
    main(sys.argv[1])
