import requests
import hashlib
import base64
import hmac
import json
import datetime
import time
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

# def fetch_sales_orders(start_page=1, max_page=200):
#     all_sales_orders = []
#     method = 'GET'
#     date_header = get_rfc7231_date()
#
#     for page in range(start_page, max_page + 1):
#         query = f'?start_date=2025-05-01&end_date=2025-05-31&page={page}&sort_by=transaction_date&sort_order=asc'
#         full_path = ENDPOINT + query
#         url = BASE_URL + full_path
#         auth_header = generate_hmac_header(method, full_path, date_header)
#
#         headers = {
#             'Content-Type': 'application/json',
#             'Date': date_header,
#             'Authorization': auth_header
#         }
#
#         print(f"🔄 Fetching page {page}...")
#         response = requests.get(url, headers=headers)
#
#         if response.status_code == 200:
#             data = response.json()
#             sales_orders = data.get('sales_orders', [])
#             if not sales_orders:
#                 print("✅ No more data.")
#                 break
#             all_sales_orders.extend(sales_orders)
#         else:
#             print(f"❌ Error on page {page}: {response.status_code} - {response.text}")
#             break
#
#     return all_sales_orders
#
# # 📦 Fetch and Save
# sales_orders = fetch_sales_orders(start_page=1)
# print(f"✅ Total sales orders fetched: {len(sales_orders)}")
#
# # Optional: sort again (just in case)
# sales_orders.sort(key=lambda x: x.get("transaction_date", ""))
#
# # 💾 Save to JSON
# with open('static/data/sales_orders_May2025.json', 'w', encoding='utf-8') as f:
#     json.dump(sales_orders, f, indent=2, ensure_ascii=False)

# def fetch_open_sales_orders(start_page=1, max_page=200):
#     all_sales_orders = []
#     method = 'GET'
#     date_header = get_rfc7231_date()
#
#     for page in range(start_page, max_page + 1):
#         # ✅ Add status=open to query string
#         query = f'?status=open&page={page}&sort_by=transaction_date&sort_order=asc'
#         full_path = ENDPOINT + query
#         url = BASE_URL + full_path
#         auth_header = generate_hmac_header(method, full_path, date_header)
#
#         headers = {
#             'Content-Type': 'application/json',
#             'Date': date_header,
#             'Authorization': auth_header
#         }
#
#         print(f"🔄 Fetching page {page}...")
#         response = requests.get(url, headers=headers)
#
#         if response.status_code == 200:
#             data = response.json()
#             sales_orders = data.get('sales_orders', [])
#             if not sales_orders:
#                 print("✅ No more data.")
#                 break
#             all_sales_orders.extend(sales_orders)
#         else:
#             print(f"❌ Error on page {page}: {response.status_code} - {response.text}")
#             break
#
#     return all_sales_orders
#
# # 📦 Fetch and Save
# sales_orders = fetch_open_sales_orders(start_page=1)
# print(f"✅ Total OPEN sales orders fetched: {len(sales_orders)}")
#
# # Optional: sort again
# sales_orders.sort(key=lambda x: x.get("transaction_date", ""))
# #
# # 💾 Save to JSON
# with open('static/data/sales_orders_open.json', 'w', encoding='utf-8') as f:
#     json.dump(sales_orders, f, indent=2, ensure_ascii=False)
#
# def load_sales_orders():
#     # Load open and closed orders
#     with open("static/data/sales_orders_open.json", "r", encoding="utf-8") as f:
#         open_orders = json.load(f)
#
#     with open("static/data/sales_orders_closed.json", "r", encoding="utf-8") as f:
#         closed_orders = json.load(f)
#
#     # Keep all open orders
#     all_orders = open_orders
#
#     # Define specific closed orders to include by transaction_no
#     include_transaction_nos = {
#         "10325", "11719", "11887", "12322", "12182", "13367", "12076"
#     }
#
#     # Define a date threshold (optional if you want recent ones)
#     DATE_THRESHOLD = datetime.datetime(2024, 1, 1)  # Change this as needed
#
#     # Filter and include desired closed orders
#     for order in closed_orders:
#         order_no = order.get("transaction_no")
#         order_date_str = order.get("transaction_date")  # assumes format "YYYY-MM-DD"
#         try:
#             order_date = datetime.datetime.strptime(order_date_str, "%Y-%m-%d")
#         except:
#             order_date = None
#
#         if order_no in include_transaction_nos or (order_date and order_date >= DATE_THRESHOLD):
#             all_orders.append(order)
#
#     return all_orders


# def fetch_filtered_closed_sales_orders(start_page=30, end_page=50):
#     all_sales_orders = []
#     include_transaction_nos = {
#         "10325", "11719", "11887", "12322", "12182", "13367", "12076"
#     }
#     date_threshold = datetime(2025, 6, 19)
#
#     for page in range(start_page, end_page + 1):
#         method = 'GET'
#         date_header = get_rfc7231_date()
#         query = f'?status=closed&page={page}&sort_by=transaction_date&sort_order=asc'
#         full_path = ENDPOINT + query
#         url = BASE_URL + full_path
#         auth_header = generate_hmac_header(method, full_path, date_header)
#
#         headers = {
#             'Content-Type': 'application/json',
#             'Date': date_header,
#             'Authorization': auth_header
#         }
#
#         print(f"🔄 Fetching closed page {page}...")
#         response = requests.get(url, headers=headers)
#
#         if response.status_code == 200:
#             data = response.json()
#             sales_orders = data.get('sales_orders', [])
#             if not sales_orders:
#                 print("✅ No more closed sales orders.")
#                 break
#
#             for order in sales_orders:
#                 tx_no = order.get("transaction_no")
#                 tx_date_str = order.get("transaction_date")
#
#                 try:
#                     tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d")
#                 except:
#                     tx_date = None
#
#                 if tx_no in include_transaction_nos or (tx_date and tx_date >= date_threshold):
#                     all_sales_orders.append(order)
#
#         elif response.status_code == 401:
#             print(f"❌ Unauthorized at page {page}: {response.status_code} - {response.text}")
#             print("⏳ Possibly hit a rate limit or time sync issue. You can resume from this page.")
#             break
#         else:
#             print(f"❌ Error on page {page}: {response.status_code} - {response.text}")
#             break
#
#         time.sleep(1)  # Wait to avoid rate limits
#
#     return all_sales_orders
#
#
# # ✅ Fetch closed orders by page range
# filtered_closed_orders = fetch_filtered_closed_sales_orders(start_page=30, end_page=50)
# print(f"✅ Fetched: {len(filtered_closed_orders)} filtered closed orders")
#
# # ✅ Combine with existing file
# output_path = 'static/data/sales_orders_closed_2024_190625.json'
#
# if os.path.exists(output_path):
#     with open(output_path, 'r', encoding='utf-8') as f:
#         existing_orders = json.load(f)
# else:
#     existing_orders = []
#
# ✅ Combine + deduplicate by transaction_no
combined_orders = existing_orders + filtered_closed_orders
seen_tx = set()
deduplicated = []
for order in combined_orders:
    tx_no = order.get("transaction_no")
    if tx_no not in seen_tx:
        deduplicated.append(order)
        seen_tx.add(tx_no)

# ✅ Sort by transaction_date
deduplicated.sort(key=lambda x: x.get("transaction_date", ""))

# ✅ Save to file
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(deduplicated, f, indent=2, ensure_ascii=False)

print(f"✅ File updated → {output_path} | Total orders: {len(deduplicated)}")

# def fetch_sales_orders_from_date(start_date_str="2025-06-19", end_page=100):
#     all_sales_orders = []
#     start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
#
#     for page in range(1, end_page + 1):
#         method = 'GET'
#         date_header = get_rfc7231_date()
#         query = f'?page={page}&sort_by=transaction_date&sort_order=asc'
#         full_path = ENDPOINT + query
#         url = BASE_URL + full_path
#         auth_header = generate_hmac_header(method, full_path, date_header)
#
#         headers = {
#             'Content-Type': 'application/json',
#             'Date': date_header,
#             'Authorization': auth_header
#         }
#
#         print(f"🔄 Fetching page {page}...")
#         response = requests.get(url, headers=headers)
#
#         if response.status_code == 200:
#             data = response.json()
#             sales_orders = data.get('sales_orders', [])
#             if not sales_orders:
#                 print("✅ No more data.")
#                 break
#
#             for order in sales_orders:
#                 tx_date_str = order.get("transaction_date")
#                 try:
#                     tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d")
#                 except:
#                     tx_date = None
#
#                 if tx_date and tx_date >= start_date:
#                     all_sales_orders.append(order)
#
#         else:
#             print(f"❌ Error on page {page}: {response.status_code} - {response.text}")
#             break
#
#         time.sleep(1)
#
#     return all_sales_orders
#
# filtered_orders = fetch_sales_orders_from_date("2025-06-19", end_page=100)
# print(f"✅ Fetched {len(filtered_orders)} sales orders from 2025-06-19 to today")
#
# # Save to file
# output_path = 'static/data/sales_orders_from_2025_06_19.json'
# with open(output_path, 'w', encoding='utf-8') as f:
#     json.dump(filtered_orders, f, indent=2, ensure_ascii=False)
#
# print(f"✅ Saved to {output_path}")


# # pull sales_order data from 19 june to 25 july
# def fetch_sales_orders_between(start_date_str="2025-06-19", end_date_str=None, end_page=100):
#     all_sales_orders = []
#     start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
#     end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else datetime.today()
#
#     for page in range(1, end_page + 1):
#         method = 'GET'
#         date_header = get_rfc7231_date()
#
#         query = (
#             f'?page={page}'
#             f'&sort_by=transaction_date'
#             f'&sort_order=asc'
#             f'&start_date={start_date_str}'
#             f'&end_date={end_date_str or end_date.strftime("%Y-%m-%d")}'
#         )
#         full_path = ENDPOINT + query
#         url = BASE_URL + full_path
#         auth_header = generate_hmac_header(method, full_path, date_header)
#
#         headers = {
#             'Content-Type': 'application/json',
#             'Date': date_header,
#             'Authorization': auth_header
#         }
#
#         print(f"🔄 Fetching page {page}...")
#         response = requests.get(url, headers=headers)
#
#         if response.status_code == 200:
#             data = response.json()
#             sales_orders = data.get('sales_orders', [])
#             if not sales_orders:
#                 print("✅ No more data.")
#                 break
#
#             for order in sales_orders:
#                 tx_date_str = order.get("transaction_date")
#                 print("📅", tx_date_str)
#                 all_sales_orders.append(order)
#
#         else:
#             print(f"❌ Error on page {page}: {response.status_code} - {response.text}")
#             break
#
#         time.sleep(1)
#
#     return all_sales_orders
#
#
# # usage
# orders = fetch_sales_orders_between("2025-06-19", "2025-06-25")
# with open('static/data/sales_orders_2025_06_19_to_25.json', 'w', encoding='utf-8') as f:
#     json.dump(orders, f, indent=2, ensure_ascii=False)
# print(f"✅ Saved {len(orders)} orders.")
#

