import requests
import hashlib
import base64
import hmac
import json
from email.utils import formatdate
from datetime import datetime

# Mekari credentials
CLIENT_ID = 'afaku9tq7KET9tMm'
CLIENT_SECRET = '8qTvnRqnasNwCRjf0ocpUlgxkfVN4TBX'
BASE_URL = 'https://api.mekari.com'
ENDPOINT = '/public/jurnal/api/v1/sales_orders'

def get_rfc7231_date():
    return formatdate(usegmt=True)

def generate_hmac_header(method, full_path, date_header):
    signing_string = f'date: {date_header}\n{method} {full_path} HTTP/1.1'
    digest = hmac.new(
        CLIENT_SECRET.encode(),
        signing_string.encode(),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(digest).decode()
    return f'hmac username="{CLIENT_ID}", algorithm="hmac-sha256", headers="date request-line", signature="{signature}"'

def fetch_sales_orders(start_page=1, max_page=200):
    all_sales_orders = []
    method = 'GET'
    date_header = get_rfc7231_date()

    for page in range(start_page, max_page + 1):
        query = f'?start_date=2025-05-01&end_date=2025-05-31&page={page}&sort_by=transaction_date&sort_order=asc'
        full_path = ENDPOINT + query
        url = BASE_URL + full_path
        auth_header = generate_hmac_header(method, full_path, date_header)

        headers = {
            'Content-Type': 'application/json',
            'Date': date_header,
            'Authorization': auth_header
        }

        print(f"🔄 Fetching page {page}...")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            sales_orders = data.get('sales_orders', [])
            if not sales_orders:
                print("✅ No more data.")
                break
            all_sales_orders.extend(sales_orders)
        else:
            print(f"❌ Error on page {page}: {response.status_code} - {response.text}")
            break

    return all_sales_orders

# 📦 Fetch and Save
sales_orders = fetch_sales_orders(start_page=1)
print(f"✅ Total sales orders fetched: {len(sales_orders)}")

# Optional: sort again (just in case)
sales_orders.sort(key=lambda x: x.get("transaction_date", ""))

# 💾 Save to JSON
with open('static/data/sales_orders_May2025.json', 'w', encoding='utf-8') as f:
    json.dump(sales_orders, f, indent=2, ensure_ascii=False)
