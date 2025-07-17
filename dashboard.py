import requests
import csv, sqlite3, re
from flask import jsonify, request
from pathlib import Path
from datetime import datetime

PRODUCTS_STD = Path("static/data/products_std.csv")   # adjust if elsewhere
DATABASE = Path(__file__).parent / "main.db"
_ws_re        = re.compile(r"\s+")            # collapse 2+ spaces

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def _norm(s: str) -> str:
    """lower‑case + single‑space + trim → key for dict lookup"""
    return _ws_re.sub(" ", s.strip()).lower()

def parse_date(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except Exception as e:
        print(f"⚠️ Date parse error: {date_str} → {e}")
        return None

def render_api_sales_by_category():
    # 1️⃣ Build item → category map from CSV
    item_to_cat = {}
    with PRODUCTS_STD.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            norm_name = _norm(row["name"])
            category = (row["Category"] or "Unknown").strip()
            item_to_cat[norm_name] = category
    print(f"📦 Loaded {len(item_to_cat)} items from products_std.csv")

    # 2️⃣ Sum qty per item from DB (filtered by parsed date)
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    start_date = request.args.get("start_date", "2025-06-01")
    end_date = request.args.get("end_date", "2025-06-30")
    print("➡️ Filtering between:", start_date, "and", end_date)

    cur.execute("""
        SELECT d.item, SUM(d.qty) AS total_qty
        FROM sales_invoices_detail d
        JOIN sales_invoices o ON TRIM(d.transaction_no) = TRIM(o.transaction_no)
        WHERE substr(o.transaction_date, 7, 4) || '-' ||  -- year
              substr(o.transaction_date, 4, 2) || '-' ||  -- month
              substr(o.transaction_date, 1, 2)            -- day
              BETWEEN ? AND ?
        GROUP BY d.item
    """, (start_date, end_date))

    rows = cur.fetchall()
    print(f"📊 Rows from DB: {len(rows)}")

    conn.close()

    # 3️⃣ Collapse into categories
    cat_totals = {}
    unmatched_items = []
    for item, qty in rows:
        norm_item = _norm(item)
        cat = item_to_cat.get(norm_item)
        if not cat:
            unmatched_items.append(item)
            cat = "Unknown"
        cat_totals[cat] = cat_totals.get(cat, 0) + (qty or 0)

    if unmatched_items:
        print("⚠️ Unmatched items (not found in products_std.csv):")
        for u in unmatched_items[:10]:
            print("   ‣", u)
        if len(unmatched_items) > 10:
            print(f"   ... and {len(unmatched_items) - 10} more.")

    # 4️⃣ Format for Plotly
    payload = [
        {"name": cat, "value": qty}
        for cat, qty in sorted(cat_totals.items(), key=lambda x: -x[1])
        if qty > 0
    ]
    print("📊 Final Payload:", payload)

    return jsonify(payload)

def render_api_sales_by_subcategory():
    # map item → subcategory from CSV
    item_to_subcat = {}
    with PRODUCTS_STD.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            norm_name = _norm(row["name"])
            subcat = (row["Subcategory"] or "Unknown").strip()
            item_to_subcat[norm_name] = subcat

    # map item → category (to filter)
    item_to_cat = {}
    with PRODUCTS_STD.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            item_to_cat[_norm(row["name"])] = (row["Category"] or "Unknown").strip()

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    category = request.args.get("category", "")
    start_date = request.args.get("start_date", "2025-06-01")
    end_date = request.args.get("end_date", "2025-06-30")
    print(f"🔍 Subcategory request for: {category}")

    cur.execute("""
        SELECT d.item, SUM(d.qty) AS total_qty
        FROM sales_invoices_detail d
        JOIN sales_invoices o ON TRIM(d.transaction_no) = TRIM(o.transaction_no)
        WHERE substr(o.transaction_date, 7, 4) || '-' ||
              substr(o.transaction_date, 4, 2) || '-' ||
              substr(o.transaction_date, 1, 2)
              BETWEEN ? AND ?
        GROUP BY d.item
    """, (start_date, end_date))

    rows = cur.fetchall()
    conn.close()

    subcat_totals = {}
    for item, qty in rows:
        norm_item = _norm(item)
        item_cat = item_to_cat.get(norm_item)
        if item_cat != category:
            continue
        subcat = item_to_subcat.get(norm_item, "Unknown")
        subcat_totals[subcat] = subcat_totals.get(subcat, 0) + (qty or 0)

    payload = [
        {"name": subcat, "value": qty}
        for subcat, qty in sorted(subcat_totals.items(), key=lambda x: -x[1])
    ]
    return jsonify(payload)
