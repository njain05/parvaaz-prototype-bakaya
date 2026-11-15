"""The contact log: reminder counts, promise states, deleting entries, and the seeded demo cases."""
from datetime import date, timedelta

import contact_log
import db

TODAY = date(2026, 11, 15)
CUSTOMER = 1


def make_data(payments=(), contacts=()):
    """One customer with two orders. payments: (order_id, date, amount); contacts: dicts with at least
    kind and date."""
    return {
        "customers": [{"id": CUSTOMER, "name": "Test Mills"}, {"id": 2, "name": "Other Mills"}],
        "orders": [{"id": 1, "customer_id": CUSTOMER}, {"id": 2, "customer_id": CUSTOMER},
                   {"id": 3, "customer_id": 2}],
        "milestones": [],
        "payments": [{"id": i, "order_id": oid, "date": d, "amount": amount}
                     for i, (oid, d, amount) in enumerate(payments, 1)],
        "contacts": [{"id": i, "customer_id": CUSTOMER, "order_id": None, "language": "", "promised_amount": None,
                      "promised_date": None, "note": "", **c}
                     for i, c in enumerate(contacts, 1)],
    }


def reminder(d):
    return {"kind": "reminder", "date": d}


def promise(d, amount, by):
    return {"kind": "promise", "date": d, "promised_amount": amount, "promised_date": by}


# customer_payments, reminder_count, last_reminder

def test_customer_payments_covers_all_their_orders_by_date():
    data = make_data(payments=[(2, "2026-11-01", 500), (1, "2026-10-01", 100), (3, "2026-09-01", 999)])
    assert [p["amount"] for p in contact_log.customer_payments(data, CUSTOMER)] == [100, 500]


def test_reminder_count_ignores_reminders_before_the_last_payment():
    data = make_data(
        payments=[(1, "2026-10-10", 1000)],
        contacts=[reminder("2026-10-01"), reminder("2026-10-10"), reminder("2026-10-20"), reminder("2026-11-01")],
    )
    assert contact_log.reminder_count(data, CUSTOMER) == 2


def test_reminder_count_counts_all_when_never_paid():
    data = make_data(contacts=[reminder("2026-10-01"), reminder("2026-11-01")])
    assert contact_log.reminder_count(data, CUSTOMER) == 2


def test_reminder_count_ignores_promises_and_other_customers():
    data = make_data(contacts=[promise("2026-11-01", 1000, "2026-11-20"),
                               {**reminder("2026-11-02"), "customer_id": 2}])
    assert contact_log.reminder_count(data, CUSTOMER) == 0


def test_last_reminder():
    assert contact_log.last_reminder(make_data(), CUSTOMER) is None
    data = make_data(contacts=[reminder("2026-11-01"), reminder("2026-10-01"), promise("2026-11-05", 1, "2026-11-09")])
    assert contact_log.last_reminder(data, CUSTOMER)["date"] == "2026-11-01"


# promise_status

def test_no_promise_gives_none():
    assert contact_log.promise_status(make_data(contacts=[reminder("2026-11-01")]), CUSTOMER, TODAY) is None


def test_unpaid_promise_before_its_date_is_open():
    data = make_data(contacts=[promise("2026-11-10", 50000, "2026-11-20")])
    status = contact_log.promise_status(data, CUSTOMER, TODAY)
    assert status == {"contact_id": 1, "date": "2026-11-10", "amount": 50000, "promised_date": "2026-11-20",
                      "paid_since": 0, "state": "open"}


def test_promise_is_open_on_the_promised_date_and_broken_the_day_after():
    data = make_data(contacts=[promise("2026-11-10", 50000, "2026-11-15")])
    assert contact_log.promise_status(data, CUSTOMER, TODAY)["state"] == "open"
    assert contact_log.promise_status(data, CUSTOMER, TODAY + timedelta(days=1))["state"] == "broken"


def test_full_payment_after_the_promise_keeps_it():
    data = make_data(payments=[(1, "2026-11-12", 30000), (2, "2026-11-14", 20000)],
                     contacts=[promise("2026-11-10", 50000, "2026-11-20")])
    status = contact_log.promise_status(data, CUSTOMER, TODAY)
    assert status["state"] == "kept"
    assert status["paid_since"] == 50000


def test_kept_promise_stays_kept_after_its_date():
    data = make_data(payments=[(1, "2026-11-12", 50000)], contacts=[promise("2026-11-10", 50000, "2026-11-12")])
    assert contact_log.promise_status(data, CUSTOMER, TODAY)["state"] == "kept"


def test_partial_payment_leaves_the_promise_open():
    data = make_data(payments=[(1, "2026-11-12", 20000)], contacts=[promise("2026-11-10", 50000, "2026-11-20")])
    status = contact_log.promise_status(data, CUSTOMER, TODAY)
    assert status["state"] == "open"
    assert status["paid_since"] == 20000


def test_payments_on_or_before_the_promise_day_do_not_count():
    data = make_data(payments=[(1, "2026-11-01", 50000), (1, "2026-11-10", 50000)],
                     contacts=[promise("2026-11-10", 50000, "2026-11-12")])
    assert contact_log.promise_status(data, CUSTOMER, TODAY)["state"] == "broken"


def test_newest_promise_wins():
    data = make_data(contacts=[promise("2026-11-01", 10000, "2026-11-05"), promise("2026-11-08", 70000, "2026-11-30")])
    status = contact_log.promise_status(data, CUSTOMER, TODAY)
    assert (status["amount"], status["state"]) == (70000, "open")


def test_promise_status_accepts_today_as_a_string():
    data = make_data(contacts=[promise("2026-11-10", 50000, "2026-11-14")])
    assert contact_log.promise_status(data, CUSTOMER, "2026-11-15")["state"] == "broken"


# db helpers

def test_add_and_delete_contact():
    with db.connect() as conn:
        cid = db.add_customer(conn, "Test Mills")
        contact_id = db.add_contact(conn, cid, "2026-11-15", "promise", promised_amount=1000,
                                    promised_date="2026-11-20")
    [row] = db.load_all()["contacts"]
    assert row["id"] == contact_id and row["promised_amount"] == 1000 and row["language"] == ""
    with db.connect() as conn:
        assert db.delete_contact(conn, contact_id) is True
        assert db.delete_contact(conn, contact_id) is False
    assert db.load_all()["contacts"] == []


def test_delete_contact_returns_false_for_a_missing_id():
    with db.connect() as conn:
        assert db.delete_contact(conn, 999) is False


# the seeded demo cases

def test_seed_has_the_five_contact_cases(seeded):
    data = seeded
    today = date.today()
    ago = lambda days: (today - timedelta(days=days)).isoformat()  # noqa: E731
    ids = {c["name"]: c["id"] for c in data["customers"]}
    assert len(data["contacts"]) == 5

    sharma = ids["Sharma Knit Processors"]
    assert contact_log.last_reminder(data, sharma)["date"] == ago(9)
    assert contact_log.reminder_count(data, sharma) == 1

    ganesh = contact_log.promise_status(data, ids["Shree Ganesh Processors"], today)
    assert (ganesh["amount"], ganesh["date"], ganesh["promised_date"], ganesh["state"]) == \
        (500000, ago(10), ago(3), "broken")

    assert contact_log.last_reminder(data, ids["Gupta Woollen Mills"])["date"] == ago(2)

    arora = contact_log.promise_status(data, ids["Arora Fabrics"], today)
    assert (arora["amount"], arora["date"], arora["promised_date"], arora["state"]) == \
        (100000, ago(4), ago(-6), "open")

    kaur = ids["Kaur Hosiery Works"]
    assert contact_log.last_reminder(data, kaur)["date"] == ago(40)
    assert contact_log.customer_payments(data, kaur)[-1]["date"] == ago(20)
    assert contact_log.reminder_count(data, kaur) == 0
