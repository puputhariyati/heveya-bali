import sqlite3
import pandas as pd
import os

from flask import Flask, render_template, jsonify, request

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / "key.env")
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "main.db"


def render_sales_quote():
    conn = sqlite3.connect(DATABASE)
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


def render_save_quote(data):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        discount = float(data.get('discount', 0))
        full_amount = float(data.get('full_amount', 0))
        avg_disc = (discount / full_amount * 100) if full_amount else 0

        cursor.execute('''
            INSERT INTO sales_quotes (
                date, customer, phone, full_amount, discount, avg_disc,
                grand_total, margin, status, ETD, quote_no
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('date'),
            data.get('customer'),
            data.get('phone'),
            full_amount,
            discount,
            avg_disc,
            data.get('grand_total'),
            data.get('margin'),
            data.get('status'),
            data.get('ETD'),
            data.get('quote_no'),
        ))

        quote_id = cursor.lastrowid

        for item in data['items']:
            cursor.execute('''
                INSERT INTO sales_quote_items (
                    quote_id, description, qty, unit, unit_price, discount,
                    discounted_price, amount, notes, full_amount, unit_cost,
                    total_cost, margin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                quote_id,
                item.get('description'),
                item.get('qty'),
                item.get('unit'),
                item.get('unit_price'),
                item.get('discount'),
                item.get('discounted_price'),
                item.get('amount'),
                item.get('notes'),
                item.get('full_amount'),
                item.get('unit_cost'),
                item.get('total_cost'),
                item.get('margin')
            ))

        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'quote_id': quote_id})

    except Exception as e:
        print("❌ Error in render_save_quote:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500



def render_edit_quote(quote_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sales_quotes WHERE id = ?", (quote_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return "Quote not found", 404

    quote = dict(row)  # ✅ convert to dict for template safety

    # ✅ Fill in any missing keys expected by the template
    expected_keys = ['id', 'date', 'customer', 'address', 'phone', 'full_amount', 'discount',
                     'grand_total', 'margin', 'status', 'ETD']
    for key in expected_keys:
        quote.setdefault(key, '')

    df = pd.read_csv("static/data/products_std.csv")
    df['image_url'] = df['image_url'].astype(str).str.strip()
    product_list = df.to_dict(orient='records')

    return render_template("create_quote.html", quote=quote, product_list=product_list, edit_mode=True)