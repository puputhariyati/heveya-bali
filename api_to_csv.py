import base64
import csv
import hashlib
import hmac
from email.utils import formatdate

import requests
from datetime import datetime

CLIENT_ID = 'afaku9tq7KET9tMm'
CLIENT_SECRET = '8qTvnRqnasNwCRjf0ocpUlgxkfVN4TBX'
BASE_URL = 'https://api.mekari.com'
# ENDPOINT = '/public/jurnal/api/v1/products'
ENDPOINT = '/public/jurnal/api/v1/sales_orders'

# def get_rfc7231_date():
#     return formatdate(usegmt=True)
#
# def generate_hmac_header(method, full_path, date_header):
#     signing_string = f'date: {date_header}\n{method} {full_path} HTTP/1.1'
#     digest = hmac.new(
#         CLIENT_SECRET.encode(),
#         signing_string.encode(),
#         hashlib.sha256
#     ).digest()
#     signature = base64.b64encode(digest).decode()
#     return f'hmac username="{CLIENT_ID}", algorithm="hmac-sha256", headers="date request-line", signature="{signature}"'

# def fetch_and_save_products_csv(filename='products_per30Jun.csv', start_page=161):
#     page = start_page
#     more_pages = True
#     first_write = page == 1  # Write header only if starting fresh
#
#     with open(filename, 'a', newline='', encoding='utf-8') as f:
#         fieldnames = ['id', 'product_code', 'name', 'showroom_qty', 'warehouse_qty']
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#
#         if first_write:
#             writer.writeheader()
#
#         while more_pages:
#             method = 'GET'
#             query = f'?archive=false&page={page}'
#             full_path = ENDPOINT + query
#             url = BASE_URL + full_path
#
#             date_header = get_rfc7231_date()
#             auth_header = generate_hmac_header(method, full_path, date_header)
#
#             headers = {
#                 'Date': date_header,
#                 'Authorization': auth_header,
#                 'Accept': 'application/json'
#             }
#
#             response = requests.get(url, headers=headers)
#
#             if response.status_code == 200:
#                 data = response.json()
#                 products = data.get('products', [])
#
#                 if not products:
#                     print(f"✅ No more products at page {page}")
#                     break
#
#                 for product in products:
#                     warehouses = product.get('warehouses', {})
#                     showroom_qty = warehouses.get('183271', {}).get('quantity', 0)
#                     warehouse_qty = warehouses.get('183275', {}).get('quantity', 0)
#
#                     writer.writerow({
#                         'id': product.get('id'),
#                         'product_code': product.get('product_code'),
#                         'name': product.get('name'),
#                         'showroom_qty': showroom_qty,
#                         'warehouse_qty': warehouse_qty
#                     })
#
#                 print(f"✅ Page {page} saved ({len(products)} products)")
#                 page += 1
#             elif response.status_code == 429:
#                 print(f"🚫 Rate limit hit at page {page}. Try again later.")
#                 break
#             else:
#                 print(f"❌ Failed at page {page}: {response.status_code} - {response.text}")
#                 break
#
#     print(f"✅ Finished saving to: {filename}")
#
# # Run it
# fetch_and_save_products_csv()


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

def fetch_and_save_sales_order_csv(filename='sales_orders_jun2025.csv', start_page=1):
    page = start_page
    more_pages = True
    first_write = page == 1  # Write header only if starting fresh
    method = 'GET'
    date_header = get_rfc7231_date()

    with open(filename, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['transaction_no', 'transaction_date', 'customer', 'product_code', 'product_name', 'quantity', 'total']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if first_write:
            writer.writeheader()

        while more_pages:
            query = f'?start_date=2025-06-01&end_date=2025-06-30&page={page}&sort_by=transaction_date&sort_order=asc'

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
                    print(f"✅ No more sales order at page {page}")
                    break

                # Function to clean and convert total to numeric
                def clean_amount(value):
                    if not value:
                        return ''
                    value = value.replace("Rp", "").replace(".", "").replace(",", "").strip()
                    try:
                        return int(value)
                    except ValueError:
                        return ''

                for order in sales_orders:
                    lines = order.get('transaction_lines_attributes', [])
                    wrote_total = False
                    for item in lines:
                        product = item.get('product', {})
                        writer.writerow({
                            'transaction_no': order.get('transaction_no'),
                            'transaction_date': order.get('transaction_date'),
                            'customer': order.get('person', {}).get('display_name', ''),
                            'product_code': product.get('product_code', ''),
                            'product_name': product.get('name', ''),
                            'quantity': item.get('quantity', 0),
                            'total': clean_amount(
                                order.get('original_amount_currency_format')) if not wrote_total else ''
                        })
                        wrote_total = True

                print(f"✅ Page {page} saved ({len(sales_orders)} sales orders)")
                page += 1
            elif response.status_code == 429:
                print(f"🚫 Rate limit hit at page {page}. Try again later.")
                break
            else:
                print(f"❌ Failed at page {page}: {response.status_code} - {response.text}")
                break

    print(f"✅ Finished saving to: {filename}")
    print(f"✅ Total sales orders fetched: {len(sales_orders)}")

# Run it
fetch_and_save_sales_order_csv()