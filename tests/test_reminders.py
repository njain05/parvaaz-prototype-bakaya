"""Reminder tone rises with each reminder since the last payment, and Ask can answer promise questions."""
import pytest

import app as app_module
import contact_log
import db
import offline


@pytest.fixture
def client(seeded):
    return app_module.app.test_client()


def customer_id(data, name):
    return next(c["id"] for c in data["customers"] if c["name"].startswith(name))


def test_tone_for():
    assert offline.tone_for(10) == "gentle"
    assert offline.tone_for(10, 0) == "gentle"
    assert offline.tone_for(10, 1) == "firm"
    assert offline.tone_for(30, 1) == "serious"
    assert offline.tone_for(10, 5) == "serious"
    assert offline.tone_for(60, 2) == "serious"
    assert offline.tone_for(0, 3) == "upcoming"


def template_for(order_id, tone, language="english"):
    """The template text for this order in the given tone, with the same facts the route uses."""
    order = next(o for o in app_module.book()["orders"] if o["id"] == order_id)
    facts = app_module.reminder_facts(order)
    return offline.TEMPLATES[language][tone].format(
        person=offline.greeting_name(facts["contact_person"], facts["customer"]),
        biz=facts["business_name"], amt=facts["amount_due"], machine=facts["machine"],
        id=facts["order_id"], due=facts["due_date"], days=facts["days_overdue"],
    )


def draft(client, order_id):
    r = client.post("/api/ai/reminder", json={"order_id": order_id, "language": "english"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["source"] == "template" and set(body) == {"message", "source", "phone", "note"}
    return body["message"]


def test_reminder_is_one_step_firmer_after_a_reminder(client, seeded):
    # Gupta is 15 days late (firm) and was reminded 2 days ago, so the next reminder is serious.
    # Sharma, named in the ticket, is 60 days late: serious either way, so it can't show the step.
    cid = customer_id(seeded, "Gupta")
    order_id = next(c["order_id"] for c in seeded["contacts"] if c["customer_id"] == cid)
    days = next(o for o in app_module.book()["orders"] if o["id"] == order_id)["days_overdue"]
    base = offline.tone_for(days)
    assert base == "firm"
    assert contact_log.reminder_count(seeded, cid) == 1

    reminded = draft(client, order_id)

    with db.connect() as conn:
        for c in seeded["contacts"]:
            if c["customer_id"] == cid and c["kind"] == "reminder":
                db.delete_contact(conn, c["id"])
    not_reminded = draft(client, order_id)

    assert not_reminded == template_for(order_id, base)
    assert reminded == template_for(order_id, "serious")


def test_reminder_facts_carry_the_count(seeded):
    cid = customer_id(seeded, "Sharma")
    order = next(o for o in app_module.book()["orders"] if o["customer_id"] == cid and o["overdue"] > 0.5)
    assert app_module.reminder_facts(order)["reminder_count"] == 1


def test_offline_promise_answer(seeded):
    b = app_module.book()
    people = app_module.ai_snapshot(b, seeded)["customers"]
    text = offline.answer("who promised to pay?", b, people)
    assert "Shree Ganesh Processors" in text and "(broken)" in text.split("Shree Ganesh")[1].split("\n")[0]
    assert "Arora Fabrics" in text and "(open)" in text.split("Arora")[1].split("\n")[0]
    assert "Sharma" not in text
    assert offline.answer("Kisne vaada kiya?", b, people) == text


def test_offline_promise_answer_none():
    assert offline.answer("any promises?", {"customers": [], "totals": {}}, []) == "No one has an open promise to pay."


def test_snapshot_has_contact_facts(seeded):
    people = {c["name"]: c for c in app_module.ai_snapshot(app_module.book(), seeded)["customers"]}
    sharma = people["Sharma Knit Processors"]
    assert sharma["reminders_since_last_payment"] == 1 and sharma["last_reminder_date"]
    assert sharma["promise"] is None
    assert people["Kaur Hosiery Works"]["reminders_since_last_payment"] == 0
    assert people["Kaur Hosiery Works"]["last_reminder_date"]
    assert people["Arora Fabrics"]["promise"]["state"] == "open"


def test_ask_route_answers_promises(client):
    body = client.post("/api/ai/ask", json={"question": "Who promised to pay?"}).get_json()
    assert body["source"] == "offline"
    assert "Shree Ganesh" in body["answer"] and "Arora" in body["answer"]
