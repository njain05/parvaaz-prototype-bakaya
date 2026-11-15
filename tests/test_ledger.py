"""The money maths in ledger.py, on small hand-built data with a fixed today."""
from datetime import date

import ledger

TODAY = date(2026, 11, 15)


def make_data(milestones, payments):
    """One customer with one ₹1,00,000 order. milestones: (label, amount, due_date); payments: (date, amount)."""
    return {
        "customers": [{"id": 1, "name": "Test Mills", "contact_person": "", "phone": "", "city": "Ludhiana"}],
        "orders": [{"id": 1, "customer_id": 1, "machine": "Raising Machine", "order_date": "2026-10-01",
                    "total": 100000, "notes": ""}],
        "milestones": [{"id": i, "order_id": 1, "label": label, "amount": amount, "due_date": due}
                       for i, (label, amount, due) in enumerate(milestones, 1)],
        "payments": [{"id": i, "order_id": 1, "date": d, "amount": amount, "mode": "", "note": ""}
                     for i, (d, amount) in enumerate(payments, 1)],
        "contacts": [],
    }


# Listed out of due-date order on purpose: payments must still clear the earliest instalment first.
PLAN = [
    ("After installation", 10000, "2026-11-30"),
    ("Advance", 30000, "2026-10-01"),
    ("Before dispatch", 60000, "2026-10-31"),
]


def order_of(payments):
    return ledger.build(make_data(PLAN, payments), TODAY)["orders"][0]


def by_label(order):
    return {m["label"]: m for m in order["milestones"]}


def test_payment_clears_instalments_in_due_date_order():
    ms = by_label(order_of([("2026-10-01", 90000)]))
    assert ms["Advance"]["status"] == "paid"
    assert ms["Before dispatch"]["status"] == "paid"
    assert ms["After installation"]["status"] == "upcoming"
    assert ms["After installation"]["unpaid"] == 10000


def test_partial_payment_leaves_the_right_unpaid():
    order = order_of([("2026-10-01", 40000)])
    ms = by_label(order)
    assert ms["Advance"]["unpaid"] == 0
    assert ms["Before dispatch"]["unpaid"] == 50000
    assert ms["Before dispatch"]["partly_paid"]
    assert order["balance"] == 60000


def test_unpaid_instalment_past_due_is_late():
    order = order_of([("2026-10-01", 40000)])
    assert by_label(order)["Before dispatch"]["status"] == "overdue"
    assert order["status"] == "overdue"
    assert order["overdue"] == 50000
    assert order["days_overdue"] == 15  # due 31 Oct, today 15 Nov


def test_nothing_late_when_paid_up_to_date():
    order = order_of([("2026-10-01", 30000), ("2026-10-30", 60000)])
    assert order["overdue"] == 0
    assert order["days_overdue"] == 0


def test_habit_boundaries():
    assert ledger.habit([]) == "new"
    assert ledger.habit([7]) == "on_time"
    assert ledger.habit([8]) == "sometimes_late"
    assert ledger.habit([30]) == "sometimes_late"
    assert ledger.habit([31]) == "often_late"
    assert ledger.habit([0, 14]) == "on_time"  # the average, not the worst


def test_inr_uses_lakh_grouping():
    assert ledger.inr(1234567) == "₹12,34,567"
    assert ledger.inr(999) == "₹999"
    assert ledger.inr(100000) == "₹1,00,000"
    assert ledger.inr(-5000) == "-₹5,000"
