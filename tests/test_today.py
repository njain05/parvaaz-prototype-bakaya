"""The Today rules: who is Late, who is Coming up, who is hidden, and the why line for each."""
from datetime import date, timedelta

import app
import db
import ledger
from today import build_today, lakh

TODAY = date(2026, 11, 15)


def day(offset, base=TODAY):
    return (base + timedelta(days=offset)).isoformat()


def run(today=TODAY):
    data = db.load_all()
    return build_today(ledger.build(data, today), data, today)


def names(rows):
    return [r["name"] for r in rows]


def row(rows, name):
    return next(r for r in rows if r["name"] == name)


def add_customer(name, sales, payments=(), contacts=()):
    """sales: [(total, [(amount, due offset)])]; payments: [(sale index, day offset, amount)];
    contacts: [(kind, day offset, extra)]. Offsets are days from TODAY."""
    with db.connect() as conn:
        cid = db.add_customer(conn, name, city="Ludhiana")
        oids = [db.add_order(conn, cid, "Machine", day(-100), total,
                             [{"label": f"Part {i}", "amount": a, "due_date": day(d)}
                              for i, (a, d) in enumerate(plan, 1)])
                for total, plan in sales]
        for i, d, amount in payments:
            db.add_payment(conn, oids[i], day(d), amount)
        for kind, d, extra in contacts:
            db.add_contact(conn, cid, day(d), kind, order_id=oids[0], **extra)
    return cid


# The seeded demo

def test_broken_promise_is_first_late_row(seeded):
    t = run(date.today())
    first = t["late"][0]
    assert first["name"] == "Shree Ganesh Processors"
    assert first["flag"] == "broken_promise"
    by = (date.today() - timedelta(days=3)).strftime("%-d %b")
    assert first["why"].startswith(f"Promised ₹5 lakh by {by}. Not received.")


def test_recently_reminded_and_open_promise_are_hidden(seeded):
    t = run(date.today())
    shown = names(t["late"]) + names(t["coming_up"])
    assert "Gupta Woollen Mills" not in shown
    assert "Arora Fabrics" not in shown


def test_contact_sentences(seeded):
    t = run(date.today())
    sharma = row(t["late"], "Sharma Knit Processors")
    assert "Reminded 9 days ago, no payment yet." in sharma["why"]
    assert sharma["flag"] == "reminded"
    kaur = row(t["late"], "Kaur Hosiery Works")
    assert kaur["why"].endswith("Not reminded yet.")
    assert kaur["flag"] is None


def test_customer_late_on_two_sales_appears_once_with_summed_amount(seeded):
    t = run(date.today())
    assert names(t["late"]).count("Tirupur Knit Finishers") == 1
    assert row(t["late"], "Tirupur Knit Finishers")["amount"] == 210000 + 85000


def test_seeded_coming_up(seeded):
    t = run(date.today())
    assert names(t["coming_up"]) == ["Malhotra Textiles"]
    m = t["coming_up"][0]
    assert m["amount"] == 960000
    assert m["why"].startswith("Due in 5 days")


def test_totals_come_from_the_book(seeded):
    t = run(date.today())
    b = ledger.build(seeded, date.today())
    assert t["totals"] == {"owed": b["totals"]["outstanding"], "late": b["totals"]["overdue"]}


# Hand-built cases on a fixed date

def test_late_row_fields_and_why():
    cid = add_customer("Late Mills", [(300000, [(100000, -40), (200000, -10)])], payments=[(0, -35, 100000)])
    r = run()["late"][0]
    assert r == {
        "customer_id": cid, "name": "Late Mills", "city": "Ludhiana", "amount": 200000, "days_late": 10,
        "due_date": day(-10), "why": "10 days late. Usually pays about 8 days late. Not reminded yet.",
        "flag": None, "remind_order_id": r["remind_order_id"],
    }
    assert r["remind_order_id"] is not None


def test_late_due_date_is_the_oldest_late_instalment_across_sales():
    add_customer("Two Sales", [(100000, [(100000, -5)]), (50000, [(50000, -30)])])
    r = run()["late"][0]
    assert r["amount"] == 150000
    assert r["due_date"] == day(-30)
    assert r["days_late"] == 30


def test_late_order_is_by_amount():
    add_customer("Small", [(50000, [(50000, -60)])])
    add_customer("Big", [(500000, [(500000, -5)])])
    assert names(run()["late"]) == ["Big", "Small"]


def test_broken_promises_go_first_biggest_promise_first():
    add_customer("Huge Late", [(900000, [(900000, -10)])])
    add_customer("Small Promise", [(200000, [(200000, -10)])],
                 contacts=[("promise", -8, {"promised_amount": 50000, "promised_date": day(-2)})])
    add_customer("Big Promise", [(200000, [(200000, -10)])],
                 contacts=[("promise", -8, {"promised_amount": 150000, "promised_date": day(-2)})])
    assert names(run()["late"]) == ["Big Promise", "Small Promise", "Huge Late"]


def test_promise_hides_up_to_and_including_its_date_then_breaks():
    add_customer("Promiser", [(200000, [(200000, -10)])],
                 contacts=[("promise", -5, {"promised_amount": 200000, "promised_date": day(0)})])
    assert run()["late"] == []
    later = run(TODAY + timedelta(days=1))["late"]
    assert later[0]["flag"] == "broken_promise"
    assert later[0]["why"].startswith("Promised ₹2 lakh by 15 Nov. Not received.")


def test_kept_promise_falls_back_to_the_normal_rules():
    add_customer("Kept", [(300000, [(100000, -20), (200000, -10)])], payments=[(0, -2, 100000)],
                 contacts=[("promise", -5, {"promised_amount": 100000, "promised_date": day(-3)})])
    r = run()["late"][0]
    assert r["flag"] is None
    assert r["amount"] == 200000


def test_reminder_hides_for_fewer_than_five_days():
    add_customer("Reminded", [(100000, [(100000, -30)])], contacts=[("reminder", -4, {})])
    assert run()["late"] == []
    r = run(TODAY + timedelta(days=1))["late"][0]
    assert r["why"].endswith("Reminded 5 days ago, no payment yet.")
    assert r["flag"] == "reminded"


def test_coming_up_only_within_seven_days_and_never_when_late():
    add_customer("Due Today", [(100000, [(100000, 0)])])
    add_customer("Due Tomorrow", [(100000, [(100000, 1)])])
    add_customer("Due In 7", [(100000, [(60000, 7), (40000, 7)])])
    add_customer("Due In 8", [(100000, [(100000, 8)])])
    add_customer("Late And Due", [(200000, [(100000, -3), (100000, 2)])])
    t = run()
    assert names(t["coming_up"]) == ["Due Today", "Due Tomorrow", "Due In 7"]
    assert names(t["late"]) == ["Late And Due"]
    assert [r["why"] for r in t["coming_up"]] == ["Due today.", "Due tomorrow.", "Due in 7 days (22 Nov)."]
    assert row(t["coming_up"], "Due In 7")["amount"] == 100000
    assert all(r["flag"] is None and r["days_late"] == 0 for r in t["coming_up"])


def test_coming_up_sums_instalments_in_the_window_and_orders_by_date_then_amount():
    add_customer("Two Due", [(300000, [(100000, 3), (100000, 6), (100000, 20)])])
    add_customer("Same Day Big", [(500000, [(500000, 3)])])
    t = run()
    assert names(t["coming_up"]) == ["Same Day Big", "Two Due"]
    two = row(t["coming_up"], "Two Due")
    assert two["amount"] == 200000
    assert two["due_date"] == day(3)


def test_paid_up_customers_are_skipped():
    add_customer("Paid", [(100000, [(100000, -30)])], payments=[(0, -30, 100000)])
    t = run()
    assert t["late"] == [] and t["coming_up"] == []


def test_habit_sentences():
    add_customer("On Time", [(200000, [(100000, -40), (100000, -5)])], payments=[(0, -40, 100000)])
    add_customer("New", [(100000, [(100000, 3)])])
    t = run()
    assert row(t["late"], "On Time")["why"] == "5 days late. Usually pays on time. Not reminded yet."
    assert row(t["coming_up"], "New")["why"] == "Due in 3 days (18 Nov)."


# lakh() and the route

def test_lakh():
    assert lakh(510000) == "₹5.1 lakh"
    assert lakh(500000) == "₹5 lakh"
    assert lakh(1230000) == "₹12.3 lakh"
    assert lakh(85000) == "₹85,000"


def test_get_today_route(seeded):
    res = app.app.test_client().get("/api/today")
    assert res.status_code == 200
    body = res.get_json()
    assert set(body) == {"today", "totals", "late", "coming_up"}
    assert set(body["totals"]) == {"owed", "late"}
    keys = {"customer_id", "name", "city", "amount", "days_late", "due_date", "why", "flag", "remind_order_id"}
    assert all(set(r) == keys for r in body["late"] + body["coming_up"])
    assert body["late"][0]["name"] == "Shree Ganesh Processors"
