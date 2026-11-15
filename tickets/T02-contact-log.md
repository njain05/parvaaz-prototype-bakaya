# T02 — Contact log table, helpers, seed data and test setup
**Status:** TODO
**Prereqs:** — · **Branch:** t02-contact-log

## Goal

The app can store reminders and promises to pay, and answer "how many times was this customer reminded since
they last paid?" and "is their promise open, kept or broken?". The demo data includes reminders and promises.
The repo gets a pytest setup with tests for the money maths.

Contract ticket for the data track: T02 → T03 / T04 / T05. PLAN.md §Shared contracts, §Assumed 1, 4, 5, 10.

## Scope / files

- `db.py`: add the `contacts` table exactly as in PLAN.md §`contacts` table to `SCHEMA`; `wipe()` deletes contacts
  first; `load_all()` adds `"contacts"`. New functions:
  - `add_contact(conn, customer_id, date, kind, order_id=None, language="", promised_amount=None, promised_date=None, note="") -> int`
  - `delete_contact(conn, contact_id) -> bool` (True if a row was deleted)
- New `contact_log.py` with the four functions in PLAN.md §`contact_log.py`.
- `seed.py`: add a `CONTACTS` list (day offsets like the rest of the file) and insert it in `seed()`.
- New `requirements-dev.txt`: `-r requirements.txt` and `pytest>=8`.
- New `tests/conftest.py`, `tests/test_ledger.py`, `tests/test_contact_log.py`.

## Details

- `customer_payments`: payments on any order whose `customer_id` matches, sorted by date then id.
- `reminder_count`: reminders for the customer with `date` strictly after the date of the customer's last payment
  (all reminders if they never paid). Assumed 4.
- `promise_status`: take the newest promise (by date, then id). `paid_since` = sum of the customer's payments with
  `date` strictly after the promise's `date`. State: `kept` if `paid_since >= amount - 0.5`; else `open` if
  `promised_date >= today`; else `broken`. Assumed 1 and 5.
- Seed contacts, so T03's Today has every case to show:
  - Sharma Knit Processors: a reminder 9 days ago (shows "Reminded 9 days ago, no payment yet").
  - Shree Ganesh Processors: a promise made 10 days ago of ₹5,00,000 by 3 days ago, unpaid → broken.
  - Gupta Woollen Mills: a reminder 2 days ago → hidden from Today.
  - Arora Fabrics: a promise made 4 days ago of ₹1,00,000 by 6 days from now → open, hidden.
  - Kaur Hosiery Works: a reminder 40 days ago, before their last payment 20 days ago → `reminder_count` is 0.
- `tests/conftest.py`: an autouse fixture that points `db.DB_PATH` at a file in `tmp_path` (monkeypatch), runs
  `db.init()`, and removes `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` from the environment so tests never call
  the API. A `seeded` fixture runs `seed.seed()` and returns `db.load_all()`.
- Ledger tests use small hand-built `data` dicts with a fixed `today`, not the seed.

## Tests

- `tests/test_ledger.py`: a payment clears instalments in due-date order; partial payment leaves the right
  `unpaid`; an unpaid instalment past its due date is late with the right `days_overdue`; `habit()` boundaries
  (7 → on_time, 8 → sometimes_late, 31 → often_late, none → new); `inr(1234567) == "₹12,34,567"`.
- `tests/test_contact_log.py`: `reminder_count` ignores reminders before the last payment; `promise_status` gives
  open, kept (full payment after the promise), still open after a partial payment, broken the day after the
  promised date, and None with no promise; `db.delete_contact` returns False for a missing id; the seed produces
  the five cases above.

## Check

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q          # all pass
.venv/bin/python seed.py && sqlite3 bakaya.db "select customer_id, kind, date from contacts"   # 5 rows
```

## Done when

- [ ] `contacts` table, `add_contact`, `delete_contact` and `load_all()["contacts"]` exist as in PLAN.md
- [ ] `contact_log.py` has the four functions with the PLAN.md signatures
- [ ] The seed has the five contact cases above
- [ ] `requirements-dev.txt` and `tests/` exist and `.venv/bin/python -m pytest -q` passes
- [ ] The app still starts and the old UI still works (`/api/book` unchanged)
- [ ] Committed: `T02: contact log table, helpers, seed and tests`
