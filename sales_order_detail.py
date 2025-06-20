import json
import sqlite3

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

        for i in range(len(item_list)):
            delivered = int(delivered_list[i]) if delivered_list[i] else 0
            qty = int(qty_list[i]) if qty_list[i] else 0
            remain = max(qty - delivered, 0)

            c.execute("SELECT id FROM sales_order_detail WHERE transaction_no=? AND line=?", (transaction_no, i + 1))
            exists = c.fetchone()

            if exists:
                c.execute("""
                    UPDATE sales_order_detail
                    SET delivered=?, remain_qty=?, po_no=?, delivery_date=?, 
                        warehouse_option=?, status=?
                    WHERE transaction_no=? AND line=?
                """, (
                    delivered, remain, po_no_list[i], delivery_date_list[i],
                    warehouse_option_list[i], status_list[i],
                    transaction_no, i + 1
                ))
            else:
                c.execute("""
                    INSERT INTO sales_order_detail
                    (transaction_no, line, item, qty, unit, delivered, remain_qty,
                    po_no, warehouse_option, delivery_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_no, i + 1, item_list[i], qty, unit_list[i],
                    delivered, remain, po_no_list[i],
                    warehouse_option_list[i], delivery_date_list[i], status_list[i]
                ))

        conn.commit()
        flash("✓ Saved successfully!", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Save failed: {str(e)}", "error")

    finally:
        conn.close()

    return redirect(f"/sales_order/{transaction_no}")
