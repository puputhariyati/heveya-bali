import requests
import csv, sqlite3, re
from flask import jsonify
from pathlib import Path

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

def render_api_sales_by_category():
    # 1️⃣ build item → category map from CSV
    item_to_cat = {}
    with PRODUCTS_STD.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            item_to_cat[_norm(row["name"])] = (row["Category"] or "Unknown").strip()

    # 2️⃣ sum qty per item from DB
    conn = sqlite3.connect(DATABASE)
    cur  = conn.cursor()
    cur.execute("""
        SELECT item, SUM(qty) AS total_qty
        FROM sales_order_detail
        GROUP BY item
    """)
    rows = cur.fetchall()
    conn.close()

    # 3️⃣ collapse into categories
    cat_totals = {}
    for item, qty in rows:
        cat = item_to_cat.get(_norm(item), "Unknown")
        cat_totals[cat] = cat_totals.get(cat, 0) + (qty or 0)

    # 4️⃣ jsonify in chart‑friendly format
    payload = [
        {"name": cat, "value": qty}           # <-- keys the chart lib expects
        for cat, qty in sorted(cat_totals.items(), key=lambda x: -x[1])
    ]
    return jsonify(payload)



# def get_sales_by_products():
#     method = 'GET'
#     query = '?start_date=2024-01-01&end_date=2025-01-01'  # 🗓️ Add date range here
#     full_path = ENDPOINT + query
#     url = BASE_URL + full_path
#
#     date_header = get_rfc7231_date()
#     auth_header = generate_hmac_header(method, full_path, date_header)
#
#     headers = {
#         'Content-Type': 'application/json',
#         'Date': date_header,
#         'Authorization': auth_header
#     }
#
#     # print("📤 Sending GET to:", url)
#     # print("🧾 Headers:", headers)
#
#     response = requests.get(url, headers=headers)
#
#     if response.status_code == 200:
#         return response.json()
#     else:
#         print(f"❌ Error {response.status_code}:", response.text)
#         return None
#
#
# def get_sales_by_products_dynamic(start, end):
#     method = 'GET'
#     query = f'?start_date={start}&end_date={end}'
#     full_path = ENDPOINT + query
#     url = BASE_URL + full_path
#
#     date_header = get_rfc7231_date()
#     auth_header = generate_hmac_header(method, full_path, date_header)
#
#     headers = {
#         'Content-Type': 'application/json',
#         'Date': date_header,
#         'Authorization': auth_header
#     }
#
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         return {"error": response.text}


# # Fetch the data
# data = get_sales_by_products()

# # ✅ Pretty print the JSON only if data is returned
# if data:
#     print("✅ Formatted Response:")
#     print(json.dumps(data, indent=2))