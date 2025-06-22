import os
import sqlite3

from flask import Flask, render_template, redirect, flash, json
from dotenv import load_dotenv


load_dotenv("key.env")  # Load environment variables from .env file

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env

DATABASE = "main.db"  # ✅ Now using main.db instead of stock.db

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def render_sales_order():
    conn = sqlite3.connect("main.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all sales orders
    cursor.execute("SELECT * FROM sales_order")
    orders = cursor.fetchall()

    updated_orders = []

    for order in orders:
        tx_no = order["transaction_no"]
        # Fetch details to determine status
        cursor.execute("SELECT delivered, remain_qty FROM sales_order_detail WHERE transaction_no = ?", (tx_no,))
        details = cursor.fetchall()

        if not details:
            new_status = "open"
        else:
            all_remain_zero = all(row["remain_qty"] == 0 for row in details)
            any_delivered_gt_zero = any(row["delivered"] > 0 for row in details)

            if all_remain_zero:
                new_status = "open"
            elif any_delivered_gt_zero:
                new_status = "partially sent"
            else:
                new_status = "prepared"

        # Update DB if status changed
        if order["status"] != new_status:
            cursor.execute("UPDATE sales_order SET status = ? WHERE transaction_no = ?", (new_status, tx_no))

        updated_orders.append({**dict(order), "status": new_status})

    conn.commit()
    conn.close()

    return render_template("sales_order.html", orders=updated_orders)

