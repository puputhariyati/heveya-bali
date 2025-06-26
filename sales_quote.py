import sqlite3
import pandas as pd

from flask import Flask, render_template, jsonify, request


def render_sales_quote():
    conn = sqlite3.connect("main.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sales_quotes ORDER BY id DESC")
    quotes = cursor.fetchall()

    conn.close()
    return render_template("sales_quote.html", quotes=quotes)

def render_create_quote():
    df = pd.read_csv("static/data/products_std.csv")

    # Make sure image_url has no extra spaces
    df['image_url'] = df['image_url'].astype(str).str.strip()

    product_list = df.to_dict(orient='records')
    return render_template("create_quote.html", product_list=product_list, quote=None)

# def render_save_quote():
#     data = request.get_json()
#     conn = sqlite3.connect('main.db')
#     cursor = conn.cursor()
#
#     if data.get('id'):
#         # UPDATE mode
#         cursor.execute('''
#             UPDATE sales_quotes
#             SET date=?, customer=?, phone=?, full_amount=?, discount=?, avg_disc=?, grand_total=?, margin=?, status=?, ETD=?
#             WHERE id=?
#         ''', (
#             data['date'],
#             data['customer'],
#             data['phone'],
#             data['full_amount'],
#             data['discount'],
#             0,
#             data['grand_total'],
#             data['margin'],
#             data['status'],
#             data['ETD'],
#             data['id']
#         ))
#     else:
#         # INSERT mode
#         cursor.execute('''
#             INSERT INTO sales_quotes (date, customer, phone, full_amount, discount, avg_disc, grand_total, margin, status, ETD)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             data['date'],
#             data['customer'],
#             data['phone'],
#             data['full_amount'],
#             data['discount'],
#             0,
#             data['grand_total'],
#             data['margin'],
#             data['status'],
#             data['ETD']
#         ))
#
#     conn.commit()
#     conn.close()
#     return jsonify({"status": "success"})

def render_save_quote(data):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()

    # Extract values from incoming data
    discount = data['discount']
    full_amount = data['full_amount']
    avg_disc = (discount / full_amount) * 100 if full_amount else 0

    # Insert sales quote header
    cursor.execute('''
        INSERT INTO sales_quotes (
            date, customer, phone, full_amount, discount, avg_disc,
            grand_total, margin, status, ETD
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['date'],
        data['customer'],
        data['phone'],
        full_amount,
        discount,
        avg_disc,
        data['grand_total'],
        data['margin'],
        data['status'],
        data['ETD']
    ))
    quote_id = cursor.lastrowid  # ✅ Move this inside the function

    # Insert each item
    for item in data['items']:
        cursor.execute('''
            INSERT INTO sales_quote_items (
                quote_id, description, qty, unit, unit_price, discount,
                discounted_price, amount, notes, full_amount, unit_cost,
                total_cost, margin
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            quote_id,
            item['description'],
            item['qty'],
            item['unit'],
            item['unit_price'],
            item['discount'],
            item['discounted_price'],
            item['amount'],
            item['notes'],
            item['full_amount'],
            item['unit_cost'],
            item['total_cost'],
            item['margin']
        ))

    conn.commit()
    conn.close()
    return {'status': 'success'}

