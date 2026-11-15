# T03 — Today rules and `GET /api/today`
**Status:** DONE
**Prereqs:** T02 · **Branch:** t03-today-rules

## Goal

The server can say who the owner should contact today and why: a Late group and a Coming up group, one row per
customer, with a plain-words reason, hiding customers who were just reminded or who promised to pay.

Data track: T02 → T03 → T08 (Today screen). PLAN.md §Today rules, §API, §Assumed 3, 5, 11.

## Scope / files

- New `today.py`: `build_today(book, data, today) -> dict`, where `book` is `ledger.build(data, today)` and
  `data` is `db.load_all()`. Returns the `GET /api/today` shape from PLAN.md §API. Also `lakh(n) -> str`
  (`510000 → "₹5.1 lakh"`, `85000 → "₹85,000"`, using `ledger.inr` below one lakh).
- `app.py`: add `GET /api/today` **directly after `get_book`** (T04 adds its routes after `record_payment`; keep
  them apart).
- New `tests/test_today.py`.

## Details

For each customer in `book["customers"]` with `outstanding > 0.5`, or with a broken promise:

1. `promise = contact_log.promise_status(data, id, today)`.
2. **Broken promise:** row in Late, `flag: "broken_promise"`, why = `"Promised {lakh(amount)} by {d MMM}. Not
   received."` plus the habit sentence.
3. **Open promise:** skip (hidden).
4. **Reminded fewer than 5 days ago** (`contact_log.last_reminder`, `(today - date).days < 5`): skip.
5. **Late** (`overdue > 0.5`): row in Late, `amount = overdue`, `days_late = days_overdue`, `due_date` = oldest late
   due date. Why = `"{days} days late."` + habit sentence + contact sentence.
6. **Coming up:** nothing late and at least one unpaid instalment due between today and today + 7 days.
   `amount` = sum of those instalments' `unpaid`, `due_date` = the earliest. Why = `"Due today."` or
   `"Due in {n} days ({d MMM})."` / `"Due tomorrow."` + habit sentence.
7. Otherwise skip.

Sentences:

- Habit: `often_late` / `sometimes_late` → `"Usually pays about {avg_days_late} days late."`; `on_time` →
  `"Usually pays on time."`; `new` → nothing.
- Contact (Late rows that aren't broken promises): `contact_log.reminder_count(...) == 0` → `"Not reminded
  yet."` (a reminder before the last payment doesn't count, Assumed 4); otherwise `"Reminded {n} days ago, no
  payment yet."` from `last_reminder`, and `flag: "reminded"`.

Order: Late = broken promises first (biggest promised amount first), then by `amount` descending. Coming up =
by `due_date`, then `amount` descending. `remind_order_id` comes from the ledger customer row (Assumed 3).
`totals` = `{"owed": book totals outstanding, "late": book totals overdue}`. Dates in why lines like `20 Nov`.

- Done as built: customers who owe nothing are skipped even if their newest promise is broken (they paid
  everything they owed, just less than they promised).
- Done as built: a broken-promise row for a customer with nothing late yet uses `amount` = what they owe,
  `days_late: 0`, `due_date: null`.
- Done as built: rules run in the order above, so a broken promise shows even if the customer was reminded in
  the last 5 days.
- Done as built: `ledger.habit()` counts unpaid late instalments too, so a customer with only one late instalment
  gets "Usually pays on time." (under 8 days) or "about N days late". The `new` habit (no sentence) only shows on
  Coming up rows.

## Tests

`tests/test_today.py`, using the `seeded` fixture and `today=date.today()` (the seed is relative to today), plus
small hand-built cases where a fixed date is clearer:

- Shree Ganesh's broken promise is the first Late row, with the "Not received" why line
- Gupta (reminded 2 days ago) and Arora (open promise) are in neither list
- Sharma's why line contains "Reminded 9 days ago"; Kaur's says "Not reminded yet." (their reminder predates
  their last payment)
- a customer late on two sales appears once, with the summed late amount
- Coming up only includes instalments due within 7 days, and never a customer who is also late
- `lakh(510000) == "₹5.1 lakh"`, `lakh(85000) == "₹85,000"`
- `GET /api/today` via `app.app.test_client()` returns 200 and the PLAN.md keys

## Check

```bash
.venv/bin/python -m pytest -q tests/test_today.py
.venv/bin/python seed.py && .venv/bin/python app.py &
curl -s localhost:5055/api/today | python3 -m json.tool | head -40
```

Shree Ganesh first with "Not received", Sharma with "Reminded 9 days ago", no Gupta or Arora.

## Done when

- [x] `today.py` with `build_today` and `lakh`
- [x] `GET /api/today` returns the PLAN.md shape
- [x] `tests/test_today.py` passes, and so does the whole suite
- [x] Committed: `T03: Today rules and /api/today`
