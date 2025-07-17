import os, csv, base64, hashlib, hmac, requests, json

from email.utils import formatdate
from collections import defaultdict
from datetime import datetime
from flask import Flask
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / "key.env", override=True)
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env
BASE_DIR = Path(__file__).parent

BASE_URL = os.getenv("BASE_URL", "https://api.mekari.com")
# ENDPOINT = '/public/jurnal/api/v1/products'
SALES_ORDERS_ENDPOINT  = "/public/jurnal/api/v1/sales_orders"
SALES_INVOICES_ENDPOINT = '/public/jurnal/api/v1/sales_invoices'
# ENDPOINT = '/public/jurnal/api/v1/sales_quotes'
CUSTOMER_ENDPOINT = "/public/jurnal/api/v1/customers"

def get_rfc7231_date():
    return formatdate(usegmt=True)

def generate_hmac_header(method, full_path, date_header):
    cid  = os.getenv("CLIENT_ID", "").strip()
    csec = os.getenv("CLIENT_SECRET", "").strip()
    if not cid or not csec:
        raise RuntimeError("CLIENT_ID / CLIENT_SECRET missing.")
    signing = f"date: {date_header}\n{method} {full_path} HTTP/1.1"
    signature = base64.b64encode(
        hmac.new(csec.encode(), signing.encode(), hashlib.sha256).digest()
    ).decode()
    return (
        f'hmac username="{cid}", algorithm="hmac-sha256", '
        f'headers="date request-line", signature="{signature}"'
    )


OUT_PATH  = Path("static/data/sales_invoices_2025_0406.json")
CKPT_PATH = Path("sales_invoices_checkpoint.txt")
BATCH     = 500
MAX_PAGES = 200

# ─── DOWNLOAD ────────────────────────────────────────────────────
def fetch_sales_invoices(start_page=1):
    collected, page = [], start_page
    date_hdr = get_rfc7231_date()
    while page <= MAX_PAGES:
        query = (f"?start_date=2025-04-01&end_date=2025-06-30"
                 f"&page={page}&sort_by=transaction_date&sort_order=asc")
        full_path = SALES_INVOICES_ENDPOINT + query
        url       = BASE_URL + full_path
        headers = {
            "Date": date_hdr,
            "Authorization": generate_hmac_header("GET", full_path, date_hdr),
            "Content-Type": "application/json",
        }

        print(f"🔄 Fetching page {page}…")
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"❌ Page {page}: {res.status_code} – {res.text}")
            break

        batch = res.json().get("sales_invoices", [])
        if not batch:
            print("✅ No more data.")
            break

        collected.extend(batch)
        page += 1

        # flush every BATCH rows
        if len(collected) >= BATCH:
            append_to_file(collected)
            collected.clear()
            save_checkpoint(page)

    # write remaining rows
    if collected:
        append_to_file(collected)
        save_checkpoint(page)

def append_to_file(rows):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 1⃣  Load existing array (or start fresh)
    existing = []
    if OUT_PATH.exists():
        try:
            with open(OUT_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Existing JSON corrupt or empty – starting over.")
    # 2⃣  Extend with the new batch
    existing.extend(rows)
    # 3⃣  Write to a temp file then rename (so file is never half‑written)
    tmp_path = OUT_PATH.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    tmp_path.replace(OUT_PATH)
    print(f"💾  Wrote {len(rows)} rows — total now {len(existing)} in {OUT_PATH.name}")

def save_checkpoint(next_page):
    CKPT_PATH.write_text(str(next_page))
    print(f"📌  Checkpoint saved (resume at page {next_page})")

# ─── MAIN ────────────────────────────────────────────────────────
if __name__ == "__main__":
    # resume if checkpoint exists
    start = int(CKPT_PATH.read_text()) if CKPT_PATH.exists() else 1
    fetch_sales_invoices(start_page=1)



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
# #
# # ✅ Combine with existing file
# output_path = 'static/data/sales_orders_closed_2024_190625.json'
#
# if os.path.exists(output_path):
#     with open(output_path, 'r', encoding='utf-8') as f:
#         existing_orders = json.load(f)
# else:
#     existing_orders = []
# #
# # ✅ Combine + deduplicate by transaction_no
# combined_orders = existing_orders + filtered_closed_orders
# seen_tx = set()
# deduplicated = []
# for order in combined_orders:
#     tx_no = order.get("transaction_no")
#     if tx_no not in seen_tx:
#         deduplicated.append(order)
#         seen_tx.add(tx_no)
#
# # ✅ Sort by transaction_date
# deduplicated.sort(key=lambda x: x.get("transaction_date", ""))
#
# # ✅ Save to file
# with open(output_path, 'w', encoding='utf-8') as f:
#     json.dump(deduplicated, f, indent=2, ensure_ascii=False)
#
# print(f"✅ File updated → {output_path} | Total orders: {len(deduplicated)}")

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

#
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


# def fetch_all_products(start_page=1):
#     all_products = []
#     page = start_page
#     more_pages = True
#
#     while more_pages:
#         method = 'GET'
#         query = f'?archive=false&page={page}'
#         full_path = ENDPOINT + query
#         url = BASE_URL + full_path
#
#         date_header = get_rfc7231_date()
#         auth_header = generate_hmac_header(method, full_path, date_header)
#
#         headers = {
#             'Date': date_header,
#             'Authorization': auth_header,
#             'Accept': 'application/json'
#         }
#
#         response = requests.get(url, headers=headers)
#
#         if response.status_code == 200:
#             data = response.json()
#             products = data.get('products', [])
#             all_products.extend(products)
#
#             links = data.get('links', {})
#             if 'next_link' in links and links['next_link']:
#                 page += 1
#             else:
#                 more_pages = False
#         elif response.status_code == 429:
#             print(f"🚫 Rate limit hit at page {page}. Try again after a minute.")
#             break
#         else:
#             print(f"❌ Failed on page {page}: {response.status_code} - {response.text}")
#             break
#
#     return all_products
#
#
# # Resume from page 41
# resumed_products = fetch_all_products(start_page=161)
#
# # Load previously saved products
# with open('product_non_archived.json') as f:
#     existing_products = json.load(f)
#
# # Combine and save again
# combined = existing_products + resumed_products
#
# with open('product_non_archived.json', 'w') as f:
#     json.dump(combined, f, indent=2)
#
# print(f"✅ Total saved products: {len(combined)}")


# def find_customer_in_pages(target_name, start_page=11, end_page=11):
#     method = 'GET'
#     full_path = ENDPOINT
#     url = BASE_URL + full_path
#
#     for page in range(start_page, end_page + 1):
#         date_header = get_rfc7231_date()
#         auth_header = generate_hmac_header(method, full_path, date_header)
#
#         headers = {
#             'Content-Type': 'application/json',
#             'Date': date_header,
#             'Authorization': auth_header
#         }
#
#         params = {
#             "page": page,
#             "type": "customer"
#         }
#
#         print(f"📤 Searching on page {page}...")
#
#         response = requests.get(url, headers=headers, params=params)
#
#         if response.status_code == 200:
#             data = response.json()
#             customers = data.get('customers', [])
#
#             for customer in customers:
#                 if customer.get('display_name') == target_name:
#                     print(f"✅ Found '{target_name}' on page {page}!")
#                     return customer  # Return immediately when found
#         else:
#             print(f"❌ Error {response.status_code} on page {page}: {response.text}")
#
#     print(f"❌ '{target_name}' not found in pages {start_page}-{end_page}.")
#     return None
#
# # 🔥 Now use it
# target_name = "Ann Marie"
# customer_data = find_customer_in_pages(target_name)

# if customer_data:
#     print("✅ Customer Data:")
#     print(json.dumps(customer_data, indent=2))


# def fetch_customers(start_page=1, max_page=200):
#     all_customers = []
#     method = 'GET'
#     date_header = get_rfc7231_date()
#     for page in range(start_page, max_page + 1):
#         query = f'?page={page}&sort_by=name&sort_order=asc'
#         full_path = ENDPOINT + query
#         url = BASE_URL + full_path
#         auth_header = generate_hmac_header(method, full_path, date_header)
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
#             customers = data.get('customers', [])
#             if not customers:
#                 print("✅ No more data.")
#                 break
#             all_customers.extend(customers)
#         else:
#             print(f"❌ Error on page {page}: {response.status_code} - {response.text}")
#             break
#     return all_customers
# # 📦 Fetch and Save
# customers = fetch_customers(start_page=1)
# print(f"✅ Total customers fetched: {len(customers)}")
# # Optional: sort alphabetically again (in case backend didn’t do it right)
# customers.sort(key=lambda x: x.get("name", "").lower())
# # Save to JSON file
# with open("static/data/customers.json", "w", encoding="utf-8") as f:
#     json.dump(customers, f, ensure_ascii=False, indent=2)
#
# print("💾 Customers saved to customers.json")


# def fetch_purchase_orders_test():
#     method = 'GET'
#     date_header = get_rfc7231_date()
#     query = '?page=1&start_date=2025-06-10&end_date=2025-06-29'
#     full_path = ENDPOINT + query
#     url = BASE_URL + full_path
#     auth_header = generate_hmac_header(method, full_path, date_header)
#
#     headers = {
#         'Content-Type': 'application/json',
#         'Date': date_header,
#         'Authorization': auth_header
#     }
#
#     print("🔑 FULL PATH:", full_path)
#     print("🧾 Authorization Header:", headers['Authorization'])
#
#     response = requests.get(url, headers=headers)
#
#     if response.status_code == 200:
#         data = response.json()
#         print("✅ Fetched:", len(data.get('purchase_orders', [])), "orders")
#         with open('static/data/purchase_orders_10_29_jun.json', 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2, ensure_ascii=False)
#     else:
#         print(f"❌ Error: {response.status_code} - {response.text}")
#
# fetch_purchase_orders_test()


