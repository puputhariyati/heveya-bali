import csv
import os
import sqlite3
import sys
import pandas as pd
import json

from flask import Flask, request, jsonify, render_template, redirect, flash, json
from dotenv import load_dotenv
from sqlalchemy import column

from sales_order_detail import render_sales_order_detail, save_sales_order_detail

load_dotenv("key.env")  # Load environment variables from .env file

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env

DATABASE = "main.db"  # ✅ Now using main.db instead of stock.db

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# # Create only the new sales_order_detail table or any others you need
# def init_db():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     # Example: your new sales_order_detail table
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS sales_order_detail (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             transaction_no TEXT,
#             line INTEGER,
#             item TEXT,
#             qty INTEGER,
#             unit TEXT,
#             delivered INTEGER DEFAULT 0,
#             remain_qty INTEGER,
#             po_no TEXT,
#             warehouse_option TEXT,
#             delivery_date TEXT,
#             status TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()
# print("✅ sales_order_detail table created.")
#
#
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
# # Create sales_order table if it doesn't exist
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS sales_order (
#     transaction_no TEXT PRIMARY KEY,
#     transaction_date TEXT,
#     customer TEXT,
#     balance_due TEXT,
#     total TEXT,
#     status TEXT,
#     etd TEXT
# )
# """)
# conn.commit()
# conn.close()
# print("✅ sales_order table created.")


# conn = sqlite3.connect('main.db')
# cursor = conn.cursor()
#
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS sales_quotes (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     date TEXT,
#     customer TEXT,
#     phone TEXT,
#     full_amount REAL,
#     discount REAL,
#     avg_disc REAL,
#     grand_total REAL,
#     margin REAL,
#     status TEXT,
#     ETD TEXT
# )
# ''')
#
# conn.commit()
# conn.close()
# print("✅ Table 'sales_quotes' created.")

# # Update DB in sales_quotes table to add a quote_no column
# import sqlite3
#
# conn = sqlite3.connect('main.db')
# cursor = conn.cursor()
#
# cursor.execute('''
#     ALTER TABLE sales_quotes ADD COLUMN quote_no TEXT
# ''')
#
# conn.commit()
# conn.close()
# print("✅ Added quote_no column to sales_quotes table")

conn = sqlite3.connect('main.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS sales_quote_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER,
    description TEXT,
    qty REAL,
    unit TEXT,
    unit_price REAL,
    discount REAL,
    discounted_price REAL,
    amount REAL,
    notes TEXT,
    full_amount REAL,
    unit_cost REAL,
    total_cost REAL,
    margin REAL
)
''')
conn.commit()
conn.close()
print("✅ Table 'sales_quote_items' created.")

# # merge multiple json data to 1 table
# def insert_orders_from_json(json_path):
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#
#     conn = sqlite3.connect("main.db")
#     cursor = conn.cursor()
#     count = 0
#
#     for order in data:
#         cursor.execute("""
#             INSERT OR IGNORE INTO sales_order (
#                 transaction_no, transaction_date, customer,
#                 balance_due, total, status, etd
#             ) VALUES (?, ?, ?, ?, ?, ?, ?)
#         """, (
#             order.get("transaction_no"),
#             order.get("transaction_date"),
#             order.get("person", {}).get("display_name", ""),
#             order.get("remaining_currency_format", "-"),
#             order.get("original_amount_currency_format", "-"),
#             "open",  # default status
#             None
#         ))
#         if cursor.rowcount > 0:
#             count += 1
#
#     conn.commit()
#     conn.close()
#     print(f"✅ Imported {count} new records from {json_path} into sales_order table.")
#
# # 🔁 Add more files here
# insert_orders_from_json("static/data/sales_orders_open.json")
# insert_orders_from_json("static/data/sales_orders_closed_2024_190625.json")
# insert_orders_from_json("static/data/sales_orders_2025_06_19_to_25.json")



# # Load JSON sales_orders_open.json into main.db table sales_order_detail
# with open("static/data/sales_orders_open.json", "r", encoding="utf-8") as f:
#     orders = json.load(f)
# conn = sqlite3.connect("main.db")
# c = conn.cursor()
# count = 0
# for order in orders:
#     tx_no = order["transaction_no"]
#     lines = order.get("transaction_lines_attributes", [])
#     for i, line in enumerate(lines, start=1):
#         product_data = line.get("product", {})
#         item = product_data.get("name", "") if isinstance(product_data, dict) else str(product_data)
#         qty = int(line.get("quantity", 0))
#         unit_value = line.get("unit", "")
#         unit = unit_value["name"] if isinstance(unit_value, dict) else str(unit_value)
#         delivered = 0
#         remain_qty = qty
#         po_no = ""
#         warehouse_option = ""
#         delivery_date = ""
#         status = "prepared"
#         description = line.get("description", "")
#
#         # Check if already exists
#         c.execute("SELECT 1 FROM sales_order_detail WHERE transaction_no=? AND line=?", (tx_no, i))
#         if c.fetchone():
#             continue  # Skip if already in DB
#
#         # Insert into DB
#         c.execute("""
#             INSERT INTO sales_order_detail
#             (transaction_no, line, item, qty, unit, delivered, remain_qty,
#             po_no, warehouse_option, delivery_date, status, description)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             tx_no, i, item, qty, unit, delivered, remain_qty,
#             po_no, warehouse_option, delivery_date, status, description
#         ))
#         count += 1
#
# conn.commit()
# conn.close()
# print(f"✅ Inserted {count} missing sales_order_detail lines")

# def insert_sales_orders_detail_from_json(json_path):
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#
#     conn = sqlite3.connect("main.db")
#     cursor = conn.cursor()
#     order_count = 0
#     detail_count = 0
#
#     for order in data:
#         tx_no = order.get("transaction_no")
#         inserted = False
#
#         # Insert lines into sales_order_detail
#         lines = order.get("transaction_lines_attributes", [])
#         for i, line in enumerate(lines, start=1):
#             product_data = line.get("product", {})
#             item = product_data.get("name", "") if isinstance(product_data, dict) else str(product_data)
#             qty = int(line.get("quantity", 0))
#             unit_value = line.get("unit", "")
#             unit = unit_value["name"] if isinstance(unit_value, dict) else str(unit_value)
#             delivered = 0
#             remain_qty = qty
#             po_no = ""
#             warehouse_option = ""
#             delivery_date = ""
#             status = "open"
#             description = line.get("description", "")
#
#             # Check if this line already exists
#             cursor.execute("SELECT 1 FROM sales_order_detail WHERE transaction_no=? AND line=?", (tx_no, i))
#             if cursor.fetchone():
#                 continue  # already exists
#
#             cursor.execute("""
#                 INSERT INTO sales_order_detail (
#                     transaction_no, line, item, qty, unit,
#                     delivered, remain_qty, po_no,
#                     warehouse_option, delivery_date, status, description
#                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             """, (
#                 tx_no, i, item, qty, unit,
#                 delivered, remain_qty, po_no,
#                 warehouse_option, delivery_date, status, description
#             ))
#             detail_count += 1
#
#     conn.commit()
#     conn.close()
#     print(f"✅ Imported {order_count} sales orders and {detail_count} detail lines from {json_path}.")
#
# insert_sales_orders_detail_from_json("static/data/sales_orders_open.json")
# insert_sales_orders_detail_from_json("static/data/sales_orders_closed_2024_190625.json")
# insert_sales_orders_detail_from_json("static/data/sales_orders_2025_06_19_to_25.json")
