# T10 — Record a payment and note a promise
**Status:** TODO
**Prereqs:** T09 · **Branch:** t10-payment-and-promise

## Goal

From the customer page, the owner can record money received and note "they said they'll pay ₹X by date". The page
updates at once, and a promise takes the customer off Today until the promised date.

Interface track: T09 → T10 → T12. PLAN.md §Customer page, §Today rules 4–5.

## Scope / files

- New `static/js/record.js`: `openRecordPayment(customer, {onSaved})` and `openPromise(customer, {onSaved})`,
  where `customer` is the `/api/customers/<id>` response.
- `static/js/customer.js`: add **Record payment** and **Note a promise** to the actions row, after Send reminder.
  Record payment shows when `owed > 0.5`; Note a promise when `late > 0.5` or a payment is due in the next 7 days.
- `static/style.css`: only the `/* ===== screen: record ===== */` section.

## Details

- **Record payment** sheet:
  - Which sale: picked automatically when only one sale has a balance (shown as text, "For: Raising Machine,
    24 roller"); a choice of sales (machine + balance) when there are several.
  - Amount, pre-filled with that sale's late amount, else its next due amount, else its balance.
  - Date (today), mode (NEFT · RTGS · UPI · Cheque · Cash), note ("Cheque no., UTR…").
  - Save: `POST /api/orders/<order_id>/payments`; show any `error` in the sheet. On success close, `onSaved()`,
    toast "₹x received from {name}".
- **Note a promise** sheet: amount (pre-filled with `late`, else the amount due soon), "Pay by" date (default 7
  days from today), note. Save: `POST /api/customers/<id>/contacts {kind: "promise", promised_amount,
  promised_date, note}`. On success close, `onSaved()`, toast "Promise noted. {name} is off Today until {date}."

## Tests

manual: see Check (validation is tested in T04)

## Check

On `#/customers/1` (Sharma, one unpaid sale):

- Record payment: the sale is chosen for you; save ₹5,10,000 → Owes and late drop, History shows the payment
- On Bansal Dyeing House (two sales): Record payment asks which sale
- Note a promise of ₹1,00,000 by next week → the promise line appears; Today no longer lists Sharma
- A promise date in the past shows the server's error in the sheet

## Done when

- [ ] Record payment works with one or several unpaid sales
- [ ] Note a promise saves and hides the customer from Today
- [ ] Errors show inside the sheet
- [ ] Committed: `T10: record payment and note a promise`
