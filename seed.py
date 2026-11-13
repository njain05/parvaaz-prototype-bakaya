"""Fictional demo data for a textile-machinery maker. Dates are relative to today,
so the demo always shows a realistic mix of overdue, due-soon and paid orders.

Run directly to reset the demo data:  python seed.py
"""
from datetime import date, timedelta

import db


def _plan(total, order_day, dispatch_day, install_after=30, split=(0.3, 0.6, 0.1)):
    """Standard machinery payment plan: advance / before dispatch / after installation."""
    adv, disp = round(total * split[0]), round(total * split[1])
    return [
        {"label": "Advance", "amount": adv, "due": order_day},
        {"label": "Before dispatch", "amount": disp, "due": dispatch_day},
        {"label": "After installation", "amount": total - adv - disp, "due": dispatch_day + install_after},
    ]


# (customer, [orders]); each order: machine, total, order day, milestones, payments [(day, amount, mode)]
# Day numbers are offsets from today: -30 means 30 days ago.
DEMO = [
    (("Sharma Knit Processors", "Rajesh Sharma", "98XXX-XX011", "Ludhiana"), [
        ("Raising Machine, 24 roller", 1850000, -120, _plan(1850000, -120, -60),
         [(-118, 555000, "NEFT"), (-55, 600000, "Cheque")]),
    ]),
    (("Gupta Woollen Mills", "Sanjay Gupta", "98XXX-XX012", "Amritsar"), [
        ("Shearing Machine", 980000, -90, _plan(980000, -90, -45),
         [(-90, 294000, "NEFT"), (-40, 588000, "NEFT")]),
    ]),
    (("Bansal Dyeing House", "Vikas Bansal", "98XXX-XX013", "Panipat"), [
        ("Brushing Machine", 650000, -200, _plan(650000, -200, -150),
         [(-200, 195000, "NEFT"), (-151, 390000, "NEFT"), (-118, 65000, "NEFT")]),
        ("Stenter, 8 chamber", 2400000, -40, _plan(2400000, -40, 10),
         [(-40, 720000, "RTGS")]),
    ]),
    (("Kaur Hosiery Works", "Harpreet Kaur", "98XXX-XX014", "Ludhiana"), [
        ("Tumble Dryer", 720000, -150, _plan(720000, -150, -100),
         [(-150, 216000, "Cheque"), (-70, 432000, "Cheque"), (-20, 30000, "Cash")]),
    ]),
    (("Malhotra Textiles", "Amit Malhotra", "98XXX-XX015", "Surat"), [
        ("Raising Machine, 36 roller", 1600000, -20, _plan(1600000, -20, 5),
         [(-18, 480000, "RTGS")]),
    ]),
    (("Tirupur Knit Finishers", "S. Kumar", "98XXX-XX016", "Tirupur"), [
        ("Compactor", 2100000, -210, _plan(2100000, -210, -150),
         [(-210, 630000, "RTGS"), (-148, 1260000, "RTGS")]),
        ("Fillet wire set (spares)", 85000, -35,
         [{"label": "Full payment", "amount": 85000, "due": -5}], []),
    ]),
    (("Arora Fabrics", "Manoj Arora", "98XXX-XX017", "Ludhiana"), [
        ("Brushing Machine", 540000, -60, _plan(540000, -60, -25),
         [(-60, 162000, "Cash"), (-10, 100000, "Cheque")]),
    ]),
    (("Bhilwara Suitings", "Ramesh Jain", "98XXX-XX018", "Bhilwara"), [
        ("Shearing Machine", 1050000, -100, _plan(1050000, -100, -60),
         [(-100, 315000, "NEFT"), (-61, 630000, "NEFT"), (-28, 105000, "NEFT")]),
        ("Raising rollers (spares)", 120000, -10,
         [{"label": "Full payment", "amount": 120000, "due": 20}], []),
    ]),
    (("Shree Ganesh Processors", "Deepak Verma", "98XXX-XX019", "Ludhiana"), [
        ("Raising Machine, 24 roller", 1780000, -75, _plan(1780000, -75, -20),
         [(-70, 300000, "Cheque"), (-50, 234000, "Cheque")]),
    ]),
]


def seed(today=None):
    today = today or date.today()

    def day(offset):
        return (today + timedelta(days=offset)).isoformat()

    db.init()
    db.wipe()
    with db.connect() as conn:
        for (name, person, phone, city), orders in DEMO:
            cid = db.add_customer(conn, name, person, phone, city)
            for machine, total, order_day, plan, pays in orders:
                milestones = [{"label": m["label"], "amount": m["amount"], "due_date": day(m["due"])} for m in plan]
                oid = db.add_order(conn, cid, machine, day(order_day), total, milestones)
                for pay_day, amount, mode in pays:
                    db.add_payment(conn, oid, day(pay_day), amount, mode)


if __name__ == "__main__":
    seed()
    print("Demo data loaded into", db.DB_PATH)
