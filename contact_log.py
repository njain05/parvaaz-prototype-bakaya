"""Answers questions about the contact log: how often a customer was reminded since they last paid, and whether
their promise to pay is open, kept or broken.

Plain functions over the data that db.load_all() returns. Dates are YYYY-MM-DD strings, which sort correctly as text.
"""
from ledger import EPS


def _iso(day):
    return day if isinstance(day, str) else day.isoformat()


def _contacts(data, customer_id, kind):
    rows = [c for c in data["contacts"] if c["customer_id"] == customer_id and c["kind"] == kind]
    return sorted(rows, key=lambda c: (c["date"], c["id"]))


def customer_payments(data, customer_id):
    """Payments on any of the customer's orders, oldest first."""
    order_ids = {o["id"] for o in data["orders"] if o["customer_id"] == customer_id}
    pays = [p for p in data["payments"] if p["order_id"] in order_ids]
    return sorted(pays, key=lambda p: (p["date"], p["id"]))


def reminder_count(data, customer_id):
    """Reminders dated after the customer's last payment (all of them if they never paid)."""
    pays = customer_payments(data, customer_id)
    since = pays[-1]["date"] if pays else ""
    return sum(1 for c in _contacts(data, customer_id, "reminder") if c["date"] > since)


def last_reminder(data, customer_id):
    """The newest reminder row, or None."""
    rows = _contacts(data, customer_id, "reminder")
    return rows[-1] if rows else None


def promise_status(data, customer_id, today):
    """The customer's newest promise and where it stands, or None if they never promised.

    Kept when the payments dated after the promise add up to the promised amount. Otherwise open up to and
    including the promised date, and broken from the next day.
    """
    rows = _contacts(data, customer_id, "promise")
    if not rows:
        return None
    p = rows[-1]
    amount = p["promised_amount"] or 0
    paid_since = sum(x["amount"] for x in customer_payments(data, customer_id) if x["date"] > p["date"])
    if paid_since >= amount - EPS:
        state = "kept"
    elif p["promised_date"] >= _iso(today):
        state = "open"
    else:
        state = "broken"
    return {
        "contact_id": p["id"],
        "date": p["date"],
        "amount": amount,
        "promised_date": p["promised_date"],
        "paid_since": round(paid_since, 2),
        "state": state,
    }
