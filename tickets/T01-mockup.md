# T01 — Clickable mockup of Today, customer page and reminder sheet
**Status:** DONE
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

- Done as built: the artifact copy is made by `python3 mockup/build_artifact.py mockup/index.html mockup/style.css
  <out.html>` (inlines the CSS, drops the document skeleton). Published at
  https://claude.ai/artifact/Nbz3hV2yqHfYqBacwkEfRe (private).
- Done as built: routes are `#today`, `#customers`, `#ask`, `#customer-<id>` (artifact links only pass a plain
  `#name`, so not the `#/customers/<id>` form PLAN.md uses for the real app). Every customer has a page, built from
  the inlined data, and Customers is a simple A–Z list with search rather than an empty placeholder.
- Done as built: the mockup's contact log is made up (Shree Ganesh broke a ₹5 lakh promise due 12 Nov, Tirupur was
  reminded 9 Nov, Kaur was reminded 20 Oct). Sending a reminder hides that customer from Today (rule 3) and adds it
  to their History; Undo puts both back. Call, WhatsApp, Record payment, Note a promise, Add sale and Ask answers
  show a "not in this mockup yet" toast.
- Done as built: Ankur approved it on 15 Nov 2026 after checking it in dark mode only; light mode was not looked at
  by a human. T06 should check light mode when it copies the stylesheet.

## Tests

manual: see Check

## Check

Open `mockup/index.html` in a browser at 390px wide and at desktop width, in light and dark mode. Tap Today →
a row → the customer page → Send reminder → switch language → Send on WhatsApp → the toast appears.

## Done when

- [x] `mockup/index.html` and `mockup/style.css` exist and show the three screens with the demo data
- [x] It works at 390px and desktop width, in light and dark mode, with no horizontal scroll
- [x] Published as a private artifact; the link is given to Ankur
- [x] Ankur has approved the look and layout in chat. Until then, set `**Status:** BLOCKED (needs human: mockup
      approval)`. Changes he asks for are made here, and any that change a decision are written into PLAN.md
- [x] Committed: `T01: mockup of the new design`
