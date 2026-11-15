# T11 — Add a sale, typed in or scanned from a bill
**Status:** TODO
**Prereqs:** T06 · **Branch:** t11-add-sale

## Goal

**+ Add sale** opens a short form: customer, machine, price, dates. The standard 30/60/10 payment plan is filled
in for you. Scanning a bill fills in the same form. Saving takes you to that customer's page.

Interface track: T06 → T11 → T12. PLAN.md §Add sale.

## Scope / files

- `static/js/add-sale.js`: replace the stub with `openAddSale(prefill = {})`. Port `planMilestones` and the form
  logic from the old `static/app.js` (`openNewOrder`, `setupScan`). T06 deletes that file; read it with
  `git show 72c38f7:static/app.js`.
- `static/style.css`: only the `/* ===== screen: add-sale ===== */` section.
- `app.py` `create_order`: return `{"id": oid, "customer_id": cid}`. Change only the final `return` line: T04 edits
  the parsing lines at the top of the same function, so the merge stays clean.

## Details

- Form fields, in order: **Scan a bill** button; customer (search/select existing, or "+ New customer" which
  shows firm name, contact person, phone, city); machine; price (₹); order date (today); expected dispatch date
  (order date + 45 days).
- Plan line under the price: "30% advance · 60% before dispatch · 10% after installation" with a **Change plan**
  link. Change plan reveals the plan choice (30/60/10 · 50/50 · full payment on delivery) and the instalment
  preview table.
- Optional "Advance received now (₹)", default 0.
- **Scan a bill:** a file input with `capture="environment"`; uploads to `POST /api/ai/scan` and fills the fields
  from the response (match an existing customer by name, else fill the new-customer fields), then shows "Filled in
  from the bill. Check every field before saving." When `getStatus().ai_enabled` is false, the button is replaced
  by "Scanning bills needs the AI (add an API key)."
- Save: `POST /api/orders`; errors show in the sheet. On success close the sheet, go to
  `#/customers/<customer_id>`, toast "Sale saved".

## Tests

- `tests/test_customer_api.py` or a new `tests/test_orders.py`: `POST /api/orders` returns `customer_id`, for an
  existing and for a new customer.

## Check

At 390px: + Add sale → choose Kaur Hosiery Works, "Tumble Dryer", 7,20,000 → the plan line shows → Save → the
Kaur page opens with the new sale and three instalments. Change plan → 50/50 → preview shows two instalments.
With an API key: Scan a bill with a photo of an invoice → fields fill in.

## Done when

- [ ] Add sale saves with the default plan and with a changed plan
- [ ] New customers can be added from the form
- [ ] Scanning fills the form (or explains it needs the AI)
- [ ] `create_order` returns `customer_id`, with a test
- [ ] Committed: `T11: add sale form with plan line and bill scanning`
