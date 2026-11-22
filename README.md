# Bakaya (बकाया): credit tracker for machinery makers

A prototype built for the **Parvaaz AI Entrepreneurship Programme**.

Bakaya is a **follow-up assistant** for the owner of a machinery-manufacturing business. The owner opens it on
their phone, sees who to contact today and why, and sends a polite payment reminder on WhatsApp in one tap.
AI helps write those reminders, answer questions about who owes what, and read bills from a photo.

**Project docs:** [the idea](docs/idea.md) · [feedback log](docs/feedback-log.md)

## The problem

We interviewed the owner of a textile-machinery manufacturer (about 15–20 workers) that builds large,
made-to-order machines costing ₹5–25 lakh each. Asked what the biggest problem is for them as the owner,
they said **credit**: collecting payments that customers owe.

Machines are sold on instalments (typically an advance, a payment before dispatch, and a final payment after
installation), and customers often pay late. Keeping track of who owes what, and following up without damaging
long-term relationships, takes time and is easy to let slip.

## What the prototype does

| Screen | What it shows |
| --- | --- |
| **Today** (home) | One line of totals (*₹55.7 lakh owed to you · ₹24.2 lakh late*), then the customers to contact today, each with a reason: *"Promised ₹5 lakh by 19 Nov. Not received."* or *"60 days late. Usually pays about 31 days late. Reminded 9 days ago, no payment yet."* Broken promises come first. Anyone reminded in the last 5 days, or with a promise that hasn't fallen due, is left off until it's time to follow up again |
| **Customers** | Everyone A to Z, with a search by name or city and what each one owes |
| **Customer page** | Call and WhatsApp buttons; what they owe and how late; their payment habit (*Usually pays about 31 days late*); each machine sold with its instalments (paid ✓, late in red, coming up in grey); and one history of payments, reminders and promises |
| ✨ **Send reminder** | Writes a WhatsApp reminder in **Hinglish, हिंदी, ਪੰਜਾਬੀ or English**. The tone gets firmer the later the payment is, and one step firmer for each reminder already sent since the customer last paid, but always stays respectful. The owner checks the message, then sends it on WhatsApp. The reminder is saved in the history, with Undo |
| **Record payment** | Money received: amount, date, mode (NEFT, RTGS, UPI, Cheque, Cash) and a note. If several sales are unpaid, it asks which one |
| **Note a promise** | *"They said they'll pay ₹3 lakh by 29 Nov."* The customer leaves Today until that date, and comes back at the top if the money doesn't arrive |
| **+ Add sale** | Customer (or a new one), machine, price and dates, with the usual plan filled in: 30% advance, 60% before dispatch, 10% after installation. **Change plan** offers 50/50 or full payment on delivery. ✨ **Scan a bill** fills in the form from a photo of an invoice |
| ✨ **Ask** | Questions in plain words, in any of the four languages: *"Who promised to pay?"*, *"Is hafte kitna paisa aana hai?"*, *"Sharma ka kitna baaki hai?"* |

It works on a phone and on a computer, and dark mode follows the device's setting.

**Without an API key the app still works.** Reminders come from built-in templates in all four languages, and Ask
answers common questions with simple rules. Only bill scanning needs the AI. The "why" lines on Today never use
the AI: they come from fixed rules, so the numbers are always right.

## Run it

You need Python 3.10 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Then open http://localhost:5055. Demo data loads automatically the first time.

### Turn on the AI features

1. Get an API key from https://platform.claude.com.
2. Copy `.env.example` to `.env` and paste the key after `ANTHROPIC_API_KEY=`.
3. Restart the app. The Ask screen stops saying *"AI is off"*, reminders say *"Written by AI"*, and
   **Scan a bill** appears in Add sale.

`.env` is listed in `.gitignore`, so your key never gets committed. Never paste the key into code or share it.

You can also set `BUSINESS_NAME` in `.env`. It's used to sign the reminders.

### Reset the demo data

```bash
.venv/bin/python seed.py
```

All demo customers, phone numbers and amounts are made up. Dates are relative to today, so the demo always shows
a realistic mix of late, due-soon and paid sales, plus a few reminders and promises to pay.

### Run the tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Each test uses its own temporary database and never calls the Claude API.

## Demo script (about 3 minutes)

Reset the demo data first (`.venv/bin/python seed.py`) so the story below matches what's on screen.

1. **Today.** "The owner opens the app and sees who to call today, and why." Point at Shree Ganesh at the top:
   *"Promised ₹5 lakh by 19 Nov. Not received."*
2. **Send a reminder** to Sharma Knit Processors. Show the Hinglish message, switch to ਪੰਜਾਬੀ, then tap
   **Send on WhatsApp**. Back on Today, Sharma has gone: they were just reminded.
3. **Customer page** for Shree Ganesh: the machine, the late instalment in red, and the history with the broken
   promise.
4. **Record a payment** of ₹5,00,000 by cheque for Shree Ganesh. The late amount drops from ₹10.68 lakh to
   ₹5.68 lakh, and the promise now counts as kept.
5. **Note a promise** for Tirupur Knit Finishers (₹2.95 lakh, a week from today). They leave Today until then.
6. **+ Add sale:** Malhotra Textiles, "Stenter, 6 chamber", ₹18,00,000. Show the plan line, then **Change plan**
   to 50/50. Save, and the customer page opens with the new sale. With an API key, **Scan a bill** instead.
7. **Ask:** tap *"Who promised to pay?"*, then *"Is hafte kitna paisa aana hai?"*
8. **Next steps:** the factory visit to try this with the owner, then service reminders (stage 2): *"Kaur
   Hosiery's tumble dryer is due for servicing"* rows in the same Today list.

## How it's built

- `app.py`: Flask web server and API routes
- `ledger.py`: works out what each customer owes, what's late and their payment habit. Payments are applied to
  instalments in due-date order
- `contact_log.py`: reminders and promises to pay: how often a customer was reminded since they last paid, and
  whether their promise is open, kept or broken
- `today.py`: the Today list rules: who is late or coming up, who is hidden after a reminder or a promise, and the
  "why" line for each
- `ai.py`: AI features using the Claude API (`claude-opus-5-5`). Bill reading uses structured outputs, so the
  result is always valid JSON
- `offline.py`: template reminders and rule-based answers for when there's no API key
- `db.py`: SQLite storage (`bakaya.db`, created on first run), including the contact log
- `seed.py`: fictional demo data, dated from today
- `static/`: the web app: plain HTML, CSS and JavaScript ES modules with no build step. `static/js/` has one file
  per screen (`today.js`, `customers.js`, `customer.js`, `ask.js`) and per sheet (`reminder.js`, `record.js`,
  `add-sale.js`), plus `lib.js` for shared helpers and `app.js` for the router
- `tests/`: pytest tests for the money maths, the contact log, the Today rules and the API
- `PLAN.md`: the plan and every shared decision; `tickets/`: the work, one ticket per piece
  (`python3 tickets/board.py` shows the board)

## Ideas for later

- **Stage 2, service reminders:** *"Kaur Hosiery's tumble dryer is due for servicing"* rows in Today
- **Stage 3, upsell and enquiries:** suggest a newer machine to past buyers, and follow up on enquiries
- Editing and deleting sales, payments and promises
- Import existing data from Tally or Excel
- Login for the owner and the accountant
