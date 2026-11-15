# T04 — Customer API: details, history, contacts, and input validation
**Status:** DONE
**Prereqs:** T02 · **Branch:** t04-customer-api

## Goal

The server can return everything about one customer (their sales, instalments and a merged history of payments,
reminders and promises), record a reminder or a promise, undo one, and answer bad input with a plain error
instead of a crash.

Data track: T02 → T04 → T07 (reminder sheet) → T09 / T10. PLAN.md §API, §Customer page, §Assumed 2.

## Scope / files

- `app.py`:
  - a helper `number(value) -> float | None` (None for missing, non-numeric, NaN or infinite values);
  - use it in `create_order` (`total`, `advance_received`, each milestone `amount`) and `record_payment`
    (`amount`), so bad numbers give the existing friendly 400 messages instead of a 500;
  - add, **directly after `record_payment`** (T03 adds its route after `get_book`):
    - `GET /api/customers/<int:customer_id>`
    - `POST /api/customers/<int:customer_id>/contacts`
    - `DELETE /api/contacts/<int:contact_id>`
- New `tests/test_customer_api.py`.

## Details

- `GET /api/customers/<id>`: shape in PLAN.md §API. Take the customer row from `ledger.build()` (`outstanding` →
  `owed`, `overdue` → `late`, `days_overdue` → `days_late`) and the customer's orders from `book["orders"]`.
  `history` merges the customer's payments (kind `payment`, with the order's `machine`) and contacts, newest
  first (date desc, then payments before contacts on the same day). `promise` is
  `contact_log.promise_status(...)`. 404 `"Customer not found."`.
- `POST …/contacts`, dated today:
  - `kind` must be `reminder` or `promise` → else 400 `"Unknown contact type."`
  - `order_id`, if given, must belong to this customer → else 400 `"That sale isn't this customer's."`
  - promise: `promised_amount` > 0 (`"Enter the amount they promised."`) and `promised_date` a valid date not
    before today (`"Enter the date they promised to pay by."`).
  - Returns `{"id": new_id}`.
- `DELETE /api/contacts/<id>`: `db.delete_contact`; 404 `"Already removed."` when nothing was deleted.
- `/api/book` stays as it is: T06 still uses it for the Customers list.

Done as built:
- The customer row is `id, name, contact_person, phone, city` plus the PLAN.md fields; the ledger's `orders` count
  is left out because `sales` carries the orders.
- `POST …/contacts` for an unknown customer returns 404 `"Customer not found."`. `language` is stored for
  reminders only, and `note` is trimmed.
- `number()` also rejects `true`/`false`. A bad `advance_received` gets the existing advance message
  (`"Advance received can't be more than the total."`), since `create_order` has no separate one.

## Tests

`tests/test_customer_api.py` with `app.app.test_client()` and the `seeded` fixture:

- customer details have `sales`, `history` newest first, and Sharma's seeded reminder in `history`
- unknown customer → 404
- posting a reminder adds it to `history`; deleting it removes it; deleting again → 404
- promise without an amount, or with a past date → 400 with the messages above
- `order_id` of another customer → 400
- `record_payment` with `amount: "abc"` → 400 (not 500); `create_order` with `total: "abc"` → 400

## Check

```bash
.venv/bin/python -m pytest -q tests/test_customer_api.py
curl -s localhost:5055/api/customers/1 | python3 -m json.tool | head -30
curl -s -X POST localhost:5055/api/orders/1/payments -H 'Content-Type: application/json' -d '{"amount":"abc","date":"2026-11-15"}'
# {"error": "Enter the amount received."}
```

## Done when

- [x] The three routes exist with the PLAN.md shapes and the error messages above
- [x] Bad numbers in `create_order` and `record_payment` return 400, not 500
- [x] `tests/test_customer_api.py` passes, and so does the whole suite
- [x] Committed: `T04: customer API, contact log routes, input validation`
