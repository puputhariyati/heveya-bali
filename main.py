import csv
import sqlite3, os
import sys
import pandas as pd
import json
from datetime import datetime, timezone, timedelta

from flask import Flask, request, jsonify, render_template, redirect, flash, json
from dotenv import load_dotenv

from sales_quote import render_sales_quote, render_create_quote, render_save_quote, render_edit_quote
from products import render_products
from sales_invoices import sync_sales_invoices, DATABASE, bulk_update_status, bulk_update_etd
# from sales_order import render_sales_order, update_single_etd, bulk_update_status, bulk_update_etd, upsert_sales_order
from sales_order_detail import render_sales_order_detail, save_sales_order_detail, parse_mattress_name
from purchase_order import render_purchase_order, save_purchase_order, update_po_eta
from create_po import render_create_po
from transfer_warehouse import render_transfer_list, render_create_transfer
from attendance import render_attendance, render_attendance_checkin

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

@app.route('/stock_adjust', methods=['GET', 'POST'])
def stock_adjust():
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

    return render_template('stock_adjust.html')

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

# 🔄 Refresh endpoint (POST)
@app.route("/api/refresh-sales-invoices", methods=["POST"])
def refresh_invoices():
    try:
        # --- 1. choose date window (last 30 days here) ------------------
        date_to   = datetime.now().strftime("%Y-%m-%d")
        date_from = "2025-07-01"  # ← fixed start
        # date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d") #backward 30days from today

        # --- 2. pull & upsert ------------------------------------------
        added, updated = sync_sales_invoices(date_from, date_to)

        # make 100 % sure we pass *real* JSON‑serialisable values
        added        = int(added or 0)
        updated      = int(updated or 0)
        last_refresh = datetime.now(timezone.utc)\
                              .isoformat(timespec="seconds")\
                              .replace("+00:00", "Z")

        return jsonify({
            "status"      : "ok",
            "added"       : added,
            "updated"     : updated,
            "last_refresh": last_refresh
        })

    except Exception as e:
        # log to stderr so you can see it in the PA error log
        print("❌ refresh_invoices failed:", e)
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route("/sales_invoices")
def sales_invoices_page():
    conn = get_db_connection()
    cur  = conn.execute("""
        SELECT
          transaction_no,
          transaction_date,              -- may be ISO or DD/MM/YYYY
          COALESCE(customer,'')    AS customer,
          COALESCE(balance_due,'') AS balance_due,
          COALESCE(total,'')       AS total,
          COALESCE(status,'')      AS status,
          COALESCE(etd,'')         AS etd
        FROM sales_order
    """)
    rows_raw = cur.fetchall()
    conn.close()

    rows = []
    for r in rows_raw:
        d = dict(r)

        # --- Parse the date safely ---------------------------------
        iso = d["transaction_date"]
        try:
            # try ISO first
            dt = datetime.strptime(iso, "%Y-%m-%d")
            display_date = dt.strftime("%d/%m/%Y")
        except ValueError:
            # fallback: DD/MM/YYYY in DB already
            try:
                dt = datetime.strptime(iso, "%d/%m/%Y")
                display_date = iso                # already formatted
            except ValueError:
                dt = datetime.min                 # put bad rows at bottom
                display_date = iso

        d["transaction_date"] = display_date
        d["_dt_obj"] = dt        # helper key for sorting
        rows.append(d)

    # --- Sort newest → oldest using _dt_obj -------------------------
    rows.sort(key=lambda x: x["_dt_obj"], reverse=True)

    # Remove helper key before sending to template
    for d in rows:
        d.pop("_dt_obj", None)

    return render_template("sales_invoices.html", orders=rows)

# @app.route('/sales_order')
# def sales_order():
#     return render_sales_order()

# @app.route("/sales_order/update_etd", methods=["POST"])
# def sales_order_etd():
#     return update_single_etd()

@app.route("/sales_invoices/bulk_update_status", methods=["POST"])
def sales_invoices_bulk_status():
    return bulk_update_status()

@app.route("/sales_invoices/bulk_update_etd", methods=["POST"])
def sales_invoices_bulk_etd():
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

@app.route('/refresh_orders')
def refresh_orders():
    new_orders = fetch_from_api_or_json()  # your fetching logic
    conn = get_db_connection()
    for order in new_orders:
        upsert_sales_order(conn, order)
    conn.close()
    return jsonify({"status": "success", "message": "Orders refreshed"})

@app.route('/purchase_order')
def show_purchase_order():
    return render_purchase_order()

@app.route("/create_po")
def create_po():
    return render_create_po()

@app.route('/transfer_warehouse')
def transfer_list():
    return render_transfer_list()

@app.route('/transfers/create', methods=['GET', 'POST'])
def create_transfer():
    return render_create_transfer

@app.route('/transfers/<int:transfer_id>')
def view_transfer(transfer_id):
    transfer = get_transfer_by_id(transfer_id)
    return render_template('view_transfer.html', transfer=transfer)

@app.route('/transfers/<int:transfer_id>/approve')
def approve_transfer(transfer_id):
    if not current_user.is_approver:
        return "Not authorized", 403
    approve_transfer_in_db(transfer_id)
    return redirect(url_for('transfer_list'))

@app.route('/create-test-transfer')
def create_test_transfer():
    transfer = TransferWarehouse(
        date=datetime.now(),
        from_warehouse='Warehouse Bali',
        to_warehouse='Showroom Bali',
        approved=False,
        created_by='puput',
        notes='Urgent showroom restock'
    )
    db.session.add(transfer)
    db.session.commit()
    return "Test transfer created!"

@app.route("/attendance", methods=["GET"])
def attendance_page():
    return render_attendance ()
@app.route("/attendance/checkin", methods=["POST"])
def attendance_checkin():
    return render_attendance_checkin()


if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reloader=False)
