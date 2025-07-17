import json
import sqlite3
import pandas as pd
import os

from flask import render_template, redirect, request, flash, Flask

# from dotenv import load_dotenv
from pathlib import Path

# load_dotenv(Path(__file__).parent / "key.env")
app = Flask(__name__)

# app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "main.db"
products_csv_path = BASE_DIR / "static" / "data" / "products_std.csv"


def render_sales_invoices_detail(transaction_no):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch header
    cursor.execute("SELECT * FROM sales_invoices WHERE transaction_no = ?", (transaction_no,))
    order_row = cursor.fetchone()
    if not order_row:
        return f"Sales order {transaction_no} not found", 404
    order = dict(order_row)

    # Fetch details
    cursor.execute("SELECT * FROM sales_invoices_detail WHERE transaction_no = ?", (transaction_no,))
    detail_rows = cursor.fetchall()
    lines = [dict(row) for row in detail_rows]

    conn.close()

    return render_template("sales_invoices_detail.html", order=order, lines=lines)

# use parse mattress logic for stock update
def parse_mattress_name(name):
    try:
        if "Mattress" not in name:
            return None, None, None
        parts = name.replace("Heveya Natural Organic Latex Mattress", "").strip().split(" - ")
        category = "Heveya " + parts[0].strip()
        size_part = parts[1].split("(")[1].replace(")", "").replace("W", "").replace("L", "").replace("cm", "").strip()
        size = parts[1].split("(")[0].strip() + " " + size_part  # e.g., King 180x200
        firmness = parts[2].strip()
        return category, size, firmness
    except Exception as e:
        print("❌ Error parsing mattress name:", name, e)
        return None, None, None

def save_sales_invoices_detail(transaction_no):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    try:
        delivered_list = request.form.getlist('delivered')
        po_no_list = request.form.getlist('PO_no')
        delivery_date_list = request.form.getlist('delivery_date')
        warehouse_option_list = request.form.getlist('warehouse_option')
        status_list = request.form.getlist('status')
        item_list = request.form.getlist('item')
        qty_list = request.form.getlist('qty')
        unit_list = request.form.getlist('unit')
        description_list = request.form.getlist('description')
        remain_qty_list = request.form.getlist('remain_qty')

        # ✅ NEW: Get selected rows and bulk warehouse option from the form
        selected_rows = request.form.getlist('selected_rows')  # e.g., ["1", "3", "5"]
        bulk_warehouse_option = request.form.get('bulk_warehouse_option')

        # Convert selected row indices to int
        selected_indices = set(int(i) for i in selected_rows)

        products_df = pd.read_csv(products_csv_path)
        stock_updated = False

        for i in range(len(item_list)):
            qty = int(float(qty_list[i])) if qty_list[i] else 0

            # ✅ Apply bulk logic if this row was selected
            if i in selected_indices:
                delivered = qty  # Set delivered = qty
                warehouse_option = bulk_warehouse_option
            else:
                delivered = int(float(delivered_list[i])) if delivered_list[i] else 0
                warehouse_option = warehouse_option_list[i]

            remain = int(float(remain_qty_list[i])) if remain_qty_list[i] else max(qty - delivered, 0)
            item_name = item_list[i]

            # Get previous delivered value to calculate stock difference
            c.execute("SELECT delivered FROM sales_invoices_detail WHERE transaction_no=? AND line=?", (transaction_no, i + 1))
            prev_record = c.fetchone()
            prev_delivered = prev_record[0] if prev_record else 0
            delivered_diff = delivered - prev_delivered

            c.execute("SELECT id FROM sales_invoices_detail WHERE transaction_no=? AND line=?", (transaction_no, i + 1))
            exists = c.fetchone()

            if exists:
                c.execute("""
                    UPDATE sales_invoices_detail
                    SET delivered=?, remain_qty=?, po_no=?, delivery_date=?, 
                        warehouse_option=?, status=?, description=?
                    WHERE transaction_no=? AND line=?
                """, (
                    delivered, remain, po_no_list[i], delivery_date_list[i],
                    warehouse_option, status_list[i], description_list[i],
                    transaction_no, i + 1
                ))
            else:
                c.execute("""
                    INSERT INTO sales_invoices_detail
                    (transaction_no, line, item, qty, unit, delivered, remain_qty,
                    po_no, warehouse_option, delivery_date, status, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_no, i + 1, item_name, qty, unit_list[i],
                    delivered, remain, po_no_list[i],
                    warehouse_option, delivery_date_list[i], status_list[i], description_list[i]
                ))

            # ✅ Stock update (same as before, untouched)
            updated = False
            product_idx = products_df[products_df['name'] == item_name].index
            if len(product_idx) > 0:
                idx = product_idx[0]
                if warehouse_option == 'showroom':
                    current_qty = products_df.at[idx, 'showroom_qty']
                    if pd.notna(current_qty) and current_qty != '':
                        current_qty = float(current_qty)
                        new_qty = current_qty - delivered_diff
                        products_df.at[idx, 'showroom_qty'] = max(new_qty, 0) if delivered_diff > 0 else new_qty
                        stock_updated = True
                        updated = True
                elif warehouse_option == 'warehouse':
                    current_qty = products_df.at[idx, 'warehouse_qty']
                    if pd.notna(current_qty) and current_qty != '':
                        current_qty = float(current_qty)
                        new_qty = current_qty - delivered_diff
                        products_df.at[idx, 'warehouse_qty'] = max(new_qty, 0) if delivered_diff > 0 else new_qty
                        stock_updated = True
                        updated = True

            if not updated and "Mattress" in item_name:
                category, size, firmness = parse_mattress_name(item_name)
                if category and size and firmness:
                    mattress_idx = products_df[
                        (products_df['Category'] == category) &
                        (products_df['Subcategory'].str.contains(size)) &
                        (products_df['Firmness'] == firmness)
                    ].index
                    if len(mattress_idx) > 0:
                        idx = mattress_idx[0]
                        if warehouse_option == 'warehouse':
                            current_qty = float(products_df.at[idx, 'warehouse_qty'])
                            products_df.at[idx, 'warehouse_qty'] = max(current_qty - delivered_diff, 0)
                            stock_updated = True

        if stock_updated:
            products_df.to_csv(products_csv_path, index=False)

        conn.commit()
        flash("✓ Saved successfully!", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Save failed: {str(e)}", "error")

    finally:
        conn.close()

    return redirect(f"/sales_invoices/{transaction_no}")



