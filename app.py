"""Bakaya: credit and payment tracker for machinery makers.

Run:  .venv/bin/python app.py   then open http://localhost:5055
"""
import math
import os
from datetime import date, timedelta

from flask import Flask, jsonify, request, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env_file(path=os.path.join(HERE, ".env")):
    """Read KEY=value lines from .env into the environment (without overriding real env vars)."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                if value:
                    os.environ.setdefault(key.strip(), value)


load_env_file()

import ai  # noqa: E402  (imported after .env is loaded)
import contact_log  # noqa: E402
import db  # noqa: E402
import ledger  # noqa: E402
import offline  # noqa: E402
import seed  # noqa: E402
import today  # noqa: E402

BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "Demo Machinery Works")
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


def book():
    b = ledger.build(db.load_all())
    b["week_end"] = (date.fromisoformat(b["today"]) + timedelta(days=ledger.DUE_SOON_DAYS)).isoformat()
    return b


def bad(msg, code=400):
    return jsonify({"error": msg}), code


def number(value):
    """The value as a float, or None when it is missing, not a number, NaN or infinite."""
    if value is None or isinstance(value, bool):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if math.isfinite(n) else None


def valid_date(s):
    try:
        date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


@app.get("/")
def index():
    return send_from_directory(os.path.join(HERE, "static"), "index.html")


@app.get("/api/status")
def status():
    return jsonify({"ai_enabled": ai.enabled(), "business_name": BUSINESS_NAME})


@app.get("/api/book")
def get_book():
    return jsonify(book())


@app.get("/api/today")
def get_today():
    data, day = db.load_all(), date.today()
    return jsonify(today.build_today(ledger.build(data, day), data, day))


@app.post("/api/orders")
def create_order():
    body = request.get_json(force=True)
    machine = (body.get("machine") or "").strip()
    total = number(body.get("total"))
    order_date = body.get("order_date")
    milestones = body.get("milestones") or []
    advance = number(body.get("advance_received") or 0)

    if not machine:
        return bad("Enter the machine or item sold.")
    if total is None or total <= 0:
        return bad("Enter the total amount.")
    if not valid_date(order_date):
        return bad("Enter a valid order date.")
    if not milestones or any(not valid_date(m.get("due_date")) or (number(m.get("amount")) or 0) <= 0
                             for m in milestones):
        return bad("Each payment instalment needs an amount and a due date.")
    if abs(sum(number(m["amount"]) for m in milestones) - total) > 1:
        return bad("The instalments must add up to the total amount.")
    if advance is None or advance < 0 or advance > total:
        return bad("Advance received can't be more than the total.")

    with db.connect() as conn:
        cid = body.get("customer_id")
        if not cid:
            nc = body.get("new_customer") or {}
            name = (nc.get("name") or "").strip()
            if not name:
                return bad("Choose a customer or enter a new customer's name.")
            cid = db.add_customer(conn, name, nc.get("contact_person", "").strip(),
                                  nc.get("phone", "").strip(), nc.get("city", "").strip())
        oid = db.add_order(conn, int(cid), machine, order_date, total,
                           [{"label": m.get("label") or "Instalment", "amount": number(m["amount"]),
                             "due_date": m["due_date"]} for m in milestones],
                           body.get("notes", ""))
        if advance > 0:
            db.add_payment(conn, oid, order_date, advance, body.get("advance_mode", ""), "Advance")
    return jsonify({"id": oid})


@app.post("/api/orders/<int:order_id>/payments")
def record_payment(order_id):
    body = request.get_json(force=True)
    amount = number(body.get("amount"))
    pay_date = body.get("date")
    order = next((o for o in book()["orders"] if o["id"] == order_id), None)
    if not order:
        return bad("Order not found.", 404)
    if amount is None or amount <= 0:
        return bad("Enter the amount received.")
    if amount > order["balance"] + 1:
        return bad(f"That's more than the balance of {ledger.inr(order['balance'])}.")
    if not valid_date(pay_date):
        return bad("Enter a valid date.")
    with db.connect() as conn:
        db.add_payment(conn, order_id, pay_date, amount, body.get("mode", ""), body.get("note", ""))
    return jsonify({"ok": True})


def history(data, customer_id, customer_orders):
    """The customer's payments and contacts in one list, newest first; payments before contacts on the same day."""
    machines = {o["id"]: o["machine"] for o in customer_orders}
    rows = []
    for p in data["payments"]:
        if p["order_id"] in machines:
            rows.append((0, p["id"], {
                "date": p["date"], "kind": "payment", "amount": p["amount"], "order_id": p["order_id"],
                "machine": machines[p["order_id"]], "mode": p["mode"], "note": p["note"],
                "language": None, "promised_date": None, "contact_id": None,
            }))
    for c in data["contacts"]:
        if c["customer_id"] == customer_id:
            rows.append((1, c["id"], {
                "date": c["date"], "kind": c["kind"], "amount": c["promised_amount"], "order_id": c["order_id"],
                "machine": machines.get(c["order_id"]), "mode": None, "note": c["note"],
                "language": c["language"], "promised_date": c["promised_date"], "contact_id": c["id"],
            }))
    rows.sort(key=lambda r: (r[2]["date"], -r[0], r[1]), reverse=True)
    return [row for _, _, row in rows]


@app.get("/api/customers/<int:customer_id>")
def get_customer(customer_id):
    data, day = db.load_all(), date.today()
    b = ledger.build(data, day)
    c = next((c for c in b["customers"] if c["id"] == customer_id), None)
    if not c:
        return bad("Customer not found.", 404)
    sales = [o for o in b["orders"] if o["customer_id"] == customer_id]
    return jsonify({
        **{k: c[k] for k in ("id", "name", "contact_person", "phone", "city")},
        "owed": c["outstanding"],
        "late": c["overdue"],
        "days_late": c["days_overdue"],
        "habit": c["habit"],
        "avg_days_late": c["avg_days_late"],
        "remind_order_id": c["remind_order_id"],
        "promise": contact_log.promise_status(data, customer_id, day),
        "sales": sales,
        "history": history(data, customer_id, sales),
    })


@app.post("/api/customers/<int:customer_id>/contacts")
def add_contact(customer_id):
    body = request.get_json(force=True)
    data, day = db.load_all(), date.today().isoformat()
    if not any(c["id"] == customer_id for c in data["customers"]):
        return bad("Customer not found.", 404)
    kind = body.get("kind")
    if kind not in ("reminder", "promise"):
        return bad("Unknown contact type.")
    order_id = body.get("order_id")
    if order_id is not None and not any(o["id"] == order_id and o["customer_id"] == customer_id
                                        for o in data["orders"]):
        return bad("That sale isn't this customer's.")
    promised_amount = promised_date = None
    if kind == "promise":
        promised_amount, promised_date = number(body.get("promised_amount")), body.get("promised_date")
        if promised_amount is None or promised_amount <= 0:
            return bad("Enter the amount they promised.")
        if not valid_date(promised_date) or promised_date < day:
            return bad("Enter the date they promised to pay by.")
    with db.connect() as conn:
        new_id = db.add_contact(conn, customer_id, day, kind, order_id=order_id,
                                language=(body.get("language") or "") if kind == "reminder" else "",
                                promised_amount=promised_amount, promised_date=promised_date,
                                note=(body.get("note") or "").strip())
    return jsonify({"id": new_id})


@app.delete("/api/contacts/<int:contact_id>")
def delete_contact(contact_id):
    with db.connect() as conn:
        if not db.delete_contact(conn, contact_id):
            return bad("Already removed.", 404)
    return jsonify({"ok": True})


def reminder_facts(order):
    if order["overdue"] > 0.5:
        unpaid = [m for m in order["milestones"] if m["status"] == "overdue"]
        amount, due = order["overdue"], unpaid[0]["due_date"]
    elif order["next_due"]:
        amount, due = order["next_due"]["amount"], order["next_due"]["due_date"]
    else:
        return None
    customer = next(c for c in db.load_all()["customers"] if c["id"] == order["customer_id"])
    return {
        "business_name": BUSINESS_NAME,
        "customer": order["customer_name"],
        "contact_person": customer["contact_person"],
        "machine": order["machine"],
        "order_id": order["id"],
        "amount_due": ledger.inr(amount),
        "due_date": ledger.nice_date(due),
        "days_overdue": order["days_overdue"],
        "phone": customer["phone"],
    }


@app.post("/api/ai/reminder")
def reminder():
    body = request.get_json(force=True)
    language = body.get("language", "english")
    order = next((o for o in book()["orders"] if o["id"] == body.get("order_id")), None)
    if not order:
        return bad("Order not found.", 404)
    facts = reminder_facts(order)
    if not facts:
        return bad("This order is fully paid. No reminder needed.")

    note = None
    if ai.enabled():
        try:
            return jsonify({"message": ai.draft_reminder(facts, language), "source": "ai", "phone": facts["phone"]})
        except ai.AIError as e:
            note = f"AI unavailable ({e}), so a template was used."
    return jsonify({"message": offline.template_reminder(facts, language), "source": "template",
                    "phone": facts["phone"], "note": note})


def ai_snapshot(b):
    """A compact view of the credit book to send to the AI."""
    return {
        "today": b["today"],
        "totals": b["totals"],
        "customers": [
            {k: c[k] for k in ("name", "city", "outstanding", "overdue", "days_overdue", "habit", "avg_days_late")}
            for c in b["customers"]
        ],
        "orders": [
            {
                "id": o["id"], "customer": o["customer_name"], "machine": o["machine"],
                "order_date": o["order_date"], "total": o["total"], "paid": o["paid"],
                "balance": o["balance"], "overdue": o["overdue"], "status": o["status"],
                "instalments": [
                    {"label": m["label"], "amount": m["amount"], "due_date": m["due_date"],
                     "unpaid": m["unpaid"], "status": m["status"]}
                    for m in o["milestones"]
                ],
            }
            for o in b["orders"]
        ],
    }


@app.post("/api/ai/ask")
def ask():
    question = (request.get_json(force=True).get("question") or "").strip()
    if not question:
        return bad("Type a question.")
    b = book()
    note = None
    if ai.enabled():
        try:
            return jsonify({"answer": ai.answer_question(question, ai_snapshot(b)), "source": "ai"})
        except ai.AIError as e:
            note = f"AI unavailable ({e}). Showing a basic answer."
    return jsonify({"answer": offline.answer(question, b), "source": "offline", "note": note})


@app.post("/api/ai/scan")
def scan():
    if not ai.enabled():
        return bad("Reading bills needs the AI. Add ANTHROPIC_API_KEY to the .env file and restart the app.")
    f = request.files.get("image")
    if not f:
        return bad("Choose a photo of a bill first.")
    if f.mimetype not in IMAGE_TYPES:
        return bad("Use a JPG, PNG or WebP photo.")
    data = f.read()
    if len(data) > 5 * 1024 * 1024:
        return bad("That photo is too large (max 5 MB). Try a smaller one.")
    try:
        fields = ai.read_bill(data, f.mimetype)
    except ai.AIError as e:
        return bad(str(e), 502)
    if not fields.get("is_bill"):
        return bad("That doesn't look like a bill or invoice. Try a clearer photo.")
    return jsonify(fields)


@app.post("/api/demo/reset")
def reset_demo():
    seed.seed()
    return jsonify({"ok": True})


if __name__ == "__main__":
    db.init()
    if db.is_empty():
        seed.seed()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5055)), debug=False)
