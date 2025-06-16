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
ENDPOINT = '/public/jurnal/api/v1/sales_by_products'

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

def get_sales_by_products():
    method = 'GET'
    query = '?start_date=2024-01-01&end_date=2025-01-01'  # 🗓️ Add date range here
    full_path = ENDPOINT + query
    url = BASE_URL + full_path

    date_header = get_rfc7231_date()
    auth_header = generate_hmac_header(method, full_path, date_header)

    headers = {
        'Content-Type': 'application/json',
        'Date': date_header,
        'Authorization': auth_header
    }

    # print("📤 Sending GET to:", url)
    # print("🧾 Headers:", headers)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error {response.status_code}:", response.text)
        return None


def get_sales_by_products_dynamic(start, end):
    method = 'GET'
    query = f'?start_date={start}&end_date={end}'
    full_path = ENDPOINT + query
    url = BASE_URL + full_path

    date_header = get_rfc7231_date()
    auth_header = generate_hmac_header(method, full_path, date_header)

    headers = {
        'Content-Type': 'application/json',
        'Date': date_header,
        'Authorization': auth_header
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}


# # Fetch the data
# data = get_sales_by_products()

# # ✅ Pretty print the JSON only if data is returned
# if data:
#     print("✅ Formatted Response:")
#     print(json.dumps(data, indent=2))