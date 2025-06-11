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
ENDPOINT = '/public/jurnal/api/v1/products'

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

def fetch_all_products(start_page=1):
    all_products = []
    page = start_page
    more_pages = True

    while more_pages:
        method = 'GET'
        query = f'?archive=false&page={page}'
        full_path = ENDPOINT + query
        url = BASE_URL + full_path

        date_header = get_rfc7231_date()
        auth_header = generate_hmac_header(method, full_path, date_header)

        headers = {
            'Date': date_header,
            'Authorization': auth_header,
            'Accept': 'application/json'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            all_products.extend(products)

            links = data.get('links', {})
            if 'next_link' in links and links['next_link']:
                page += 1
            else:
                more_pages = False
        elif response.status_code == 429:
            print(f"🚫 Rate limit hit at page {page}. Try again after a minute.")
            break
        else:
            print(f"❌ Failed on page {page}: {response.status_code} - {response.text}")
            break

    return all_products


# Resume from page 41
resumed_products = fetch_all_products(start_page=161)

# Load previously saved products
with open('product_non_archived.json') as f:
    existing_products = json.load(f)

# Combine and save again
combined = existing_products + resumed_products

with open('product_non_archived.json', 'w') as f:
    json.dump(combined, f, indent=2)

print(f"✅ Total saved products: {len(combined)}")
