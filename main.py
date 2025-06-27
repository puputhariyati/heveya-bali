import csv
import os
import sqlite3
import sys
import pandas as pd
import json

from flask import Flask, request, jsonify, render_template, redirect, flash, json
from dotenv import load_dotenv

from sales_quote import render_sales_quote, render_create_quote, render_save_quote, render_edit_quote
from products import render_products
from sales_order import render_sales_order, update_single_etd, bulk_update_status, bulk_update_etd
from sales_order_detail import render_sales_order_detail, save_sales_order_detail, parse_mattress_name

from pathlib import Path
load_dotenv(Path(__file__).parent / "key.env")


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

# Add your project folder for pythonanywhere
path = '/home/puputheveya/heveya-bali'
if path not in sys.path:
    sys.path.insert(0, path)

#Dashboard page
@app.route('/')
def home():
    return render_template('index.html')

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

@app.route("/products")
def products():
    return render_products()

@app.route('/stock_history')
def stock_history():
    category = request.args.get('category')
    size = request.args.get('size')
    firmness = request.args.get('firmness')
    location = request.args.get('location')

    df = pd.read_csv("static/data/stock_history.csv")
    filtered = df[
        (df['category'] == category) &
        (df['size'] == size) &
        (df['firmness'] == firmness) &
        (df['location'] == location)
    ]

    result = filtered.sort_values('timestamp', ascending=False).to_dict(orient='records')
    return jsonify(result)

@app.route('/adjust_stock', methods=['GET', 'POST'])
def adjust_stock():
    if request.method == 'POST':
        category = request.form['category']
        subcategory = request.form['subcategory']
        size = request.form['size']
        firmness = request.form['firmness']
        location = request.form['location']
        qty = float(request.form['qty'])
        note = request.form['note']
        source = 'Manual Adjust'
        reference = request.form.get('reference', '')

        log_stock_change(category, subcategory, size, firmness, location, qty, note, source, reference)
        flash("Stock adjustment saved successfully!", "success")
        return redirect('/adjust_stock')

    return render_template('adjust_stock.html')

@app.route('/customer')
def render_customer():
    return render_template('customer.html')

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

@app.route('/sales_kpi')
def sales_kpi():
    return render_template('sales_kpi.html')

@app.route('/sales_quote')
def sales_quote():
    return render_sales_quote()

@app.route("/create_quote")
def create_quote():
    return render_create_quote()

@app.route('/save_quote', methods=['POST'])
def save_quote():
    return render_save_quote()

@app.route('/sales_quote/<int:quote_id>')
def edit_quote(quote_id):
    return render_edit_quote(quote_id)

@app.route('/sales_order')
def sales_order():
    return render_sales_order()

@app.route("/sales_order/update_etd", methods=["POST"])
def sales_order_etd():
    return update_single_etd()

@app.route("/sales_order/bulk_update_status", methods=["POST"])
def sales_order_bulk_status():
    return bulk_update_status()

@app.route("/sales_order/bulk_update_etd", methods=["POST"])
def sales_order_bulk_etd():
    return bulk_update_etd()

@app.route("/sales_order/<transaction_no>")
def sales_order_detail_route(transaction_no):  # ✅ Rename to avoid name conflict
    return render_sales_order_detail(transaction_no)

@app.route("/sales_order/<transaction_no>")
def sales_order_detail_mattress(name):  # ✅ Rename to avoid name conflict
    return parse_mattress_name(name)

@app.route('/sales_order/save_detail/<transaction_no>', methods=['POST'])
def save_sales_order_detail_route(transaction_no):  # ✅ Rename to avoid name conflict
    return save_sales_order_detail(transaction_no)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reloader=False)
