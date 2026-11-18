# T08 — Today screen
**Status:** DONE
**Prereqs:** T03, T07 · **Branch:** t08-today-screen

## Goal

The app opens on Today: one line of totals, then who to contact and why, in a Late group and a Coming up group.
Sending a reminder from a row takes that customer off the list.

Interface track: T03 + T07 → T08 → T12. PLAN.md §Today, §Today rules.

## Scope / files

- `static/js/today.js`: replace the stub with `render(el)` built on `GET /api/today`.
- `static/style.css`: only the `/* ===== screen: today ===== */` section.

## Details

- Totals line: `"{lakh(owed)} owed to you · {lakh(late)} late"`, the late part in red. (`lakh` is in `lib.js`.)
- **Late** heading with a count, then one row per item; then **Coming up** the same way. Leave out a group with no
  rows.
- Row: name (bold) and amount on the first line (amount red in Late); the `why` text below; a **Send reminder**
  button. Tapping anywhere else on the row goes to `#/customers/<customer_id>`.
- Send reminder: `openReminder(row.customer_id, row.remind_order_id, {onSent: () => render(el)})`.
- Both groups empty: "Nobody to chase today. Everyone has paid, been reminded, or promised a date."
- The look follows the mockup's Today screen.

- Done as built: the page head also shows today's date above the title ("Wednesday, 18 November"), as in the
  mockup. A row without a `remind_order_id` has no Send reminder button. Rows can be opened with Enter or Space
  as well as a tap. After a reminder is sent or undone, only the totals and rows are redrawn, not the whole screen.
  On phones the Send reminder button is full width.

## Tests

manual: see Check (the rules themselves are tested in T03)

## Check

`.venv/bin/python seed.py && .venv/bin/python app.py`, open http://localhost:5055 at 390px:

- Shree Ganesh is first under Late with "Promised ₹5 lakh by … Not received."
- Sharma shows "Reminded 9 days ago, no payment yet."; Gupta and Arora are not listed
- Send reminder on Sharma → send → Sharma leaves the list; Undo → Sharma is back
- tapping a row opens that customer's page (a stub until T09)

## Done when

- [x] Today renders totals, Late and Coming up from `/api/today`
- [x] Send reminder removes the row, Undo restores it
- [x] Empty state shows when there's nothing to do
- [x] Committed: `T08: Today screen`
