import os
import time
import hmac
import json
import base64
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from email.utils import formatdate

# Mekari credentials
CLIENT_ID = 'afaku9tq7KET9tMm'
CLIENT_SECRET = '8qTvnRqnasNwCRjf0ocpUlgxkfVN4TBX'
BASE_URL = 'https://api.mekari.com'
ENDPOINT = '/public/jurnal/api/v1/purchase_orders'

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

def fetch_purchase_orders_test():
    method = 'GET'
    date_header = get_rfc7231_date()
    query = '?page=1&start_date=2025-06-10&end_date=2025-06-29'
    full_path = ENDPOINT + query
    url = BASE_URL + full_path
    auth_header = generate_hmac_header(method, full_path, date_header)

    headers = {
        'Content-Type': 'application/json',
        'Date': date_header,
        'Authorization': auth_header
    }

    print("🔑 FULL PATH:", full_path)
    print("🧾 Authorization Header:", headers['Authorization'])

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("✅ Fetched:", len(data.get('purchase_orders', [])), "orders")
        with open('static/data/purchase_orders_10_29_jun.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

fetch_purchase_orders_test()
