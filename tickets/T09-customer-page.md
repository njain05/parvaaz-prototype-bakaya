# T09 — Customer page
**Status:** DONE
**Prereqs:** T07 · **Branch:** t09-customer-page

## Goal

Tapping a customer anywhere opens one page with everything about them: how to reach them, what they owe, their
machines and instalments, and a history of payments, reminders and promises. The owner can send a reminder from
there.

Interface track: T07 → T09 → T10. PLAN.md §Customer page.

## Scope / files

- `static/js/customer.js`: replace the stub with `render(el, id)` built on `GET /api/customers/<id>`.
- `static/style.css`: only the `/* ===== screen: customer ===== */` section.

## Details

Sections, in this order:

1. Name (large), contact person and city. **Call** (`tel:` link) and **WhatsApp** (`whatsappUrl(phone, "")`)
   buttons. Hide them when there's no phone.
2. `"Owes {lakh(owed)} · {lakh(late)} late ({days_late} days)"` (late part red, left out when nothing is late),
   and the habit in words: "Usually pays on time" / "Usually pays about N days late" / "New customer". If
   `promise` is open or broken, a line: "Promised {amount} by {date}" (+ " · Not received" in red when broken).
3. Actions row with **Send reminder** (`openReminder(id, remind_order_id, {onSent: rerender})`), shown only when
   `remind_order_id` is set. Leave room in the row: T10 adds **Record payment** and **Note a promise** after it.
4. **Machines:** one block per sale: machine, order date, price, "Paid {x} of {total}". Instalments as rows:
   label, due date, amount, and state in words: "Paid 3 Oct ✓", "{n} days late" (red), "{x} left · {n} days
   late" (red, partly paid), "Due 20 Nov" (grey).
5. **History:** newest first. Payment: "Paid {inr(amount)} · {mode}" with the machine. Reminder: "Reminder sent
   ({language})". Promise: "Promised {inr(amount)} by {date}". Each with its date.

- Unknown id (404): "Customer not found." with a link back to Customers.
- A **‹ Back** link at the top goes to the previous screen (`history.back()`), or Customers if there is none.

Done as built:
- The contact line also shows the phone number, as in the mockup.
- Instalment rows keep the mockup's mark column (✓ paid, ! late, · coming up), so a paid row reads
  "✓ Advance … Due 21 Jul · Paid 23 Jul" instead of putting ✓ after the date.
- A broken promise in History also says "Not received", with the owner's note.
- Back uses `history.back()` only after a navigation inside the app; a page opened directly goes to Customers.
- Any load error (404 included) shows the server's message, e.g. "Customer not found.", and a link to Customers.
- The actions row (`#cust-actions`) is hidden when empty; T10 adds Record payment and Note a promise to it.

## Tests

manual: see Check

## Check

Open http://localhost:5055/#/customers/1 at 390px and at desktop width:

- the five sections in order, late instalments in red, paid ones with ✓
- Send reminder → send → a new "Reminder sent" line at the top of History
- `#/customers/999` shows "Customer not found."
- From Today (T08 merged) or Customers, tapping a customer opens this page; Back returns

## Done when

- [x] All five sections render from `/api/customers/<id>`
- [x] Send reminder works from the page and History updates
- [x] 404 and Back handled
- [x] Committed: `T09: customer page`
