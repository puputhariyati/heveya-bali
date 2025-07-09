import csv
import os
from flask import Flask, render_template, jsonify, request
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "key.env")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

BASE_DIR = Path(__file__).parent
QUOTES_FILE = BASE_DIR / "static/data/sales_quotes.csv"
DETAIL_FILE = BASE_DIR / "static/data/sales_quote_detail.csv"
PRODUCTS_CSV = BASE_DIR / "static/data/products_std.csv"

def render_sales_quote():
    sales_quotes = []
    if QUOTES_FILE.exists():
        with open(QUOTES_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('id'):
                    sales_quotes.append(row)
    return render_template("sales_quote.html", quotes=sales_quotes)

def render_create_quote():
    df = pd.read_csv(PRODUCTS_CSV)
    df['image_url'] = df['image_url'].astype(str).str.strip()
    product_list = df.to_dict(orient='records')
    return render_template("create_quote.html", product_list=product_list, quote=None)

def render_save_quote():
    try:
        data = request.get_json()
        print("🔍 Received Quote:", data)

        quote_id = data.get("id")
        is_edit = False

        # Load existing quotes
        existing_quotes = []
        if QUOTES_FILE.exists():
            with open(QUOTES_FILE, newline='') as f:
                reader = csv.DictReader(f)
                existing_quotes = list(reader)

        if quote_id:
            is_edit = any(q["id"] == quote_id for q in existing_quotes)
        else:
            ids = [int(q["id"]) for q in existing_quotes if q["id"].isdigit()]
            quote_id = str(max(ids, default=0) + 1)
            data["id"] = quote_id

        # ✅ Save updated quote list (overwrite existing quote if editing)
        headers = [
            'id', 'date', 'quote_no', 'expiry_date',
            'customer', 'address', 'phone',
            'project_name', 'ETD',
            'full_amount', 'discount', 'grand_total', 'margin', 'status'
        ]
        updated_quotes = [q for q in existing_quotes if q["id"] != quote_id]
        updated_quotes.append({k: data.get(k, '') for k in headers})
        with open(QUOTES_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(updated_quotes)

        # ✅ Save updated items (overwrite all previous items for this quote)
        item_headers = ['quote_id', 'description', 'qty', 'unit', 'unit_price', 'discount', 'discounted_price', 'amount', 'notes', 'full_amount', 'unit_cost', 'total_cost', 'margin']
        existing_items = []
        if DETAIL_FILE.exists():
            with open(DETAIL_FILE, newline='') as f:
                reader = csv.DictReader(f)
                existing_items = [r for r in reader if r["quote_id"] != quote_id]

        new_items = []
        for item in data.get("items", []):
            item["quote_id"] = quote_id
            new_items.append({k: item.get(k, '') for k in item_headers})

        with open(DETAIL_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=item_headers)
            writer.writeheader()
            writer.writerows(existing_items + new_items)

        return jsonify({"status": "success", "id": quote_id})

    except Exception as e:
        print("❌ Server error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


def render_edit_quote(quote_id):
    quote = None
    items = []

    if QUOTES_FILE.exists():
        with open(QUOTES_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['id'] == str(quote_id):
                    quote = row
                    break

    if not quote:
        return "Quote not found", 404

    if DETAIL_FILE.exists():
        with open(DETAIL_FILE, newline='') as f:
            reader = csv.DictReader(f)
            items = [r for r in reader if r.get('quote_id') == str(quote_id)]

    # Fill defaults
    expected_keys = ['id', 'date', 'customer', 'address', 'phone', 'full_amount', 'discount', 'grand_total', 'margin', 'status', 'ETD']
    for key in expected_keys:
        quote.setdefault(key, '')

    df = pd.read_csv(PRODUCTS_CSV)
    df['image_url'] = df['image_url'].astype(str).str.strip()
    product_list = df.to_dict(orient='records')
    print("🧾 Editing quote:", quote)

    return render_template("create_quote.html", quote=quote, items=items, product_list=product_list, edit_mode=True)
