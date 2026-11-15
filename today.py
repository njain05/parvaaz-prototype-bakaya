"""Works out who the owner should contact today and why: a Late group and a Coming up group, one row per customer.

Plain functions over ledger.build() and db.load_all() data, like ledger.py. The rules are in PLAN.md §Today rules.
"""
from datetime import date, timedelta

import contact_log
from ledger import DUE_SOON_DAYS, EPS, inr

REMINDER_HIDE_DAYS = 5  # a customer reminded fewer than this many days ago leaves Today (Assumed 11)


def lakh(n):
    """Short rupee amount for why lines and totals: 510000 -> ₹5.1 lakh, 85000 -> ₹85,000."""
    if n < 100000:
        return inr(n)
    s = f"{n / 100000:.1f}".removesuffix(".0")
    return f"₹{s} lakh"


def _day(d):
    """20 Nov"""
    return d.strftime("%-d %b")


def _habit_sentence(c):
    if c["habit"] in ("often_late", "sometimes_late"):
        return f"Usually pays about {c['avg_days_late']} days late."
    if c["habit"] == "on_time":
        return "Usually pays on time."
    return ""


def _why(*sentences):
    return " ".join(s for s in sentences if s)


def _milestones(book, customer_id, status):
    return [m for o in book["orders"] if o["customer_id"] == customer_id
            for m in o["milestones"] if m["status"] == status]


def _row(c, amount, days_late, due_date, why, flag):
    return {
        "customer_id": c["id"],
        "name": c["name"],
        "city": c["city"],
        "amount": round(amount, 2),
        "days_late": days_late,
        "due_date": due_date,
        "why": why,
        "flag": flag,
        "remind_order_id": c["remind_order_id"],
    }


def _late_row(c, book, why, flag):
    late_due = [m["due_date"] for m in _milestones(book, c["id"], "overdue")]
    return _row(c, c["overdue"], c["days_overdue"], min(late_due, default=None), why, flag)


def build_today(book, data, today):
    """The GET /api/today answer: totals, the Late rows and the Coming up rows."""
    broken, late, coming = [], [], []
    week_end = today + timedelta(days=DUE_SOON_DAYS)

    for c in book["customers"]:
        if c["outstanding"] <= EPS:
            continue
        cid = c["id"]
        habit = _habit_sentence(c)

        promise = contact_log.promise_status(data, cid, today)
        if promise and promise["state"] == "broken":
            by = date.fromisoformat(promise["promised_date"])
            why = _why(f"Promised {lakh(promise['amount'])} by {_day(by)}. Not received.", habit)
            row = _late_row(c, book, why, "broken_promise")
            if c["overdue"] <= EPS:  # promised money that isn't late yet: chase what they still owe
                row["amount"] = c["outstanding"]
            broken.append((promise["amount"], row))
            continue
        if promise and promise["state"] == "open":
            continue

        last = contact_log.last_reminder(data, cid)
        if last and (today - date.fromisoformat(last["date"])).days < REMINDER_HIDE_DAYS:
            continue

        if c["overdue"] > EPS:
            flag = None
            if contact_log.reminder_count(data, cid) == 0:
                contact = "Not reminded yet."
            else:
                contact = f"Reminded {(today - date.fromisoformat(last['date'])).days} days ago, no payment yet."
                flag = "reminded"
            late.append(_late_row(c, book, _why(f"{c['days_overdue']} days late.", habit, contact), flag))
            continue

        due = [m for m in _milestones(book, cid, "upcoming")
               if today <= date.fromisoformat(m["due_date"]) <= week_end]
        if due:
            first = min(date.fromisoformat(m["due_date"]) for m in due)
            n = (first - today).days
            when = ("Due today." if n == 0 else "Due tomorrow." if n == 1
                    else f"Due in {n} days ({_day(first)}).")
            amount = sum(m["unpaid"] for m in due)
            coming.append(_row(c, amount, 0, first.isoformat(), _why(when, habit), None))

    broken.sort(key=lambda pr: (-pr[0], -pr[1]["amount"]))
    late.sort(key=lambda r: -r["amount"])
    coming.sort(key=lambda r: (r["due_date"], -r["amount"]))

    return {
        "today": today.isoformat(),
        "totals": {"owed": book["totals"]["outstanding"], "late": book["totals"]["overdue"]},
        "late": [row for _, row in broken] + late,
        "coming_up": coming,
    }
