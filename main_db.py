import csv
import os
import sqlite3
import sys
import pandas as pd
import json

from flask import Flask, request, jsonify, render_template, redirect, flash, json
from dotenv import load_dotenv
from sqlalchemy import column
from pathlib import Path

from sales_invoices_detail import render_sales_invoices_detail, save_sales_invoices_detail

load_dotenv("key.env")  # Load environment variables from .env file
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env

DATABASE = Path(__file__).parent / "main.db"

# def get_db_connection():
#     conn = sqlite3.connect(DATABASE)
#     conn.row_factory = sqlite3.Row
#     return conn

# Connect to your database
conn = sqlite3.connect("main.db")
cursor = conn.cursor()

# # ✅ merge multiple json data to 1 table
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
#            INSERT OR IGNORE INTO sales_invoices (
#             transaction_no, transaction_date, customer,
#             balance_due, total, status, etd, po_no, tags, payment
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#            """, (
#                order.get("transaction_no"),
#                order.get("transaction_date"),
#                order.get("person", {}).get("display_name", ""),
#                order.get("remaining_currency_format", "-"),
#                order.get("original_amount_currency_format", "-"),
#                "closed",  # default status
#                None,  # etd (optional)
#                order.get("po_number", ""),
#                order.get("tags_string", ""),
#                order["payments"][0]["payment_method_name"] if order.get("payments") else ""
#            ))
#
#         if cursor.rowcount > 0:
#             count += 1
#
#     conn.commit()
#     conn.close()
#     print(f"Imported {count} new records from {json_path} into sales_invoices table.")
#
# # 🔁 Add more files here
# insert_orders_from_json("static/data/sales_invoices_2022_0106.json")
# insert_orders_from_json("static/data/sales_invoices_2022_0712.json")
# insert_orders_from_json("static/data/sales_invoices_2023_0106.json")
# insert_orders_from_json("static/data/sales_invoices_2023_0712.json")
# insert_orders_from_json("static/data/sales_invoices_2024_0106.json")
# insert_orders_from_json("static/data/sales_invoices_2024_0712.json")
# insert_orders_from_json("static/data/sales_invoices_2025_0103.json")
# insert_orders_from_json("static/data/sales_invoices_2025_0406.json")
#
#
# # ✅ merge multiple json data to 1 table sales_invoices_detail
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
#         # Insert lines into sales_invoices_detail
#         lines = order.get("transaction_lines_attributes", [])
#         for i, line in enumerate(lines, start=1):
#             product_data = line.get("product", {})
#             item = product_data.get("name", "") if isinstance(product_data, dict) else str(product_data)
#             qty = int(line.get("quantity", 0))
#             unit_value = line.get("unit", "")
#             unit = unit_value["name"] if isinstance(unit_value, dict) else str(unit_value)
#             delivered = qty
#             remain_qty = 0
#             po_no = ""
#             warehouse_option = ""
#             delivery_date = ""
#             status = "closed"
#             description = line.get("description", "")
#
#             # Check if this line already exists
#             cursor.execute("SELECT 1 FROM sales_invoices_detail WHERE transaction_no=? AND line=?", (tx_no, i))
#             if cursor.fetchone():
#                 continue  # already exists
#
#             cursor.execute("""
#                 INSERT INTO sales_invoices_detail (
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
#     print(f" Imported {order_count} sales invoices detail and {detail_count} detail lines from {json_path}.")
#
# # # 🔁 Add more files here
# insert_sales_orders_detail_from_json("static/data/sales_invoices_2022_0106.json")
# insert_sales_orders_detail_from_json("static/data/sales_invoices_2022_0712.json")
# insert_sales_orders_detail_from_json("static/data/sales_invoices_2023_0106.json")
# insert_sales_orders_detail_from_json("static/data/sales_invoices_2023_0712.json")
# insert_sales_orders_detail_from_json("static/data/sales_invoices_2024_0106.json")
# insert_sales_orders_detail_from_json("static/data/sales_invoices_2024_0712.json")
# insert_sales_orders_detail_from_json("static/data/sales_invoices_2025_0103.json")
# insert_sales_orders_detail_from_json("static/data/sales_invoices_2025_0406.json")

# # ✅ create a composite unique constraint on (transaction_no, line) for the sales_invoices_detail
# db_path = "main.db"  # Make sure this is the one your app uses
# def ensure_tx_line_index():
#     conn = sqlite3.connect(db_path)
#     cur = conn.cursor()
#     cur.execute("""
#         CREATE UNIQUE INDEX IF NOT EXISTS idx_tx_line
#         ON sales_invoices_detail (transaction_no, line)
#     """)
#     conn.commit()
#     conn.close()
#     print(" Composite UNIQUE index on (transaction_no, line) ensured.")
# ensure_tx_line_index()

# ✅ Function to Only Update unit_sold_price column
def update_unit_sold_price_from_json(json_path):
    import sqlite3, json
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    updated_count = 0

    for invoice in data:
        tx_no = invoice.get("transaction_no")
        lines = invoice.get("transaction_lines_attributes", [])
        if not lines:
            continue

        try:
            total_discount = float(invoice.get("discount_price", 0))
            num_lines = len(lines)
            per_line_discount = (total_discount * 1.11) / num_lines if num_lines > 0 else 0
        except Exception as e:
            print(f"❌ Error parsing discount for {tx_no}: {e}")
            continue

        for i, line in enumerate(lines, start=1):
            try:
                amount = float(line.get("amount", 0))
                unit_sold_price = round((amount * 1.11) - per_line_discount, 2)
            except Exception as e:
                print(f"❌ Error calculating unit_sold_price for {tx_no} line {i}: {e}")
                continue

            cursor.execute("""
                UPDATE sales_invoices_detail
                SET unit_sold_price = ?
                WHERE transaction_no = ? AND line = ?
            """, (unit_sold_price, tx_no, i))
            updated_count += 1

    conn.commit()
    conn.close()
    print(f"✅ Updated unit_sold_price for {updated_count} lines from {json_path}.")

# 🔁 Add more files here
update_unit_sold_price_from_json("static/data/sales_invoices_2025_0103.json")






# # ✅debug_table_schema
# def debug_table_schema():
#     conn = sqlite3.connect(DATABASE)
#     cursor = conn.cursor()
#     cursor.execute("PRAGMA table_info(sales_invoices_detail)")
#     for row in cursor.fetchall():
#         print(row)
#     conn.close()
# debug_table_schema()



# # Insert multiple Sales Orders csv to sales_order table
# # Paths to your CSV files
# csv_files = [
#     'static/data/sales_orders_jun2025.csv',
#     'static/data/specific_sales_orders.csv'
# ]
#
# # Connect to the SQLite database
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
#
# inserted = 0
# skipped = 0
#
# for file in csv_files:
#     df = pd.read_csv(file)
#
#     # Normalize column names
#     df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
#
#     # Group by transaction_no
#     grouped = df.groupby("transaction_no")
#
#     for transaction_no, group in grouped:
#         cursor.execute("SELECT 1 FROM sales_order WHERE transaction_no = ?", (transaction_no,))
#         if cursor.fetchone():
#             skipped += 1
#             continue  # already exists
#
#         # Get order-level data from the first row
#         first_row = group.iloc[0]
#         transaction_date = first_row.get("transaction_date", "")
#         customer = first_row.get("customer", "")
#         total = first_row.get("total", "")
#
#         # Insert into sales_order
#         cursor.execute("""
#             INSERT INTO sales_order (transaction_no, transaction_date, customer, total)
#             VALUES (?, ?, ?, ?)
#         """, (transaction_no, transaction_date, customer, total))
#
#         # Insert each item into sales_order_detail
#         for i, row in enumerate(group.itertuples(), start=1):
#             product_name = getattr(row, "product_name", "")
#             product_code = getattr(row, "product_code", "")
#             quantity = int(float(getattr(row, "quantity", 0)))
#
#             cursor.execute("""
#                 INSERT INTO sales_order_detail (
#                     transaction_no, line, item, qty, unit, delivered, remain_qty, po_no, status
#                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#             """, (
#                 transaction_no, i, product_name, quantity, "pcs", 0, quantity, "", "open"
#             ))
#
#         inserted += 1
#
# conn.commit()
# conn.close()
#
# print(f"✅ Insert complete! Inserted: {inserted}, Skipped (already exists): {skipped}")


# # One-time script to update all totals in sales_order table:
# def format_to_rupiah(value):
#     try:
#         value = int(float(value))
#         return "Rp. {:,}".format(value).replace(",", ".")
#     except:
#         return value  # leave as is if already formatted or invalid
#
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
#
# cursor.execute("SELECT transaction_no, total FROM sales_order")
# rows = cursor.fetchall()
#
# updated = 0
#
# for tx_no, total in rows:
#     if isinstance(total, str) and total.startswith("Rp."):
#         continue  # already formatted
#
#     formatted = format_to_rupiah(total)
#     cursor.execute("UPDATE sales_order SET total = ? WHERE transaction_no = ?", (formatted, tx_no))
#     updated += 1
#
# conn.commit()
# conn.close()
#
# print(f"✅ Updated {updated} totals to currency format.")

# Add Column into existing table
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
# cursor.execute("ALTER TABLE sales_order_detail ADD COLUMN description TEXT")
# conn.commit()
# conn.close()

# ✅ Step-by-Step: Update Only New Columns
# for inv in fetched_invoices:
#     try:
#         tx_no = inv["transaction_no"]
#
#         po_no = inv.get("po_number", "")
#         tags = ", ".join(tag["name"] for tag in inv.get("tags", [])) if inv.get("tags") else ""
#         payment = inv.get("payment_method", {}).get("name", "")
#
#         # Only update existing records
#         cursor.execute("""
#             UPDATE sales_invoices
#             SET po_no = ?, tags = ?, payment = ?
#             WHERE transaction_no = ?
#         """, (po_no, tags, payment, tx_no))
#
#         if cursor.rowcount == 0:
#             print(f"⚠️ Invoice {tx_no} not found — skipping")
#
#     except Exception as e:
#         print(f"⚠️ Failed to update invoice {inv.get('transaction_no', '?')}: {e}")


#
# # ✅ Clear the table first
# cursor.execute("DELETE FROM sales_invoices_detail")
# deleted_rows = cursor.rowcount
# print(f"🗑️ Deleted {deleted_rows} existing rows")
# conn.commit()
# conn.close()
#
# #✅ Delete table from the stock table
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
# cursor.execute("DROP TABLE IF EXISTS sales_quote;")
# # Commit changes and close connection
# conn.commit()
# conn.close()
#
# # # Reset auto-increment ID (optional)
# # cursor.execute("DELETE FROM sqlite_sequence WHERE name='inventory';")
# print("Stock database has been cleared.")

# #✅ Delete data from date
# cursor.execute("""
#     DELETE FROM sales_invoices
#     WHERE substr(transaction_date, 7, 4) || '-' ||
#           substr(transaction_date, 4, 2) || '-' ||
#           substr(transaction_date, 1, 2)
#           >= '2025-07-01'
# """)
# deleted_rows = cursor.rowcount
# conn.commit()
# conn.close()
# print(f"🗑️ Deleted {deleted_rows} existing rows")

# # ✅ Delete values in a column: Set all values to NULL
# cursor.execute("UPDATE sales_invoices_detail SET unit_sold_price = NULL;")
# conn.commit()
# conn.close()
# print(" All values in 'unit_sold_price' have been cleared (set to NULL).")



#
# #✅ To see what tables list in my main.db
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
# import sqlite3
# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
# tables = cursor.fetchall()
# for table in tables:
#     table_name = table[0]
#     try:
#         cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
#         row_count = cursor.fetchone()[0]
#         print(f"{table_name}: {row_count}")
#     except Exception as e:
#         print(f"Could not read {table_name}: {e}")
# conn.close()


#✅ Export your SQLite tables to .csv
import pandas as pd
# Load sales_order table
df = pd.read_sql_query("SELECT * FROM sales_invoices_detail", conn)
# Save to CSV
df.to_csv("db_sales_invoices_detail.csv", index=False)
conn.close()
print("db_sales_invoices_detail.csv")


# # Run a quick count test
# cursor.execute("SELECT COUNT(*) FROM sales_order_detail")
# count = cursor.fetchone()[0]
# print("Total rows in sales_order_detail:", count)


# # RENAME TABLE
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
#
# # Rename table
# cursor.execute("ALTER TABLE sales_order_detail RENAME TO sales_invoices_detail")
#
# conn.commit()
# conn.close()
# print("✅ Table renamed to sales_invoices.")

