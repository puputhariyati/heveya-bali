import requests
import hashlib
import base64
import hmac
import json
from email.utils import formatdate

# Mekari credentials
CLIENT_ID = 'afaku9tq7KET9tMm'
CLIENT_SECRET = '8qTvnRqnasNwCRjf0ocpUlgxkfVN4TBX'
BASE_URL = 'https://api.mekari.com'
ENDPOINT = '/public/jurnal/api/v1/customers'

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

def find_customer_in_pages(target_name, start_page=11, end_page=11):
    method = 'GET'
    full_path = ENDPOINT
    url = BASE_URL + full_path

    for page in range(start_page, end_page + 1):
        date_header = get_rfc7231_date()
        auth_header = generate_hmac_header(method, full_path, date_header)

        headers = {
            'Content-Type': 'application/json',
            'Date': date_header,
            'Authorization': auth_header
        }

        params = {
            "page": page,
            "type": "customer"
        }

        print(f"📤 Searching on page {page}...")

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            customers = data.get('customers', [])

            for customer in customers:
                if customer.get('display_name') == target_name:
                    print(f"✅ Found '{target_name}' on page {page}!")
                    return customer  # Return immediately when found
        else:
            print(f"❌ Error {response.status_code} on page {page}: {response.text}")

    print(f"❌ '{target_name}' not found in pages {start_page}-{end_page}.")
    return None

# 🔥 Now use it
target_name = "Ann Marie"
customer_data = find_customer_in_pages(target_name)

# if customer_data:
#     print("✅ Customer Data:")
#     print(json.dumps(customer_data, indent=2))
