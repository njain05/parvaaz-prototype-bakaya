"""The customer details route, the contact log routes and number checks on the money routes."""
from datetime import date, timedelta

import pytest

import app as app_module


@pytest.fixture
def client(seeded):
    return app_module.app.test_client()


def customer_id(data, name):
    return next(c["id"] for c in data["customers"] if c["name"].startswith(name))


def other_customers_order(data, cid):
    return next(o["id"] for o in data["orders"] if o["customer_id"] != cid)


def test_number():
    assert app_module.number("12.5") == 12.5
    assert app_module.number(3) == 3.0
    for bad in (None, "", "abc", "nan", "inf", float("nan"), True, [1]):
        assert app_module.number(bad) is None


def test_customer_details(client, seeded):
    cid = customer_id(seeded, "Sharma")
    c = client.get(f"/api/customers/{cid}").get_json()
    assert c["name"] == "Sharma Knit Processors"
    for key in ("owed", "late", "days_late", "habit", "avg_days_late", "remind_order_id", "promise", "sales"):
        assert key in c
    assert c["sales"] and all(o["customer_id"] == cid for o in c["sales"])
    dates = [h["date"] for h in c["history"]]
    assert dates == sorted(dates, reverse=True)
    assert any(h["kind"] == "reminder" and h["language"] == "hinglish" for h in c["history"])
    pay = next(h for h in c["history"] if h["kind"] == "payment")
    assert pay["machine"] and pay["contact_id"] is None


def test_unknown_customer(client):
    r = client.get("/api/customers/9999")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Customer not found."}


def test_reminder_add_and_undo(client, seeded):
    cid = customer_id(seeded, "Sharma")
    r = client.post(f"/api/customers/{cid}/contacts", json={"kind": "reminder", "language": "hindi"})
    new_id = r.get_json()["id"]
    first = client.get(f"/api/customers/{cid}").get_json()["history"]
    today_rows = [h for h in first if h["date"] == date.today().isoformat()]
    assert today_rows[-1]["contact_id"] == new_id  # contacts come after payments on the same day

    assert client.delete(f"/api/contacts/{new_id}").get_json() == {"ok": True}
    after = client.get(f"/api/customers/{cid}").get_json()["history"]
    assert all(h["contact_id"] != new_id for h in after)

    again = client.delete(f"/api/contacts/{new_id}")
    assert again.status_code == 404
    assert again.get_json() == {"error": "Already removed."}


def test_promise_shows_as_open(client, seeded):
    cid = customer_id(seeded, "Sharma")
    by = (date.today() + timedelta(days=3)).isoformat()
    r = client.post(f"/api/customers/{cid}/contacts",
                    json={"kind": "promise", "promised_amount": "50000", "promised_date": by})
    assert r.status_code == 200
    c = client.get(f"/api/customers/{cid}").get_json()
    assert c["promise"]["state"] == "open" and c["promise"]["amount"] == 50000
    assert c["history"][0]["kind"] == "promise" and c["history"][0]["promised_date"] == by


@pytest.mark.parametrize("body, error", [
    ({"kind": "call"}, "Unknown contact type."),
    ({"kind": "promise", "promised_date": "2099-01-01"}, "Enter the amount they promised."),
    ({"kind": "promise", "promised_amount": "abc", "promised_date": "2099-01-01"}, "Enter the amount they promised."),
    ({"kind": "promise", "promised_amount": 5000, "promised_date": "2020-01-01"},
     "Enter the date they promised to pay by."),
    ({"kind": "promise", "promised_amount": 5000, "promised_date": "soon"}, "Enter the date they promised to pay by."),
])
def test_contact_errors(client, seeded, body, error):
    cid = customer_id(seeded, "Sharma")
    r = client.post(f"/api/customers/{cid}/contacts", json=body)
    assert r.status_code == 400
    assert r.get_json() == {"error": error}


def test_contact_for_another_customers_sale(client, seeded):
    cid = customer_id(seeded, "Sharma")
    r = client.post(f"/api/customers/{cid}/contacts",
                    json={"kind": "reminder", "order_id": other_customers_order(seeded, cid)})
    assert r.status_code == 400
    assert r.get_json() == {"error": "That sale isn't this customer's."}


def test_contact_for_unknown_customer(client):
    r = client.post("/api/customers/9999/contacts", json={"kind": "reminder"})
    assert r.status_code == 404


@pytest.mark.parametrize("amount", ["abc", "nan", "inf", None])
def test_payment_bad_amount(client, seeded, amount):
    oid = seeded["orders"][0]["id"]
    r = client.post(f"/api/orders/{oid}/payments", json={"amount": amount, "date": date.today().isoformat()})
    assert r.status_code == 400
    assert r.get_json() == {"error": "Enter the amount received."}


def sale(**changes):
    body = {"customer_id": 1, "machine": "Dryer", "total": 100000, "order_date": "2026-11-01",
            "milestones": [{"label": "Advance", "amount": 100000, "due_date": "2026-11-01"}]}
    return {**body, **changes}


@pytest.mark.parametrize("body, error", [
    (sale(total="abc"), "Enter the total amount."),
    (sale(total="inf"), "Enter the total amount."),
    (sale(milestones=[{"amount": "abc", "due_date": "2026-11-01"}]),
     "Each payment instalment needs an amount and a due date."),
    (sale(advance_received="abc"), "Advance received can't be more than the total."),
])
def test_order_bad_numbers(client, body, error):
    r = client.post("/api/orders", json=body)
    assert r.status_code == 400
    assert r.get_json() == {"error": error}


def test_order_still_saves(client):
    r = client.post("/api/orders", json=sale(total="100000", advance_received="30000"))
    assert r.status_code == 200 and r.get_json()["id"]
