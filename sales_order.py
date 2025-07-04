import os
import sqlite3

from flask import Flask, render_template, redirect, flash, json, request, jsonify
from datetime import datetime

from pathlib import Path
app = Flask(__name__)
BASE_DIR = Path(__file__).parent

DATABASE = BASE_DIR / "main.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def render_sales_order():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all sales orders
    cursor.execute("SELECT * FROM sales_order ORDER BY transaction_date DESC")
    orders = cursor.fetchall()

    results = []

    for order in orders:
        tx_no = order["transaction_no"]
        # Fetch details to determine status
        cursor.execute("SELECT delivered, remain_qty FROM sales_order_detail WHERE transaction_no = ?", (tx_no,))
        details = cursor.fetchall()

        # Default status logic
        if not details:
            status = "closed"
        else:
            all_remain_zero = all(d["remain_qty"] == 0 for d in details)
            any_delivered_gt_zero = any(d["delivered"] > 0 for d in details)

            if all_remain_zero:
                status = "closed"
            elif any_delivered_gt_zero:
                status = "partially sent"
            else:
                status = "open"

        # Merge status into order
        order_dict = dict(order)
        order_dict["status"] = status
        results.append(order_dict)

    # ✅ Sort by newest date using datetime.strptime
    results.sort(
        key=lambda x: datetime.strptime(x["transaction_date"], "%d/%m/%Y"),
        reverse=True
    )

    conn.commit()
    conn.close()
    return render_template("sales_order.html", orders=results)


def update_single_etd():
    data = request.get_json()
    transaction_no = data.get("transaction_no")
    etd = data.get("etd")

    if not transaction_no or not etd:
        return jsonify({"success": False, "message": "Missing transaction number or ETD"})

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Make sure ETD is stored as text
    cursor.execute("""
        UPDATE sales_order 
        SET etd = ?
        WHERE transaction_no = ?
    """, (etd, transaction_no))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/sales_order/bulk_update_status", methods=["POST"])
def bulk_update_status():
    data = request.get_json()
    transaction_nos = data.get("transaction_nos", [])
    status = data.get("status")

    if not transaction_nos or status not in ["closed"]:
        return jsonify({"success": False, "message": "Invalid data"})

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for tx_no in transaction_nos:
        if status == "closed":
            # Mark as fully delivered → remain_qty = 0
            cursor.execute("""
                UPDATE sales_order_detail
                SET remain_qty = 0,
                    delivered = qty
                WHERE transaction_no = ?
            """, (tx_no,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


def bulk_update_etd():
    data = request.get_json()
    transaction_nos = data.get("transaction_nos", [])
    etd = data.get("etd")

    if not transaction_nos or not etd:
        return jsonify({"success": False, "message": "Missing data"})

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for tx_no in transaction_nos:
        cursor.execute("UPDATE sales_order SET etd = ? WHERE transaction_no = ?", (etd, tx_no))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

# Refresh Invoices Button
def upsert_sales_order(conn, order):
    query = """
    INSERT INTO sales_order (
        transaction_no, transaction_date, customer, balance_due, total, status, etd
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(transaction_no) DO UPDATE SET
        balance_due = excluded.balance_due,
        status      = excluded.status,
        etd         = excluded.etd;
    """
    conn.execute(query, (
        order['transaction_no'],
        order['transaction_date'],
        order['customer'],
        order['balance_due'],
        order['total'],
        order['status'],
        order['etd']
    ))
    conn.commit()
