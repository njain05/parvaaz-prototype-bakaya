"""POST /api/orders tells the Add sale form which customer page to open (T11)."""
import pytest

import app as app_module
import db


@pytest.fixture
def client(seeded):
    return app_module.app.test_client()


def plan(total=720000):
    return [
        {"label": "Advance", "amount": 216000, "due_date": "2026-11-01"},
        {"label": "Before dispatch", "amount": 432000, "due_date": "2026-12-16"},
        {"label": "After installation", "amount": total - 216000 - 432000, "due_date": "2027-01-15"},
    ]


def test_existing_customer_returns_its_id(client, seeded):
    kaur = next(c["id"] for c in seeded["customers"] if c["name"] == "Kaur Hosiery Works")
    r = client.post("/api/orders", json={"customer_id": kaur, "machine": "Tumble Dryer", "total": 720000,
                                         "order_date": "2026-11-01", "milestones": plan()})
    assert r.status_code == 200
    body = r.get_json()
    assert body["customer_id"] == kaur
    order = next(o for o in db.load_all()["orders"] if o["id"] == body["id"])
    assert order["customer_id"] == kaur


def test_new_customer_returns_the_new_id(client, seeded):
    before = {c["id"] for c in seeded["customers"]}
    r = client.post("/api/orders", json={
        "new_customer": {"name": "Jindal Knits", "contact_person": "Ravi Jindal", "phone": "", "city": "Ludhiana"},
        "machine": "Shearing Machine", "total": 720000, "order_date": "2026-11-01", "milestones": plan(),
        "advance_received": 216000,
    })
    assert r.status_code == 200
    body = r.get_json()
    assert body["customer_id"] not in before
    data = db.load_all()
    new = next(c for c in data["customers"] if c["id"] == body["customer_id"])
    assert new["name"] == "Jindal Knits" and new["city"] == "Ludhiana"
    assert next(o for o in data["orders"] if o["id"] == body["id"])["customer_id"] == new["id"]
    assert sum(p["amount"] for p in data["payments"] if p["order_id"] == body["id"]) == 216000
