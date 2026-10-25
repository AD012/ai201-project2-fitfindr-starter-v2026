# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->
My search is a plain keyword match and my size rule is exact — "8" doesn't
match "US 8" — so a reasonable phrasing of a query that *should* match can
still come back empty. Two of the three calls also go to a rate-limited model,
so one try in five failing on something outside my code is plausible; two in
five would mean something is actually wrong.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->
This path never touches the model. Query parsing is a regex and the search is
plain Python over a fixed file, so the same query gives the same empty list
every time, and the branch on `[]` either works or it doesn't. Anything less
than 5 of 5 would mean the branch is broken, not unlucky.

---

## 3. Something about state

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

Given a query that matches at least one listing, `session["selected_item"]["id"]`
equals `session["search_results"][0]["id"]`, and the fit card in
`session["fit_card"]` names that same item's platform — in 5 of 5 tries.

**Why this target:**
The loop reads `selected_item` out of the session and passes that one dict to
both `suggest_outfit` and `create_fit_card`, with no model step in between, so
there's no randomness that could swap the item. The platform check is there
because the id comparison alone only proves the session is consistent with
itself — the platform showing up in the card is what proves the item actually
reached the last tool. If this misses even once, the state is wrong.


---

## 4. Something about the fit card

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

For 5 different matching queries, each fit card is 2 to 4 sentences long and
contains the selected item's price written with a dollar sign (e.g. `$24`) —
in at least 4 of 5 tries.

**Why this target:**
The prompt asks for 2–4 sentences and the price once, but at temperature 0.9
the model doesn't always follow length or formatting instructions — it might
write "24.0", or drop the price for a vibe-only caption. One slip in five is
the model being a model; two would mean my prompt isn't clear enough. I'm not
requiring identical wording because varied wording is the point of the card.

> **Revised in unit 4:** For 5 different matching queries, each fit card is 2 to
> 4 sentences long, contains the selected item's price written with a dollar
> sign, **and is written as the shopper who found the item** — it never presents
> the item as the poster's own listing ("up on my Depop", "I've got it listed")
> or tells readers to go buy it ("grab it", "head over", "before I change my
> mind") — in at least 4 of 5 tries. Seller voice is checked by a fixed phrase
> list in `score_run.py::SELLER_VOICE`.
>
> **Why revised:** the original measured the wrong thing. It came out 5 of 5 in
> the before run while 21 of the 25 fit cards in that run were written as a
> seller advertising their own listing — to a user who is deciding whether to
> *buy* the item. Length and price are format; a card the user can't post
> without lying about owning a Depop shop isn't a working fit card, and the
> original criterion couldn't see that. The target stays 4 of 5 for the same
> reason as before.


---

## 5. Your choice

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

**The price ceiling is respected.** For 5 queries that state a price
("under $30", "under $50", …), every listing in `session["search_results"]` has
a `price` less than or equal to the stated number — 5 of 5 tries.

**Why this target:**
A thrift search that shows you a $45 jacket after you said "under $30" is the
failure I'd be most annoyed by as a user. Both the regex that pulls the number
out of the query and the `<=` filter are deterministic, so there's no reason
for this to ever fail once it's right — 5 of 5 is the only honest target.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
