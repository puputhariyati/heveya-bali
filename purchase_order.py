import sqlite3
from flask import request, jsonify, render_template
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "main.db"


def load_purchase_orders():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM purchase_orders ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def render_purchase_order():
    orders = load_purchase_orders()
    return render_template("purchase_order.html", orders=orders)


def save_purchase_order():
    data = request.get_json()
    print("📦 Received PO:", data)

    transaction_no = data.get("transaction_no")
    vendor = data.get("vendor")
    date = data.get("transaction_date")
    eta = data.get("eta")
    status = data.get("status", "Open")
    items = data.get("items", [])

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Insert into purchase_orders table
    cursor.execute("""
        INSERT OR REPLACE INTO purchase_orders 
        (transaction_no, transaction_date, vendor, eta, status)
        VALUES (?, ?, ?, ?, ?)
    """, (transaction_no, date, vendor, eta, status))

    # Remove existing items first (if editing)
    cursor.execute("DELETE FROM purchase_order_detail WHERE transaction_no = ?", (transaction_no,))

    # Insert items
    for item in items:
        cursor.execute("""
            INSERT INTO purchase_order_detail 
            (transaction_no, product_code, description, qty, unit, unit_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            transaction_no,
            item.get("product_code", ""),
            item.get("description", ""),
            item.get("qty", 0),
            item.get("unit", ""),
            item.get("unit_cost", 0.0)
        ))

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


def update_po_eta():
    data = request.get_json()
    transaction_no = data.get("transaction_no")
    new_eta = data.get("eta")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE purchase_orders SET eta = ? WHERE transaction_no = ?", (new_eta, transaction_no))
    conn.commit()
    conn.close()

    return jsonify({"status": "updated"})
