# T01 — Clickable mockup of Today, customer page and reminder sheet
**Status:** TODO
**Prereqs:** — · **Branch:** t01-mockup

## Goal

Ankur can tap through the new design on a phone before any real code changes: the Today list, a customer page and
the send-reminder sheet, in the ledger style. Its CSS becomes the real app's stylesheet in T06.

Start of the interface track: T01 → T06 → T07 / T11 → … PLAN.md §Screens, §Look, §Words.

## Scope / files

- `mockup/index.html`: one self-contained page (inline CSS and JS, no build step) with the three screens, switched
  by the bottom bar and by tapping rows. A fixed copy of the demo data is inlined as a JS object (Assumed 8).
- `mockup/style.css`: the stylesheet, written so T06 can copy it into `static/style.css`: tokens on `:root`, dark
  mode under `@media (prefers-color-scheme: dark)`, shared components (bottom bar, top bar, row, amount, sheet,
  button, toast, field), then the screen sections named in PLAN.md §Front-end structure.
- Publish `mockup/index.html` as a private artifact (inline the CSS for the published copy) so Ankur can open it on
  a phone.

## Details

- Get the demo data: run the app (`.venv/bin/python app.py`), `curl localhost:5055/api/book`, and hand-write the
  Today rows from it as PLAN.md §Today rules would produce them. Include one broken promise row ("Promised ₹5
  lakh by 12 Nov. Not received.") and one Coming up row.
- **Today:** one totals line, a **Late** group, a **Coming up** group, rows as in PLAN.md §Today (name, amount,
  why line, **Send reminder**). One row per customer.
- **Customer page:** the five sections in the order of PLAN.md §Customer page. Use Sharma Knit Processors.
- **Reminder sheet:** opens over the current screen from any **Send reminder**. Language switch (Hinglish ·
  हिंदी · ਪੰਜਾਬੀ · English), editable message (use `offline.py` template text), **Send on WhatsApp**. After
  tapping it, show the toast "Reminder sent to Sharma Knit Processors · Undo".
- Bottom bar: **Today · Customers · Ask** and a **+ Add sale** button. Customers and Ask can be empty placeholders.
- Desktop (≥ 768px): slim top bar instead of the bottom bar, content in one column at most ~680px wide.
- Look (PLAN.md §Look): warm off-white paper, near-black ink, ruled hairlines, no card shadows, no badges, no
  emojis, no gradients. Deep red only for late money. Large rupee amounts in lakh format. Noto Sans with
  Devanagari and Gurmukhi from Google Fonts. Tap targets at least 44px.
- Words: use the PLAN.md §Words column "New" everywhere.

## Tests

manual: see Check

## Check

Open `mockup/index.html` in a browser at 390px wide and at desktop width, in light and dark mode. Tap Today →
a row → the customer page → Send reminder → switch language → Send on WhatsApp → the toast appears.

## Done when

- [ ] `mockup/index.html` and `mockup/style.css` exist and show the three screens with the demo data
- [ ] It works at 390px and desktop width, in light and dark mode, with no horizontal scroll
- [ ] Published as a private artifact; the link is given to Ankur
- [ ] Ankur has approved the look and layout in chat. Until then, set `**Status:** BLOCKED (needs human: mockup
      approval)`. Changes he asks for are made here, and any that change a decision are written into PLAN.md
- [ ] Committed: `T01: mockup of the new design`
