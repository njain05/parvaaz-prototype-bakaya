# Plan: Bakaya redesign

A living plan. Update it when a decision changes, and note the change in the [changelog](#changelog).

## Goal

Turn Bakaya from a cluttered credit dashboard into a clean **follow-up assistant**. The owner opens it on their
phone, sees who to contact today and why, and sends the message in one tap.

Credit comes first: it's the owner's biggest problem and most of the code exists. Service reminders, upsell
suggestions and enquiries come later and slot into the same Today list.

## Decisions

Settled in a grilling session on 15 Nov 2026.

### Product

| Decision | Why |
| --- | --- |
| The product is a follow-up assistant, built in stages: credit, then service, then upsell and enquiries | Matches the original discussion. Credit first because it's the owner's biggest pain |
| The main user is the owner, on a phone. Desktop is a wider version of the same layout | The owner is on the factory floor and already uses WhatsApp for reminders |
| First audience: the business owner at the factory visit, then the class demo. Aim for a working build in about a week | Owner feedback matters more than polish for the instructor |
| The interface is in plain English. The reminders stay in 4 languages | Plain words are easy to read. Add a Hindi/Hinglish toggle only if the owner struggles |

### Screens and navigation

| Decision | Why |
| --- | --- |
| The home screen is **Today**: one line of totals, then a list of who to contact and why | This is the "what to send, when and why" from the discussion. Later action types join the same list |
| The app is organised around **customers**, not orders. Sales are shown on the customer page | The owner thinks "Sharma ji owes me", not "order #3 has an overdue milestone" |
| Navigation: bottom bar with **Today · Customers · Ask**, plus a **+ Add sale** button. A slim top bar on desktop, with content in one readable column | Few places to go, and one obvious way to add data |
| Bill scanning is one way to add a sale, not its own tab | It's an input method, not a destination |
| Ask AI stays, but off the main screens | Strong demo moment, but not daily use |

### What's in the first release

- **In:** Today list, customer page, send reminder (AI + WhatsApp), record payment, note a promise to pay, contact
  history, add a sale (typed or scanned), Ask AI
- **Cut:** ageing chart, the 4 stat tiles (replaced by one line), the Orders table, the "AI: offline demo mode"
  pill in the header (moves to a quiet settings or about spot)
- **Later:** service reminders (stage 2), upsell and enquiries (stage 3), editing and deleting entries

### Look

| Decision | Why |
| --- | --- |
| **Bahi-khata / ledger style:** warm off-white paper, near-black ink, thin ruled lines instead of cards and shadows | Feels like the owner's own account book, not a generic SaaS dashboard |
| One deep red, used only for late money. No coloured badges, gradients or emojis | Colour means something when it's rare |
| Large, clear numbers in rupees with lakh formatting | Amounts are what the owner scans for |
| A font that covers Latin, Devanagari and Gurmukhi (Noto Sans family) | Hindi and Punjabi reminders must render well |
| Dark mode follows the phone setting | Free with CSS tokens |

### Words

| Old | New |
| --- | --- |
| Outstanding | Owed |
| Overdue | Late |
| Milestone | Instalment |
| Order | Sale |
| Ageing | (removed) |

### Engineering

| Decision | Why |
| --- | --- |
| Keep Flask + SQLite + plain HTML/CSS/JS, no build step | The problem is design, not tech. Easy to run on any laptop for a demo |
| "Why" lines come from fixed rules in code. The AI only drafts messages | Instant, always correct, works offline. Wrong numbers would destroy trust |
| pytest suite for the ledger maths and the Today rules only. No UI tests | A wrong amount on screen is the one bug we can't afford |
| Work is split into tickets in `tickets/`, one `tNN-…` branch per ticket, merged into `main`. No push unless asked | Tickets can run in parallel, and each is easy to review and roll back |
| Mockup first (`mockup/index.html`, also published as a private artifact for phone viewing), then the real app reuses its CSS | Catches layout disagreements before they're coded |

## Screens

### Today (home)

- One line: *"₹56 lakh owed to you · ₹24 lakh late"*
- **Late:** one row per customer with late instalments, biggest late amount first
- **Coming up:** customers with an instalment due in the next 7 days and nothing late, soonest first
- Each row: customer name, amount, one "why" line, a **Send reminder** button. Tapping the row opens the customer

Example row:

> **Sharma Knit Processors** · ₹5.1 lakh late
> 58 days late. Usually pays about 40 days late. Not reminded yet.  **[Send reminder]**

### Customer page

1. Name, contact person, city, with **Call** and **WhatsApp** buttons
2. One line: *"Owes ₹12.3 lakh · ₹5.1 lakh late (58 days)"*, and the payment habit in words
3. Actions: **Send reminder · Record payment · Note a promise**
4. **Machines:** one block per sale with its instalments (paid ✓, late in red, upcoming in grey)
5. **History:** payments, reminders and promises in one timeline, newest first

Record payment picks the sale automatically when only one is unpaid, and asks which one only when there are several.

### Send reminder (sheet over the current screen)

- Language switch: Hinglish · हिंदी · ਪੰਜਾਬੀ · English
- The drafted message, editable
- **Send on WhatsApp** opens WhatsApp with the text and records the reminder in the contact log

### Add sale

- Customer (pick or add new), machine, price, order date, expected dispatch date
- Payment plan filled in as 30% advance / 60% before dispatch / 10% after installation, shown as one line with a
  **Change plan** link
- Optional: advance received
- **Scan a bill** fills in the same form

### Ask

- Chat box with 3 suggested questions. Answers use the contact log and promises too.

## Today rules

These go in a new `today.py`, as plain functions over the loaded data, like `ledger.py`.

1. **Late:** the customer has at least one instalment past its due date with more than ₹0.50 unpaid.
2. **Coming up:** nothing late, and the next unpaid instalment is due within 7 days.
3. **Hidden after a reminder:** if the customer was reminded in the last 5 days, they leave Today. They come back
   with *"Reminded 5 days ago, no payment yet."*
4. **Hidden by a promise:** if the customer promised to pay by a date that hasn't passed, they leave Today.
5. **Broken promise:** if the promised date has passed and the payments since the promise add up to less than the
   promised amount, the row shows *"Promised ₹5 lakh by 20 Nov. Not received."* These rows go to the top of Late.
6. **Why line:** built from days late, payment habit (average days late), and the last contact.
7. **Firmness:** the reminder tone starts from days late (gentle under 15, firm 15–45, serious over 45). Each
   earlier reminder for the same late amount raises it one step, up to serious. It always stays respectful.

## Assumed (approved 2026-11-15)

1. **Partial promises:** a promise is kept only when the customer's payments dated after the promise add up to the
   promised amount.
2. **Undo:** the toast after "Send on WhatsApp" has an **Undo** link that deletes that log entry.
3. **Which sale a reminder is about:** the customer's worst sale (most late, then biggest balance), as
   `remind_order_id` in `ledger.build()` already picks.
4. **Firmness:** one step firmer for each reminder dated after the customer's last payment.
5. **Hiding by a promise:** an unkept promise hides the customer up to and including the promised date. From the
   next day it is broken.
6. **Customers list:** A–Z, with a search box and the amount each customer owes.
7. **Front end:** hash routes and plain ES modules, one file per screen, no build step (see
   [Front-end structure](#front-end-structure)).
8. **Mockup:** uses a fixed copy of the demo data, not the live API.
9. **AI status:** a small "AI on / off" line at the bottom of the Ask screen replaces the header pill.
10. **Tests:** in `tests/`, each using a temporary database. pytest is in `requirements-dev.txt`.
11. **Reminder hiding window:** a customer reminded fewer than 5 days ago is hidden from Today.

## Shared contracts

The tickets build against these. Change them only in a ticket whose Scope says so.

### `contacts` table

```sql
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    date TEXT NOT NULL,                 -- YYYY-MM-DD, the day of the contact
    kind TEXT NOT NULL CHECK (kind IN ('reminder', 'promise')),
    language TEXT DEFAULT '',           -- reminders: english | hinglish | hindi | punjabi
    promised_amount REAL,               -- promises only
    promised_date TEXT,                 -- promises only, YYYY-MM-DD
    note TEXT DEFAULT ''
);
```

`db.load_all()` returns it as `data["contacts"]`, ordered by date, then id.

### `contact_log.py` (pure functions over `db.load_all()` data)

```python
def customer_payments(data, customer_id) -> list[dict]          # payments on any of the customer's orders, by date
def reminder_count(data, customer_id) -> int                    # reminders dated after the customer's last payment
def last_reminder(data, customer_id) -> dict | None             # newest reminder row
def promise_status(data, customer_id, today) -> dict | None
    # newest promise, or None if there is none:
    # {"contact_id", "date", "amount", "promised_date", "paid_since", "state": "open" | "kept" | "broken"}
```

### API

`GET /api/today`

```json
{
  "today": "2026-11-15",
  "totals": {"owed": 5600000, "late": 2400000},
  "late": [Row],
  "coming_up": [Row]
}
```

`Row`: `{"customer_id", "name", "city", "amount", "days_late", "due_date", "why", "flag", "remind_order_id"}`.
`amount` is the late amount (Late) or the amount due in the window (Coming up). `due_date` is the oldest late due
date (Late) or the next due date (Coming up). `flag` is `"broken_promise"`, `"reminded"` or `null`.

`GET /api/customers/<id>`: the customer row plus `owed`, `late`, `days_late`, `habit`, `avg_days_late`,
`remind_order_id`, `promise` (from `promise_status`, or null), `sales` (the customer's orders as `ledger.build()`
returns them, newest first) and `history`, newest first:

```json
{"date", "kind": "payment" | "reminder" | "promise", "amount", "order_id", "machine",
 "mode", "note", "language", "promised_date", "contact_id"}
```

`POST /api/customers/<id>/contacts`: body `{"kind", "order_id"?, "language"?, "promised_amount"?,
"promised_date"?, "note"?}`, dated today. Returns `{"id"}`.

`DELETE /api/contacts/<id>`: returns `{"ok": true}`, or 404.

Errors from every route: `{"error": "<plain sentence for the owner>"}` with status 400 or 404.

### Front-end structure

```
static/index.html        shell: top bar (desktop) / bottom bar (phone), <main id="view">, <dialog id="sheet">, toast
static/style.css         tokens and shared components, then one marked section per screen:
                         /* ===== screen: today ===== */ and so on; a ticket edits only its own section
static/js/app.js         router: #/today (default), #/customers, #/customers/<id>, #/ask
static/js/lib.js         api, postJSON, del, esc, inr, lakh, fmtDate, addDays, store, whatsappUrl,
                         toast(text, {action: {label, onClick}}), openSheet(html), closeSheet(), getStatus()
static/js/today.js       export function render(el)
static/js/customers.js   export function render(el)
static/js/customer.js    export function render(el, id)
static/js/reminder.js    export function openReminder(customerId, orderId, {onSent})
static/js/add-sale.js    export function openAddSale(prefill = {})
static/js/ask.js         export function render(el)
```

## Build steps (first release)

The work is in tickets: run `python3 tickets/board.py` for the state, `--graph` for the order.

| Step | Tickets |
| --- | --- |
| 1. Mockup | T01 |
| 2. Data and rules | T02, T03, T04, T05 |
| 3. New interface | T06, T07, T08, T09, T10, T11 |
| 4. End-to-end check and docs | T12 |
| 5. Try it with the owner | Not a ticket: factory visit, feedback in `docs/feedback-log.md`, then revise this plan |

## Later stages

### Stage 2: Service reminders

Today gets *"Kaur Hosiery's tumble dryer is due for servicing"* rows. Needs an installation date per sale and a
service interval per machine type.

### Stage 3: Upsell and enquiries

- A product list with "related to" and "newer version of" links, so a new machine can be suggested to past buyers
- An enquiries list (name, phone, interested in, source, status, next follow-up date) with follow-up rows in Today

## Open questions

- Dates of the factory visit and the class demo.
- Stage 2: where are installation dates and service intervals entered, and what intervals do these machines need?
  Ask the owner on the factory visit.
- When to add editing and deleting entries. Probably before the owner uses it with real data.

## Changelog

- **15 Nov 2026:** work split into tickets T01–T12. Added the approved assumptions and shared contracts. Per-ticket
  branches replace the single `redesign` branch. Partial promises and undo moved from open questions to Assumed.
- **15 Nov 2026:** first version, from the grilling session.
