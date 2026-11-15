"""SQLite storage for customers, orders, payment milestones, payments and the contact log."""
import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "bakaya.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    contact_person TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    city TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    machine TEXT NOT NULL,
    order_date TEXT NOT NULL,
    total REAL NOT NULL,
    notes TEXT DEFAULT ''
);
-- A payment plan: e.g. 30% advance, 60% before dispatch, 10% after installation
CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    amount REAL NOT NULL,
    due_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    mode TEXT DEFAULT '',
    note TEXT DEFAULT ''
);
-- The contact log: reminders sent and promises to pay
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    date TEXT NOT NULL,                 -- YYYY-MM-DD, the day of the contact
    kind TEXT NOT NULL CHECK (kind IN ('reminder', 'promise')),
    language TEXT DEFAULT '',           -- reminders: english | hinglish | hindi | punjabi
    promised_amount REAL,               -- promises only
    promised_date TEXT,                 -- promises only, YYYY-MM-DD
    note TEXT DEFAULT ''
);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init():
    with connect() as conn:
        conn.executescript(SCHEMA)


def is_empty():
    with connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0


def wipe():
    with connect() as conn:
        conn.executescript(
            "DELETE FROM contacts; DELETE FROM payments; DELETE FROM milestones; DELETE FROM orders; DELETE FROM customers;"
        )


def load_all():
    """Return every table as lists of dicts (the dataset is small, so we load it whole)."""
    with connect() as conn:
        return {
            "customers": [dict(r) for r in conn.execute("SELECT * FROM customers ORDER BY name")],
            "orders": [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY order_date DESC, id DESC")],
            "milestones": [dict(r) for r in conn.execute("SELECT * FROM milestones ORDER BY due_date, id")],
            "payments": [dict(r) for r in conn.execute("SELECT * FROM payments ORDER BY date, id")],
            "contacts": [dict(r) for r in conn.execute("SELECT * FROM contacts ORDER BY date, id")],
        }


def add_customer(conn, name, contact_person="", phone="", city=""):
    cur = conn.execute(
        "INSERT INTO customers (name, contact_person, phone, city) VALUES (?, ?, ?, ?)",
        (name, contact_person, phone, city),
    )
    return cur.lastrowid


def add_order(conn, customer_id, machine, order_date, total, milestones, notes=""):
    cur = conn.execute(
        "INSERT INTO orders (customer_id, machine, order_date, total, notes) VALUES (?, ?, ?, ?, ?)",
        (customer_id, machine, order_date, total, notes),
    )
    order_id = cur.lastrowid
    for m in milestones:
        conn.execute(
            "INSERT INTO milestones (order_id, label, amount, due_date) VALUES (?, ?, ?, ?)",
            (order_id, m["label"], m["amount"], m["due_date"]),
        )
    return order_id


def add_payment(conn, order_id, date, amount, mode="", note=""):
    cur = conn.execute(
        "INSERT INTO payments (order_id, date, amount, mode, note) VALUES (?, ?, ?, ?, ?)",
        (order_id, date, amount, mode, note),
    )
    return cur.lastrowid


def add_contact(conn, customer_id, date, kind, order_id=None, language="", promised_amount=None,
                promised_date=None, note=""):
    """Log a reminder sent or a promise to pay. Returns the new row's id."""
    cur = conn.execute(
        "INSERT INTO contacts (customer_id, order_id, date, kind, language, promised_amount, promised_date, note)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (customer_id, order_id, date, kind, language, promised_amount, promised_date, note),
    )
    return cur.lastrowid


def delete_contact(conn, contact_id):
    """Delete one contact log entry. Returns True if a row was deleted."""
    return conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,)).rowcount > 0
