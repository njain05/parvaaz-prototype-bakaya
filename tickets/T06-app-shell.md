# T06 — App shell: new design, navigation, Customers list and Ask
**Status:** IN PROGRESS
**Prereqs:** T01 · **Branch:** t06-app-shell

## Goal

The real app gets the approved mockup's look and the new navigation. Today · Customers · Ask and **+ Add sale**
work on phone and desktop, the Customers list and Ask screens are done, and the old dashboard, Orders table, Scan
tab and ageing chart are gone. Every other screen has a stub file that its own ticket fills in, so T07–T11 can run
in parallel without touching the same lines.

Prefactoring ticket for the interface track: T06 → T07 / T11 → T08 / T09 → T10. PLAN.md §Front-end structure,
§Screens, §Assumed 6, 7, 9.

## Scope / files

- `static/index.html`: rewrite as the shell in PLAN.md §Front-end structure. Load `/static/js/app.js` as
  `type="module"`. Google Fonts link for Noto Sans (+ Devanagari, Gurmukhi) as in the mockup.
- `static/style.css`: replace with `mockup/style.css`, adjusted as needed. Keep one marked section per screen
  (`/* ===== screen: today ===== */`, `customers`, `customer`, `reminder`, `add-sale`, `record`, `ask`), empty
  where the screen isn't built yet. Remove styles for things that no longer exist.
- `static/app.js`: delete. Its useful pieces move into the new modules.
- New `static/js/lib.js` with the functions in PLAN.md §Front-end structure. `whatsappUrl` is moved from the old
  `app.js` unchanged. `toast(text, {action})` shows an optional action link (used for **Undo**). `openSheet(html)`
  opens `<dialog id="sheet">` as a bottom sheet on phones and a centred panel on desktop; Escape and the backdrop
  close it. `getStatus()` fetches `/api/status` once and caches it.
- New `static/js/app.js`: hash router (`#/today` default, `#/customers`, `#/customers/<id>`, `#/ask`), marks the
  active nav item, scrolls to the top on change; the **+ Add sale** button calls `openAddSale()`.
- New `static/js/customers.js`: the Customers list from `GET /api/book` (Assumed 6): A–Z, a search box filtering
  by name or city, each row showing the name, city, and the amount owed (red "· {amount} late" when late). Tapping
  a row goes to `#/customers/<id>`.
- New `static/js/ask.js`: the Ask chat ported from the old `app.js` `setupAsk`/`ask`, with three suggested
  questions ("Who owes the most?", "Is hafte kitna paisa aana hai?", "Who promised to pay?") and, at the bottom,
  the line "AI is on" or "AI is off: answers use simple rules. Add an API key to turn it on." (Assumed 9).
- Stubs, each exporting the function named in PLAN.md and showing a short "Coming soon" note:
  `static/js/today.js`, `static/js/customer.js`, `static/js/reminder.js`, `static/js/add-sale.js`.

## Details

- No AI sparkle emojis, no badges. Plain words from PLAN.md §Words.
- Back button: the router listens to `hashchange`, so browser Back works between screens.
- Desktop (≥ 768px): top bar with the three items and **+ Add sale** on the right; content column ~680px.
- Between this ticket and T07–T11, reminders, payments and adding sales are missing from the UI on `main`. That's
  expected; T12 checks everything end to end.

## Tests

manual: see Check

## Check

`.venv/bin/python app.py`, open http://localhost:5055 at 390px wide and at desktop width:

- the look matches the mockup, in light and dark mode
- Today · Customers · Ask switch screens and the active item is marked; browser Back works
- Customers: search "ludh" leaves only the Ludhiana customers; tapping one goes to `#/customers/<id>`
- Ask: "Who owes the most?" gets an answer; the AI status line shows
- no console errors, and `static/app.js` no longer exists

## Done when

- [ ] Shell, router, `lib.js`, Customers list and Ask work as above
- [ ] Stub files exist for today, customer, reminder and add-sale, exporting the PLAN.md functions
- [ ] `static/style.css` has a marked section per screen
- [ ] The old dashboard, Orders table, Scan tab, ageing chart and header AI pill are gone
- [ ] Committed: `T06: app shell with new design, navigation, Customers and Ask`
