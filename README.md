# Bakaya (बकाया): credit tracker for machinery makers

A prototype built for the **Parvaaz AI Entrepreneurship Programme**.

Bakaya helps the owner of a machinery-manufacturing business keep track of money customers owe them,
see what's overdue at a glance, and send polite payment reminders on WhatsApp. AI features help write those
reminders, answer questions about the credit book, and read bills from a photo.

**Project docs:** [the idea](docs/idea.md) · [feedback log](docs/feedback-log.md)

## The problem

We interviewed the owner of a textile-machinery manufacturer (about 15–20 workers) that builds large,
made-to-order machines costing ₹5–25 lakh each. Asked what the biggest problem is for them as the owner,
they said **credit**: collecting payments that customers owe.

Machines are sold on instalments (typically an advance, a payment before dispatch, and a final payment after
installation), and customers often pay late. Keeping track of who owes what, and following up without damaging
long-term relationships, takes time and is easy to let slip.

## What the prototype does

| Feature | What it shows |
| --- | --- |
| **Dashboard** | Total outstanding, overdue amount, what's due in the next 7 days, overdue money grouped by how late it is, and a "Who owes you" list sorted by overdue amount |
| **Payment habits** | Each customer is labelled *Pays on time*, *Sometimes late* or *Often late*, based on how late their past instalments were |
| **Orders and payment plans** | Each machine order has its instalments (e.g. 30% advance, 60% before dispatch, 10% after installation). Recording a payment updates everything automatically |
| ✨ **AI payment reminders** | Writes a WhatsApp reminder in **Hinglish, Hindi, Punjabi or English**. The tone gets firmer the later the payment is, but always stays respectful. One tap opens it in WhatsApp |
| ✨ **Ask AI** | Ask questions in plain language, e.g. *"Sabse zyada paisa kiska baaki hai?"* or *"What's due this week?"* |
| ✨ **Scan a bill** | Take a photo of an invoice and the AI fills in a new order (customer, machine, amount, date) for you to check |

**Offline demo mode:** without an API key, the app still works. Reminders come from built-in templates in all four
languages, and Ask AI answers common questions with simple rules. Only bill scanning needs the AI.

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
3. Restart the app. The badge in the top-right changes to **AI: on**.

`.env` is listed in `.gitignore`, so your key never gets committed. Never paste the key into code or share it.

You can also set `BUSINESS_NAME` in `.env`. It's used to sign the reminders.

### Reset the demo data

```bash
.venv/bin/python seed.py
```

All demo customers, phone numbers and amounts are made up. Dates are relative to today, so the demo always shows
a realistic mix of overdue, due-soon and paid orders.

## Demo script (about 3 minutes)

1. **Dashboard.** "₹24 lakh of ₹56 lakh is overdue, and ₹2.5 lakh has been late for over 60 days. The owner sees this in one glance instead of going through ledgers."
2. **Who owes you.** Point out the *Often late* label on Sharma Knit Processors: it's based on their payment history.
3. **Remind.** Click *Remind* on Sharma. Show the Hinglish message, switch to Punjabi, then click *Open in WhatsApp*.
4. **Record a payment.** Click Sharma's row, record ₹5,10,000, and show the overdue total drop on the dashboard.
5. **Ask AI.** Ask *"Is hafte kitna paisa aana hai?"*
6. **Scan bill** (needs an API key). Upload a photo of any invoice and create an order from it.
7. **Next steps.** Factory visit to check how they track credit today (Tally? a notebook?) and test this with the owner.

## How it's built

- `app.py`: Flask web server and API routes
- `ledger.py`: works out balances, overdue amounts, ageing and payment habits. Payments are applied to instalments in due-date order
- `ai.py`: AI features using the Claude API (`claude-opus-5-5`). Bill reading uses structured outputs, so the result is always valid JSON
- `offline.py`: template reminders and rule-based answers for offline mode
- `db.py`: SQLite storage (`bakaya.db`, created on first run)
- `seed.py`: fictional demo data
- `static/`: the web page (plain HTML, CSS and JavaScript, with no build step)

## Ideas for later

- Import existing data from Tally or Excel
- Automatic reminder schedule (e.g. 3 days before the due date, then weekly)
- Login for the owner and the accountant
- Track spare-parts sales and service visits for each machine sold
