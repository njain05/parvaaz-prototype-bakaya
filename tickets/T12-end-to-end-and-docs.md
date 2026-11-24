# T12 — End-to-end check and docs
**Status:** BLOCKED (needs human: run the demo once with an API key)
**Prereqs:** T05, T08, T10, T11 · **Branch:** t12-end-to-end-and-docs

## Goal

The whole first release works as one app on a phone and on desktop, and the README, idea doc and demo script
describe the follow-up assistant rather than the old dashboard. After this, the app is ready for the factory
visit.

Closes the first release. PLAN.md §Build steps.

## Scope / files

- `README.md`: rewrite "What the prototype does", "Demo script" and "How it's built" for the new app (Today,
  customer page, reminders with the contact log, promises, add sale with scanning, Ask). Add how to run the tests
  (`pip install -r requirements-dev.txt`, `python -m pytest`). Keep "Run it" and "Turn on the AI features".
- `docs/idea.md`: describe the follow-up assistant and the stages (credit now, service and upsell/enquiries
  later), keeping the interview facts.
- `PLAN.md`: changelog entry; move anything learned into Open questions.
- Small fixes found during the click-through, in any file. Anything bigger becomes a new ticket (ask Ankur).

## Details

New demo script (about 3 minutes), to write into the README and to run here:

1. **Today.** "The owner opens the app and sees who to call today, and why." Point at the broken promise at the
   top.
2. **Send a reminder** to Sharma in Hinglish, switch to Punjabi, send on WhatsApp. Sharma leaves Today.
3. **Customer page** for Shree Ganesh: machines, late instalment, history with the broken promise.
4. **Record a payment** for Shree Ganesh; the late amount drops.
5. **Note a promise** for another late customer; they leave Today.
6. **Add a sale** (or scan a bill with an API key).
7. **Ask:** "Who promised to pay?" and "Is hafte kitna paisa aana hai?"
8. **Next steps:** factory visit, then service reminders (stage 2).

Done as built:
- The demo script ran end to end without an API key at 390px (light) and 1280px (dark): 19 screens and sheets,
  no horizontal scroll, no old words, no console errors except deliberate 404 tests.
- Not done yet: the run **with** an API key (AI reminders, AI answers in Ask, Scan a bill). No key is set up.
  Once `.env` has a key, run steps 2, 6 and 7 again, then set this ticket to DONE.
- Old words fixed: "Order date" → "Sale date" in Add sale; "Order not found." → "Sale not found."; "This order is
  fully paid." → "This sale is fully paid."; "Enter a valid order date." → "Enter a valid sale date.";
  offline Ask answers now say owed/late instead of outstanding/overdue, and "1 customer is late" reads right;
  "Who owes the most?" no longer shows "(₹0 late)". The AI Ask prompt now asks for the same plain words.
- Reminder messages to customers still say "order #N" (and "overdue" in the English/Hinglish templates): those are
  messages to customers, not the app's interface. Added as an open question in PLAN.md.
- README: also fixed "Turn on the AI features", which described the removed "AI: on" badge.

## Tests

`.venv/bin/python -m pytest -q` passes. The click-through below is manual.

## Check

`.venv/bin/python seed.py && .venv/bin/python app.py`, then run the demo script at 390px and at desktop width,
in light and dark mode, with and without an API key. No console errors, no horizontal scroll, no leftover old
words (Outstanding, Overdue, Milestone, Order, Ageing) in the interface.

## Done when

- [ ] The demo script runs end to end at phone and desktop width, light and dark, with and without AI
- [x] `README.md` and `docs/idea.md` describe the new app; `PLAN.md` changelog updated
- [x] The full test suite passes
- [x] Committed: `T12: end-to-end check and docs for the first release`
