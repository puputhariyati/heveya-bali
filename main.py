import csv
import os
import sqlite3
import sys
import pandas as pd
import json

from flask import Flask, request, jsonify, render_template, redirect, flash, json
from dotenv import load_dotenv

from sales_order import render_sales_order
from sales_order_detail import render_sales_order_detail, save_sales_order_detail

load_dotenv("key.env")  # Load environment variables from .env file

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env

DATABASE = "main.db"  # ✅ Now using main.db instead of stock.db

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Create only the new sales_order_detail table or any others you need
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Example: your new sales_order_detail table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_order_detail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_no TEXT,
            line INTEGER,
            item TEXT,
            qty INTEGER,
            unit TEXT,
            delivered INTEGER DEFAULT 0,
            remain_qty INTEGER,
            po_no TEXT,
            warehouse_option TEXT,
            delivery_date TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()



#Dashboard page
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/crm')
def crm():
    return render_template('crm.html')

@app.route('/api/crm', methods=['GET', 'POST'])
def crm_data():
    if request.method == 'POST':
        data = request.get_json()
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO leads (customer, product, status, sales_person, amount, date, source, mobile, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['customer'],
                data['product'],
                data['status'],
                data['sales_person'],
                float(data['amount']),
                data['date'],
                data['source'],
                data['mobile'],
                data['email'] if data['email'] else None
            ))
            conn.commit()
            conn.close()
            return jsonify({"success": True}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # For GET
    conn = get_db_connection()
    leads = conn.execute('SELECT * FROM leads').fetchall()
    conn.close()
    return jsonify([dict(lead) for lead in leads])


@app.route('/api/summary')
def summary():
    conn = get_db_connection()
    leads = conn.execute('SELECT status, amount FROM leads').fetchall()
    conn.close()

    total_leads = len(leads)
    success = sum(1 for lead in leads if lead['status'].lower() == 'success')
    fail = sum(1 for lead in leads if lead['status'].lower() == 'fail')
    follow_up = sum(1 for lead in leads if 'follow' in lead['status'].lower())
    total_amount = sum(float(lead['amount']) for lead in leads)

    return jsonify({
        'total_leads': total_leads,
        'success': success,
        'fail': fail,
        'follow_up': follow_up,
        'total_amount': total_amount
    })

@app.route("/sync_sales", methods=["GET"])
def sync_sales():
    data = get_sales_orders()
    if not data or "sales_orders" not in data:
        return jsonify([])

    items = []
    for order in data["sales_orders"]:
        for line in order.get("transaction_lines_attributes", []):
            product = line.get("product")
            if product:
                items.append({
                    "name": product.get("name"),
                    "quantity": line.get("quantity")
                })
    return jsonify(items)

import pandas as pd

@app.route("/bedsheets")
def bedsheets():
    df = pd.read_csv("static/data/products_std.csv")
    # Filter only pillow products
    pillow_df = df[df['Category'].str.contains("pillow", case=False, na=False)].copy()
    # Rename quantity columns for easier handling
    pillow_df.rename(columns={
        'Showroom_Qty': 'showroom_qty',
        'Warehouse_Qty': 'warehouse_qty'
    }, inplace=True)
    # Compute required to showroom (req_sh)
    pillow_df['req_sh'] = pillow_df.apply(
        lambda row: 6 - row['showroom_qty'] if row['showroom_qty'] < 6 else 0,
        axis=1
    )
    # Compute required to warehouse (req_wh)
    pillow_df['req_wh'] = pillow_df.apply(
        lambda row: 20 - row['warehouse_qty'] if row['warehouse_qty'] < 20 else 0,
        axis=1
    )
    # Format numeric values for display
    def format_qty(value):
        try:
            value = float(value)
            if value == 0:
                return '-'
            elif value.is_integer():
                return str(int(value))
            else:
                return str(value)
        except:
            return '-'
    for col in ['showroom_qty', 'warehouse_qty', 'req_sh', 'req_wh']:
        pillow_df[col] = pillow_df[col].apply(format_qty)

    # Convert to list of dicts for template rendering
    pillow_products = pillow_df.to_dict(orient='records')
    return render_template("product1.html", pillows=pillow_products)

# this is when using Mekari API
# @app.route('/api/sales_by_products', methods=["GET"])
# def sales_by_products():
#     start_date = request.args.get('start_date')
#     end_date = request.args.get('end_date')
#     data = get_sales_by_products_dynamic(start_date, end_date)
#     return jsonify(data)

@app.route('/api/sales_by_products', methods=["GET"])
def sales_by_products():
    # Always use dummy data for now
    data = {
        "sales_by_products": {
            "reports": {
                "products": [
                    {"product": {"product_name": "Pillow", "quantity": 20}},
                    {"product": {"product_name": "Mattress", "quantity": 15}},
                    {"product": {"product_name": "Topper", "quantity": 10}},
                ]
            }
        }
    }
    return jsonify(data)

# Add your project folder
path = '/home/puputheveya/heveya-bali'
if path not in sys.path:
    sys.path.insert(0, path)

@app.route('/sales_kpi')
def sales_kpi():
    return render_template('sales_kpi.html')

@app.route("/sales_quote")
def sales_quote():
    df = pd.read_csv("static/data/products_std.csv")

    # Make sure image_url has no extra spaces
    df['image_url'] = df['image_url'].astype(str).str.strip()

    product_list = df.to_dict(orient='records')
    return render_template("sales_quote.html", product_list=product_list)


@app.route('/sales_order')
def sales_order():
    return render_sales_order()

@app.route("/sales_order/<transaction_no>")
def sales_order_detail_route(transaction_no):  # ✅ Rename to avoid name conflict
    return render_sales_order_detail(transaction_no)

@app.route('/sales_order/save_detail/<transaction_no>', methods=['POST'])
def save_sales_order_detail_route(transaction_no):  # ✅ Rename to avoid name conflict
    return save_sales_order_detail(transaction_no)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reloader=False)
