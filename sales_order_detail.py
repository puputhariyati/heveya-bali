import json
import sqlite3
import pandas as pd
import os

from flask import render_template, redirect, request, flash


def render_sales_order_detail(transaction_no):
    # 1. Load original order from JSON (still useful for full lines)
    with open("static/data/sales_orders_May2025.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    order = next((o for o in data if o["transaction_no"] == transaction_no), None)
    if not order:
        return f"Sales order {transaction_no} not found", 404

    # 2. Fetch stored edits from the DB
    conn = sqlite3.connect("main.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales_order_detail WHERE transaction_no = ?", (transaction_no,))
    rows = cursor.fetchall()
    conn.close()

    # 3. Merge the data: apply DB edits (if any) to the lines
    line_updates = {row["line"]: dict(row) for row in rows}
    for i, line in enumerate(order.get("transaction_lines_attributes", []), start=1):
        if i in line_updates:
            line["db_update"] = line_updates[i]  # Inject updates into line

    return render_template("sales_order_detail.html", order=order)


def save_sales_order_detail(transaction_no):
    conn = sqlite3.connect("main.db")
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

        # Load products CSV for stock update
        products_csv_path = "static/data/products_std.csv"
        products_df = pd.read_csv(products_csv_path)
        stock_updated = False

        for i in range(len(item_list)):
            delivered = int(float(delivered_list[i])) if delivered_list[i] else 0
            qty = int(float(qty_list[i])) if qty_list[i] else 0
            remain = int(float(remain_qty_list[i])) if remain_qty_list[i] else max(qty - delivered, 0)
            item_name = item_list[i]
            warehouse_option = warehouse_option_list[i]

            # Get previous delivered value to calculate the difference
            c.execute("SELECT delivered FROM sales_order_detail WHERE transaction_no=? AND line=?", (transaction_no, i + 1))
            prev_record = c.fetchone()
            prev_delivered = prev_record[0] if prev_record else 0
            delivered_diff = delivered - prev_delivered

            c.execute("SELECT id FROM sales_order_detail WHERE transaction_no=? AND line=?", (transaction_no, i + 1))
            exists = c.fetchone()

            if exists:
                c.execute("""
                    UPDATE sales_order_detail
                    SET delivered=?, remain_qty=?, po_no=?, delivery_date=?, 
                        warehouse_option=?, status=?, description=?
                    WHERE transaction_no=? AND line=?
                """, (
                    delivered, remain, po_no_list[i], delivery_date_list[i],
                    warehouse_option_list[i], status_list[i], description_list[i],
                    transaction_no, i + 1
                ))
            else:
                c.execute("""
                    INSERT INTO sales_order_detail
                    (transaction_no, line, item, qty, unit, delivered, remain_qty,
                    po_no, warehouse_option, delivery_date, status, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_no, i + 1, item_name, qty, unit_list[i],
                    delivered, remain, po_no_list[i],
                    warehouse_option_list[i], delivery_date_list[i], status_list[i], description_list[i]
                ))

            # Update stock quantity if delivered quantity has changed
            if delivered_diff > 0:
                # Find the product in the CSV by name
                product_idx = products_df[products_df['name'] == item_name].index

                if len(product_idx) > 0:
                    idx = product_idx[0]

                    # Update showroom or warehouse quantity based on warehouse option
                    if warehouse_option == 'showroom':
                        current_qty = products_df.at[idx, 'showroom_qty']
                        if pd.notna(current_qty) and current_qty != '':
                            current_qty = float(current_qty)
                            new_qty = max(current_qty - delivered_diff, 0)
                            products_df.at[idx, 'showroom_qty'] = new_qty
                            stock_updated = True
                    elif warehouse_option == 'warehouse':
                        current_qty = products_df.at[idx, 'warehouse_qty']
                        if pd.notna(current_qty) and current_qty != '':
                            current_qty = float(current_qty)
                            new_qty = max(current_qty - delivered_diff, 0)
                            products_df.at[idx, 'warehouse_qty'] = new_qty
                            stock_updated = True

        # Save updated stock quantities to CSV if any changes were made
        if stock_updated:
            products_df.to_csv(products_csv_path, index=False)

        conn.commit()
        flash("✓ Saved successfully!", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Save failed: {str(e)}", "error")

    finally:
        conn.close()

    return redirect(f"/sales_order/{transaction_no}")
