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

    conn.commit()
    conn.close()
    return render_template("sales_order.html", orders=results)

