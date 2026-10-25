# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
  id             str    lst_001
  title          str    Vintage Levi's 501 Jeans — Medium Wash
  description    str    Classic 501s in a perfect medium wash. Some light fading a…
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr is a thrift-shopping agent. You ask for something in plain language — *"vintage graphic tee under $30"* or *"platform sneakers size 8"* — and it searches 40 secondhand listings from Depop, Poshmark and thredUp for the best match within your size and price. It then suggests one or two outfits built around that item using pieces from your wardrobe (or general styling advice if your wardrobe is empty), and writes a short, postable caption — a "fit card" — mentioning the item, its price and where it's listed. If nothing matches, it stops before the styling steps and tells you which filter to loosen or which words to try instead.



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the secondhand listings in `data/listings.json` for items whose words match the user's description, keeping only those that fit the requested size and price ceiling, and ranks them best match first.
- **Inputs:** description (string), size (string), max_price (float); size and max_price can be None, and None means "skip that filter". `max_price` is an inclusive ceiling — a $30.00 item passes `max_price=30`.
- **Returns:** A list of up to 10 (`config.SEARCH_RESULT_LIMIT`) listing dicts, each with `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price` (float), `colors`, `brand` (str or None), `platform`. A listing is kept only if it passes the price filter, passes the size filter, and shares at least one keyword with `description` (lowercased, stopwords like "a"/"under"/"for" removed) across its title, description, category, style_tags, colors and brand. Sorted by number of shared keywords, most first. **Size rule:** the listing's size is split on `/`, anything in parentheses is dropped, and it matches if any part equals the requested size, case-insensitive — so `"M"` matches `S/M` and `M/L`, `"L"` does not match `XL`, `"8"` does not match `US 8`. Any `One Size` listing matches every size.
- **When it has nothing:** `[]` — an empty list, never `None` and never an exception. That includes a `description` with no usable keywords.
 
### `suggest_outfit`

- **What it does:** Asks the model to suggest one or two outfits built around the chosen listing, using pieces the user already owns, or general styling ideas when the wardrobe is empty.
- **Inputs:** `new_item` (dict) — one listing dict from `search_listings`; `wardrobe` (dict) — `{"items": [...]}`, where each item has `id`, `name`, `category`, `colors`, `style_tags`, `notes`. The `items` list may be empty.
- **Returns:** A non-empty string from the model describing 1–2 outfits built around `new_item`, each naming the specific wardrobe pieces it uses by their `name`.
- **When it has nothing:** If `wardrobe["items"]` is `[]`, it returns a non-empty string of general styling advice for `new_item` (what kinds of pieces to pair it with) instead of naming wardrobe pieces. It never returns `""` and never raises for an empty wardrobe.

### `create_fit_card`

- **What it does:** Asks the model to write a short, social-media-style caption for the find that mentions the item, its price, and its platform and describes the outfit's vibe.
- **Inputs:** `outfit` (str) — the string returned by `suggest_outfit`; `new_item` (dict) — the same listing dict that was passed to `suggest_outfit`.
- **Returns:** A 2–4 sentence caption string that reads like a social post, mentions the item's `title`, `price` and `platform` once each, and describes the outfit's vibe. Wording varies between runs (temperature 0.9).
- **When it has nothing:** If `outfit` is empty or whitespace-only, it returns exactly `"Can't make a fit card: no outfit suggestion was provided."` without calling the model.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns `[]`, store a message in `session["error"]` that names the filters used (description, size, max price) and says which one to loosen — or, if loosening wouldn't help, which broader words to try — then stop — `suggest_outfit` and `create_fit_card` are never called and `session["fit_card"]` stays `None`. Otherwise, store `results[0]` in `session["selected_item"]`, call `suggest_outfit` with it, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query` — no model call. `under $30` / `below 30` / `$30` → `max_price=30.0`; `size M` / `in size W30` → `size="M"`; a bare number like `size 8` becomes `"US 8"`, because that's how shoe sizes are written in the data. Filler like "looking for" is dropped, and whatever is left is the description. Either filter is `None` when the query doesn't state it.

**The empty-search message:** `agent.py::no_results_message` re-runs the search with the price limit dropped, then with the size dropped, and says which change would find something (e.g. *"drop the size — matches come in US 7, US 8, US 9"*). If neither helps, it says no listing mentions those words and suggests broader ones.

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. On an empty search, `error` is set and the last three stay `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Casual Y2K Contrast**
Pair the Y2K Baby Tee — Butterfly Print with your baggy straight-leg jeans, dark wash. Layer the black cropped zip hoodie on top, leaving it unzipped to show off the print. Finish with the chunky white sneakers and your black crossbody bag for an effortless, everyday throwback look.

**Outfit 2: Edgy Vintage Mix**
Tuck the Y2K Baby Tee — Butterfly Print into your wide-leg khaki trousers, cinched with the brown leather belt. Throw on the vintage black denim jacket and lace up your black combat boots to give the sweet butterfly graphic a cool, grunge-inspired edge.

  Fit card: Obsessed with this Y2K butterfly baby tee that just dropped in the shop for $18 on Depop! I’ve been living for baby tees lately, and this graphic is just too good. Whether you're leaning into a chill, everyday throwback vibe or styling it with some grunge edge, it's such an easy piece to throw on.
```

**The empty path** — stops after search; `session["fit_card"]` stays `None`

```
$ python app.py ask 'designer ballgown size XXS under $5'

  No listing mentions 'designer ballgown', even with size and price ignored. Try broader words — a category like 'dress', 'jacket' or 'tee', or a style like 'vintage' or 'y2k'.

0 model calls this session
```

**State check** — the item search picked is the one `suggest_outfit` received

```
selected id: lst_002 | search[0] id: lst_002 | reached suggest_outfit: lst_002 | same object: True
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit 1: Casual Coffee Run**
Pair the vintage Levi’s 501s with the white ribbed tank top tucked in. Cinch your waist with the brown leather belt, and layer the slightly cropped vintage black denim jacket on top. Finish the look with the chunky white sneakers and the black crossbody bag for an effortless, classic streetwear vibe.

**Outfit 2: Edgy Weekend Layers**
Wear the medium-wash 501s with the black cropped zip hoodie. Slip on the black combat boots, and accessorize with the black crossbody bag. For chilly days, throw the oversized grey crewneck sweatshirt over your shoulders or wear it layered underneath for a relaxed, textured silhouette.

$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
**Outfit 1: Casual Streetwear**
Pair these 501s with an oversized, thrifted graphic tee (tucked in slightly at the front) and a worn-in brown leather bomber jacket. Slip on a pair of classic canvas high-top sneakers and add a simple silver chain necklace for an effortless, everyday look.

**Outfit 2: Elevated Vintage**
Dress them up with a fitted black ribbed turtleneck layered under a boxy, thrifted tweed blazer in houndstooth or charcoal. Finish with black leather loafers worn with white athletic crew socks, and add a structured vintage leather shoulder bag.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Nothing beats the effortless 90s off-duty model vibe of a worn-in medium wash. I’m styling these with crisp white sneakers for that ultimate effortless look that goes with literally everything. Snagged these vintage Levi's 501 jeans for just $38 and I am never taking them off. Head over to my depop before someone else snatches them up!

(run 2, cache off) Nothing beats the effortless 90s off-duty model vibe of a worn-in medium wash. I’ve got these classic vintage Levi's 501 jeans paired with crisp white sneakers, and they fit like an absolute dream. Grab them over on my depop right now for $38 before I change my mind and keep them.

(run 3, cache off) Nothing beats finding the holy grail of denim while thrifting, especially when it's a classic medium wash. I’ve been living in these worn-in vintage Levi's 501 jeans styled effortlessly with crisp white sneakers for that ultimate 90s off-duty model vibe. Snagged them for just $38 and they are finally up on my depop shop waiting for a new home.

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
Can't make a fit card: no outfit suggestion was provided.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude to look over my Tool Inventory for Milestone 2 and tell me whether someone else could build the tools from it.
- *What came back:* It said my `search_listings` return line — "list of matching dictionary" — was exactly the "returns a list" the template says earns nothing, and that my `create_fit_card` empty case ("a descriptive message string") couldn't be checked by code. It also listed every size string in the data and asked me to decide what counts as a size match.
- *What I changed:* I rewrote the return line to name all 11 fields, the 10-result cap, the ranking and the size rule; fixed the empty fit-card case to one exact string the loop can recognise; and decided to keep my exact-part size rule (`"M"` matches `S/M`, `"L"` does not match `XL`).

**Moment 2**

- *What I asked for:* I had Claude wire the loop and parse the query with a regex, then run every example query from `python app.py examples` through it.
- *What came back:* `'platform sneakers size 8'` returned nothing. The parser handed the tool `"8"`, my size rule doesn't match `"8"` to `"US 8"`, and the empty-search message contradicted itself: "drop the size — matches come in US 7, US 8, US 9".
- *What I changed:* I kept the tool's size rule as specified and fixed it in the parser instead — a bare number after "size" becomes `"US 8"`, because that's how the data writes shoe sizes. Re-ran it: `size 8`, `size us8` and `size 8.5` each now find their match.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

`python run_eval.py --label before` → [results/run_2026-10-25_1536_before.md](results/run_2026-10-25_1536_before.md)
(raw sessions in the matching `.json`). Cache off, temperature 0.9, 50 real model calls.

**How the run is set up** ([scenarios.py](scenarios.py)): one scenario per criterion, five tries each.
Criteria 4 and 5 say "5 different queries", so I added a `queries` list to a scenario —
try *i* runs the *i*-th query — and a two-line change in `run_eval.py` to use it.
Criteria 1, 2 and 3 run the same query five times.

**How each try was marked** ([score_run.py](score_run.py), `check()`): I wrote each criterion
down as a check rather than eyeballing 25 runs.
1 — no `error`, a non-empty outfit, and a fit card that isn't the empty-outfit message.
2 — `error` is set, `outfit_suggestion` and `fit_card` are both still `None`, and the message says *Try / raise / drop / Add*.
3 — `selected_item.id == search_results[0].id`, and the item's platform appears in the fit card.
4 — the card splits into 2–4 sentences (on `. ! ?`, pieces of 3+ words), and contains `$<price>`.
5 — the ceiling is read from what the *user typed* (not from my parser, so a parser bug can't mark itself correct), and no result is over it.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item is search_results[0] and its platform reaches the fit card | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card is 2–4 sentences and contains the price with a $ | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every search result is within the stated price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output, one try per criterion.** All produced by `agent.py::run_agent`, run by
`run_eval.py::run_once`; the tool named in each block is the one that wrote the text.

*Criterion 1, try 1* — `vintage graphic tee under $30`. Trace from `agent.py::_run_step`, card from `tools.py::create_fit_card`:

```
[1] parse_query
      in:  'vintage graphic tee under $30'
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: results — continuing
[3] select_item
      in:  search_results[0]
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  new_item=lst_002, wardrobe=10 items
      out: **Outfit 1: Casual Y2K Streetwear** Pair the Y2K Baby Tee — Butterfly Print with your baggy straight-leg jeans…
[5] create_fit_card
      in:  outfit=<647 chars>, new_item=lst_002
      out: Found the ultimate Y2K butterfly tee and honestly might keep this one for myself, but it’s currently live on d…

fit_card: Found the ultimate Y2K butterfly tee and honestly might keep this one for myself, but it’s currently live on depop for $18. Style it casual with baggy denim and an unzipped hoodie, or tuck it into khaki trousers with combat boots for that perfect sweet-meets-edgy vintage vibe. Grab it before I change my mind!
```

*Criterion 2, try 1* — `designer ballgown size XXS under $5`. Message from `agent.py::no_results_message`:

```
[1] parse_query
      in:  'designer ballgown size XXS under $5'
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty — stopping before suggest_outfit

error:             No listing mentions 'designer ballgown', even with size and price ignored. Try broader words — a category like 'dress', 'jacket' or 'tee', or a style like 'vintage' or 'y2k'.
outfit_suggestion: None
fit_card:          None
```

*Criterion 3, try 1* — `90s track jacket in size M`. Session fields set by `agent.py::_run_step`, card from `tools.py::create_fit_card`:

```
selected_item.id:     lst_004
search_results[0].id: lst_004
platform:             poshmark
fit_card: Obsessed with this vintage 90s track jacket and how effortlessly cool it looks dressed up with khakis or kept casual with baggy denim. I’ve got it listed on Poshmark for just $45, and it’s the ultimate sporty-chic layering piece for your wardrobe. Grab it before it’s gone!
```

*Criterion 4, try 4* — `platform sneakers size 8`, lst_019 at $48. Card from `tools.py::create_fit_card`:

```
Just scored these chunky platform sneakers on Poshmark for only $48 and I am obsessed! They are giving the ultimate 90s skater vibe paired with my baggy jeans and vintage denim jacket, but they look just as good with wide-leg trousers for an effortless Y2K casual-cool fit. Run, don't walk, to check out my Poshmark closet before I change my mind and keep them both!
```

*Criterion 5, try 4* — `y2k top for less than $20`. Parsed by `agent.py::parse_query`, results from `search_listings` over MCP (`mcp_server.py` → `tools.py::search_listings`):

```
parsed: {'description': 'y2k top for', 'size': None, 'max_price': 20.0}
search_results:
  lst_017  Mesh Long-Sleeve Top — Black       15.0
  lst_002  Y2K Baby Tee — Butterfly Print     18.0
  lst_026  Biker Shorts — Black, Shiny        14.0
  lst_035  Low-Top Canvas Sneakers — Off-White 20.0
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

Trace calls live in `agent.py::_run_step` — one `trace.step()` per step,
called by `agent.py::run_agent`. Step 2 is the MCP call.

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  'vintage graphic tee under $30'
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: results — continuing
[3] select_item
      in:  search_results[0]
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  new_item=lst_002, wardrobe=10 items
      out: **Outfit 1: Casual Y2K Contrast** Pair the Y2K Baby Tee — Butterfly Print with your baggy straight-leg jeans, …
[5] create_fit_card
      in:  outfit=<604 chars>, new_item=lst_002
      out: Obsessed with this Y2K butterfly baby tee that just dropped in the shop for $18 on Depop! I’ve been living for…
```

**Empty search** — two steps, not five. The branch stops it.

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  'designer ballgown size XXS under $5'
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    branch: empty — stopping before suggest_outfit

  No listing mentions 'designer ballgown', even with size and price ignored. Try broader words — a category like 'dress', 'jacket' or 'tee', or a style like 'vintage' or 'y2k'.
```

### The three failures, triggered on purpose

**1. Empty search** — handled already in unit 3 by `agent.py::no_results_message`.
Two different messages depending on what's in the way:

```
$ python app.py ask 'designer ballgown size XXS under $5'
  No listing mentions 'designer ballgown', even with size and price ignored. Try broader words — a category like 'dress', 'jacket' or 'tee', or a style like 'vintage' or 'y2k'.

$ python app.py ask 'platform sneakers size 7 under $10'
  Nothing matched 'platform sneakers' in size US 7 under $10. To find something, raise your price limit — the cheapest match is $55.
```

**2. Empty wardrobe** — `tools.py::suggest_outfit` already had an empty-wardrobe
prompt, so this returned general advice first time, no change needed:

```
$ python app.py ask 'denim jacket under $50' --empty-wardrobe
(running with an empty wardrobe)

  Found:    Denim Jacket — Light Wash, Cropped — $42.0 on poshmark

  Outfit:   **Outfit 1: Retro Casual**
Layer the cropped Wrangler jacket over a fitted, ribbed black turtleneck. Pair with high-waisted, wide-leg beige corduroy trousers to balance the proportions. Finish with well-worn canvas high-top sneakers and a simple leather shoulder bag for an effortless, texture-rich look. …
```

**3. Model unavailable** (one character of the key changed, cache off). *Before
the handler* the agent itself didn't catch it — `app.py`'s catch-all printed the
exception class and exited with status 1, throwing away the listing the search
had already found:

```
$ python app.py ask 'corduroy pants size W29'
ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

*After* — `agent.py::run_agent` catches `ModelUnavailable`, and
`agent.py::model_unavailable_message` says which step needed the model, keeps
what was found, and says what to do:

```
$ python app.py ask 'corduroy pants size W29' --trace
…
[4] suggest_outfit
      →    stopped: model unavailable — The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

  Found Low-Rise Cargo Pants — Khaki ($27 on poshmark), but couldn't reach the AI model to suggest an outfit. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. The search itself still works — once the key is fixed, ask again.
```

I also added a handler for the MCP server not answering (pointed `mcp_client.SERVER`
at a file that doesn't exist), since that's a new way for step 2 to fail now:

```
Couldn't reach the listings search (the MCP server in mcp_server.py didn't answer), so nothing was searched. Run `python mcp_client.py` to check the server starts, then ask again.
```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
