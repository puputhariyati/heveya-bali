import requests
import csv, sqlite3, re
from flask import jsonify, request
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import calendar

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

# ✅ for @app.route("/api/set-monthly-target", methods=["POST"])
def render_set_monthly_target():
    import sqlite3
    data = request.get_json()
    month = data.get("month")  # format: '2025-07'
    target = float(data.get("target", 0))
    if not month:
        return jsonify({"error": "Month is required"}), 400
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales_targets (
            month TEXT PRIMARY KEY,
            target REAL NOT NULL
        )
    """)
    cur.execute("""
        INSERT INTO sales_targets (month, target)
        VALUES (?, ?)
        ON CONFLICT(month) DO UPDATE SET target=excluded.target
    """, (month, target))
    conn.commit()
    conn.close()
    return jsonify({"message": "Target saved"})


# ✅ for @app.route("/api/sales-vs-target")
def render_api_sales_vs_target():
    view = request.args.get("view", "monthly")
    start_date = request.args.get("start_date", "2025-01-01")
    end_date = request.args.get("end_date", "2025-07-31")

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    # 1️⃣ Get actual sales per day
    cur.execute("""
        SELECT
            substr(o.transaction_date, 7, 4) || '-' ||  -- yyyy
            substr(o.transaction_date, 4, 2) || '-' ||  -- mm
            substr(o.transaction_date, 1, 2) AS date,
            SUM(unit_sold_price) AS amount
        FROM sales_invoices_detail d
        JOIN sales_invoices o ON TRIM(d.transaction_no) = TRIM(o.transaction_no)
        WHERE date BETWEEN ? AND ?
        GROUP BY date
    """, (start_date, end_date))
    daily_sales = cur.fetchall()

    # 2️⃣ Get monthly targets
    cur.execute("SELECT month, target FROM sales_targets")
    monthly_targets_raw = dict(cur.fetchall())
    conn.close()

    # 3️⃣ Prepare actuals
    actuals = defaultdict(float)
    for date_str, amount in daily_sales:
        amount = amount or 0
        date = datetime.strptime(date_str, "%Y-%m-%d")

        if view == "daily":
            key = date.strftime("%Y-%m-%d")
        elif view == "monthly":
            key = date.strftime("%Y-%m")
        elif view == "quarterly":
            quarter = (date.month - 1) // 3 + 1
            key = f"{date.year}-Q{quarter}"
        elif view == "yearly":
            key = str(date.year)
        else:
            key = date.strftime("%Y-%m")

        actuals[key] += amount

    # 4️⃣ Prepare targets
    targets = defaultdict(float)

    if view == "daily":
        for date_str, _ in daily_sales:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            month_str = date.strftime("%Y-%m")
            days_in_month = calendar.monthrange(date.year, date.month)[1]
            daily_target = monthly_targets_raw.get(month_str, 0) / days_in_month
            targets[date_str] = daily_target

    elif view == "monthly":
        for month_str, target in monthly_targets_raw.items():
            targets[month_str] = target

    elif view == "quarterly":
        for month_str, target in monthly_targets_raw.items():
            dt = datetime.strptime(month_str, "%Y-%m")
            quarter = (dt.month - 1) // 3 + 1
            qkey = f"{dt.year}-Q{quarter}"
            targets[qkey] += target

    elif view == "yearly":
        for month_str, target in monthly_targets_raw.items():
            dt = datetime.strptime(month_str, "%Y-%m")
            ykey = str(dt.year)
            targets[ykey] += target

    # 5️⃣ Merge periods
    periods = sorted(set(actuals.keys()) | set(targets.keys()))
    result = [
        {
            "period": p,
            "actual": actuals.get(p, 0),
            "target": targets.get(p, 0)
        }
        for p in periods
    ]

    return jsonify(result)

