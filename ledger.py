"""Works out balances, overdue amounts and payment habits from the raw records.

Payments are applied to an order's milestones in due-date order: the first
payment clears the advance, the next ones the dispatch instalment, and so on.
"""
from datetime import date, timedelta

EPS = 0.5  # amounts below half a rupee count as fully paid
DUE_SOON_DAYS = 7


def _d(s):
    return date.fromisoformat(s)


def inr(n):
    """Format a number as Indian rupees with lakh grouping: 1234567 -> ₹12,34,567."""
    n = int(round(n))
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if n < 0 else "") + "₹" + s


def nice_date(iso):
    return _d(iso).strftime("%-d %b %Y")


def compute_order(order, milestones, payments, today):
    total = order["total"]
    paid = sum(p["amount"] for p in payments)
    ms = sorted(milestones, key=lambda m: (m["due_date"], m["id"]))
    pays = sorted(payments, key=lambda p: (p["date"], p["id"]))

    cum = 0.0
    out_ms = []
    overdue = 0.0
    oldest_unpaid_due = None
    next_due = None
    lateness = []  # days late, one entry per milestone that has fallen due
    overdue_parts = []  # (days overdue, amount) for the ageing chart

    for m in ms:
        cum += m["amount"]
        unpaid = max(0.0, min(m["amount"], cum - paid))
        due = _d(m["due_date"])

        covered_on = None
        if unpaid <= EPS:
            running = 0.0
            for p in pays:
                running += p["amount"]
                if running >= cum - EPS:
                    covered_on = _d(p["date"])
                    break

        if unpaid > EPS and due < today:
            status = "overdue"
            days = (today - due).days
            overdue += unpaid
            overdue_parts.append((days, unpaid))
            lateness.append(days)
            if oldest_unpaid_due is None:
                oldest_unpaid_due = due
        elif unpaid > EPS:
            status = "upcoming"
            if next_due is None:
                next_due = {"amount": unpaid, "due_date": m["due_date"], "label": m["label"]}
        else:
            status = "paid"
            if covered_on and due <= today:
                lateness.append(max(0, (covered_on - due).days))

        out_ms.append({
            **m,
            "unpaid": round(unpaid, 2),
            "status": status,
            "partly_paid": EPS < unpaid < m["amount"] - EPS,
            "paid_on": covered_on.isoformat() if covered_on else None,
        })

    balance = max(0.0, total - paid)
    if balance <= EPS:
        status = "paid"
    elif overdue > EPS:
        status = "overdue"
    elif next_due and _d(next_due["due_date"]) <= today + timedelta(days=DUE_SOON_DAYS):
        status = "due_soon"
    else:
        status = "on_track"

    return {
        **order,
        "paid": round(paid, 2),
        "balance": round(balance, 2),
        "overdue": round(overdue, 2),
        "days_overdue": (today - oldest_unpaid_due).days if oldest_unpaid_due else 0,
        "next_due": next_due,
        "status": status,
        "milestones": out_ms,
        "payments": pays,
        "_lateness": lateness,
        "_overdue_parts": overdue_parts,
    }


def habit(lateness):
    """Label a customer's payment habit from how many days late their past instalments were."""
    if not lateness:
        return "new"
    avg = sum(lateness) / len(lateness)
    if avg <= 7:
        return "on_time"
    if avg <= 30:
        return "sometimes_late"
    return "often_late"


def build(data, today=None):
    """Turn raw tables into orders, customers and dashboard totals."""
    today = today or date.today()
    customers = {c["id"]: c for c in data["customers"]}
    ms_by_order, pay_by_order = {}, {}
    for m in data["milestones"]:
        ms_by_order.setdefault(m["order_id"], []).append(m)
    for p in data["payments"]:
        pay_by_order.setdefault(p["order_id"], []).append(p)

    orders = []
    for o in data["orders"]:
        co = compute_order(o, ms_by_order.get(o["id"], []), pay_by_order.get(o["id"], []), today)
        c = customers[o["customer_id"]]
        co["customer_name"] = c["name"]
        co["city"] = c["city"]
        orders.append(co)

    cust_out = []
    for c in data["customers"]:
        mine = [o for o in orders if o["customer_id"] == c["id"]]
        lateness = [d for o in mine for d in o["_lateness"]]
        worst = max(mine, key=lambda o: (o["overdue"], o["balance"]), default=None)
        cust_out.append({
            **c,
            "orders": len(mine),
            "outstanding": round(sum(o["balance"] for o in mine), 2),
            "overdue": round(sum(o["overdue"] for o in mine), 2),
            "days_overdue": max((o["days_overdue"] for o in mine), default=0),
            "habit": habit(lateness),
            "avg_days_late": round(sum(lateness) / len(lateness)) if lateness else None,
            "remind_order_id": worst["id"] if worst and worst["balance"] > EPS else None,
        })
    cust_out.sort(key=lambda c: (-c["overdue"], -c["outstanding"]))

    buckets = {"1-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    for o in orders:
        for days, amt in o["_overdue_parts"]:
            key = "1-30" if days <= 30 else "31-60" if days <= 60 else "61-90" if days <= 90 else "90+"
            buckets[key] += amt

    week_end = today + timedelta(days=DUE_SOON_DAYS)
    due_week = sum(
        m["unpaid"] for o in orders for m in o["milestones"]
        if m["status"] == "upcoming" and today <= _d(m["due_date"]) <= week_end
    )

    for o in orders:
        o.pop("_lateness")
        o.pop("_overdue_parts")

    return {
        "today": today.isoformat(),
        "totals": {
            "outstanding": round(sum(o["balance"] for o in orders), 2),
            "overdue": round(sum(o["overdue"] for o in orders), 2),
            "due_this_week": round(due_week, 2),
            "customers_overdue": sum(1 for c in cust_out if c["overdue"] > EPS),
        },
        "ageing": {k: round(v, 2) for k, v in buckets.items()},
        "customers": cust_out,
        "orders": orders,
    }
