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
# ENDPOINT = '/public/jurnal/api/v1/sales_invoices'
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

def fetch_and_save_sales_invoices_csv(filename='sales_invoices_jun2025.csv', start_page=1):
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


                    for order in sales_invoices:
                        # flatten tags & payments once per invoice
                        tags_list = order.get("tags") or []
                        tags_str = "; ".join(t.get("name", "") for t in tags_list if isinstance(t, dict) and t.get("name"))
                        payment_methods = ", ".join(
                            p.get("payment_method_name", "")
                            for p in order.get("payments", [])
                            if p.get("payment_method_name")
                        )
                        wrote_total = False
                        for line in order.get("transaction_lines_attributes", []):
                            product = line.get("product", {})
                            writer.writerow({
                                "transaction_no" : order.get("transaction_no"),
                                "transaction_date": order.get("transaction_date"),
                                "customer"       : order.get("person", {}).get("display_name", ""),
                                "total"          : clean_amount(order.get("original_amount_currency_format")) if not wrote_total else "",
                                "balance_due"    : clean_amount(order.get("remaining_currency_format"))      if not wrote_total else "",
                                "tags"           : tags_str,
                                "payment_methods": payment_methods,
                                "product_name"   : product.get("name", ""),
                                "quantity"       : line.get("quantity", 0),
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


# def fetch_and_save_sales_order_csv(filename='sales_orders_jun2025.csv', start_page=1):
#     page = start_page
#     more_pages = True
#     first_write = page == 1  # Write header only if starting fresh
#     method = 'GET'
#     date_header = get_rfc7231_date()
#
#     with open(filename, 'a', newline='', encoding='utf-8') as f:
#         fieldnames = ['transaction_no', 'transaction_date', 'customer', 'product_code', 'product_name', 'quantity', 'total']
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#
#         if first_write:
#             writer.writeheader()
#
#         while more_pages:
#             query = f'?start_date=2025-06-01&end_date=2025-06-30&page={page}&sort_by=transaction_date&sort_order=asc'
#
#             full_path = ENDPOINT + query
#             url = BASE_URL + full_path
#             auth_header = generate_hmac_header(method, full_path, date_header)
#
#             headers = {
#                 'Content-Type': 'application/json',
#                 'Date': date_header,
#                 'Authorization': auth_header
#             }
#
#             print(f"🔄 Fetching page {page}...")
#             response = requests.get(url, headers=headers)
#
#             if response.status_code == 200:
#                 data = response.json()
#                 sales_orders = data.get('sales_orders', [])
#
#                 if not sales_orders:
#                     print(f"✅ No more sales order at page {page}")
#                     break
#
#                 # Function to clean and convert total to numeric
#                 def clean_amount(value):
#                     if not value:
#                         return ''
#                     value = value.replace("Rp", "").replace(".", "").replace(",", "").strip()
#                     try:
#                         return int(value)
#                     except ValueError:
#                         return ''
#
#                 for order in sales_orders:
#                     lines = order.get('transaction_lines_attributes', [])
#                     wrote_total = False
#                     for item in lines:
#                         product = item.get('product', {})
#                         writer.writerow({
#                             'transaction_no': order.get('transaction_no'),
#                             'transaction_date': order.get('transaction_date'),
#                             'customer': order.get('person', {}).get('display_name', ''),
#                             'product_code': product.get('product_code', ''),
#                             'product_name': product.get('name', ''),
#                             'quantity': item.get('quantity', 0),
#                             'total': clean_amount(
#                                 order.get('original_amount_currency_format')) if not wrote_total else ''
#                         })
#                         wrote_total = True


                #     for order in sales_invoices:
                #         # flatten tags & payments once per invoice
                #         tags_list = order.get("tags") or []
                #         tags_str = "; ".join(t.get("name", "") for t in tags_list if isinstance(t, dict) and t.get("name"))
                #         payment_methods = ", ".join(
                #             p.get("payment_method_name", "")
                #             for p in order.get("payments", [])
                #             if p.get("payment_method_name")
                #         )
                #         wrote_total = False
                #         for line in order.get("transaction_lines_attributes", []):
                #             product = line.get("product", {})
                #             writer.writerow({
                #                 "transaction_no" : order.get("transaction_no"),
                #                 "transaction_date": order.get("transaction_date"),
                #                 "customer"       : order.get("person", {}).get("display_name", ""),
                #                 "total"          : clean_amount(order.get("original_amount_currency_format")) if not wrote_total else "",
                #                 "balance_due"    : clean_amount(order.get("remaining_currency_format"))      if not wrote_total else "",
                #                 "tags"           : tags_str,
                #                 "payment_methods": payment_methods,
                #                 "product_name"   : product.get("name", ""),
                #                 "quantity"       : line.get("quantity", 0),
                #             })
                #             wrote_total = True


#
#                 print(f"✅ Page {page} saved ({len(sales_orders)} sales orders)")
#                 page += 1
#             elif response.status_code == 429:
#                 print(f"🚫 Rate limit hit at page {page}. Try again later.")
#                 break
#             else:
#                 print(f"❌ Failed at page {page}: {response.status_code} - {response.text}")
#                 break
#
#     print(f"✅ Finished saving to: {filename}")
#     print(f"✅ Total sales orders fetched: {len(sales_orders)}")
#
# # Run it
# fetch_and_save_sales_order_csv()

# def fetch_specific_sales_orders(transaction_nos, filename='specific_sales_orders.csv'):
#     method = 'GET'
#     date_header = get_rfc7231_date()
#
#     with open(filename, 'w', newline='', encoding='utf-8') as f:
#         fieldnames = ['transaction_no', 'transaction_date', 'customer', 'product_code', 'product_name', 'quantity', 'total']
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         writer.writeheader()
#
#         for trans_no in transaction_nos:
#             endpoint = f"/public/jurnal/api/v1/sales_orders/{trans_no}"
#             full_path = endpoint
#             url = BASE_URL + full_path
#             auth_header = generate_hmac_header(method, full_path, date_header)
#
#             headers = {
#                 'Content-Type': 'application/json',
#                 'Date': date_header,
#                 'Authorization': auth_header
#             }
#
#             print(f"🔍 Fetching sales order {trans_no}...")
#             response = requests.get(url, headers=headers)
#
#             if response.status_code == 200:
#                 order = response.json().get('sales_order', {})
#
#                 # Function to clean and convert total to numeric
#                 def clean_amount(value):
#                     if not value:
#                         return ''
#                     value = value.replace("Rp", "").replace(".", "").replace(",", "").strip()
#                     try:
#                         return int(value)
#                     except ValueError:
#                         return ''
#
#                 lines = order.get('transaction_lines_attributes', [])
#                 wrote_total = False
#                 for item in lines:
#                     product = item.get('product', {})
#                     writer.writerow({
#                         'transaction_no': order.get('transaction_no'),
#                         'transaction_date': order.get('transaction_date'),
#                         'customer': order.get('person', {}).get('display_name', ''),
#                         'product_code': product.get('product_code', ''),
#                         'product_name': product.get('name', ''),
#                         'quantity': item.get('quantity', 0),
#                         'total': clean_amount(order.get('original_amount_currency_format')) if not wrote_total else ''
#                     })
#                     wrote_total = True
#             else:
#                 print(f"❌ Failed to fetch {trans_no}: {response.status_code} - {response.text}")
#
#     print(f"✅ Finished saving {len(transaction_nos)} sales orders to: {filename}")
# transaction_nos = ['10325', '12896', '13102', '13104', '13070', '13271']
# fetch_specific_sales_orders(transaction_nos)


# # helpers
# CHECKPOINT_FILE        = "last_page.txt"
# CSV_PATH               = "static/data/customers_orders.csv"
# BATCH_SIZE             = 5          # ⬅️  save/flush every 500 customers
# MAX_PAGES              = 5          # safety cap
#
# def format_rupiah(amount):
#     return f"Rp. {amount:,.0f}".replace(",", ".")
#
# def format_date(date_string):
#     try:
#         dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")
#         return dt.strftime("%d %b %Y")  # Example: 02 Jul 2025
#     except:
#         return date_string  # fallback
#
# # ------------------------------------------------------------------
# # ─────  SALES‑ORDER TOTALS (one‑off)  ─────────────────────────────
# # ------------------------------------------------------------------
# def fetch_sales_order_totals():
#     totals, params = defaultdict(float), {"page": 1}
#     date_hdr = get_rfc7231_date()
#     while True:
#         full = f"{SALES_ORDERS_ENDPOINT}"
#         url  = BASE_URL + full
#         hdrs = {
#             "Date": date_hdr,
#             "Authorization": generate_hmac_header("GET", full, date_hdr),
#             "Content-Type": "application/json",
#         }
#         res = requests.get(url, headers=hdrs, params=params)
#         data = res.json()
#         orders = data.get("sales_orders", [])
#         if not orders:
#             break
#         for o in orders:
#             p = o.get("person") or {}
#             totals[p.get("id")] += float(o.get("total", 0))
#         print(f"✅ orders: page {params['page']}, fetched {len(orders)}")
#         params["page"] += 1
#     return totals
# # ------------------------------------------------------------------
# # ─────  CUSTOMER BATCH GENERATOR  ─────────────────────────────────
# # ------------------------------------------------------------------
# def customer_batches(start_page=1):
#     date_hdr = get_rfc7231_date()
#     page, collected = start_page, []
#     while page <= MAX_PAGES:
#         query = f"?page={page}&sort_by=name&sort_order=asc"
#         full  = CUSTOMER_ENDPOINT + query
#         url   = BASE_URL + full
#         hdrs  = {
#             "Date": date_hdr,
#             "Authorization": generate_hmac_header("GET", full, date_hdr),
#             "Content-Type": "application/json",
#         }
#         res = requests.get(url, headers=hdrs)
#         if res.status_code != 200:
#             print(f"❌ page {page}: {res.status_code} – {res.text}")
#             break
#         cust = res.json().get("customers", [])
#         if not cust:
#             break
#         collected.extend(cust)
#         print(f"✅ customers page {page}: {len(cust)}")
#         page += 1
#         # yield a full batch
#         if len(collected) >= BATCH_SIZE:
#             yield collected, page
#             collected = []
#     # yield remaining (if any)
#     if collected:
#         yield collected, page
# # ------------------------------------------------------------------
# # ─────  MAIN  ─────────────────────────────────────────────────────
# # ------------------------------------------------------------------
# def main():
#     # 1⃣  Read checkpoint (if any)
#     start_page = 1
#     if os.path.exists(CHECKPOINT_FILE):
#         with open(CHECKPOINT_FILE) as f:
#             try:
#                 start_page = int(f.read().strip())
#             except ValueError:
#                 pass
#     print(f"▶️  Resuming from page {start_page}")
#
#     # 2⃣  Fetch sales‑order totals once
#     totals = fetch_sales_order_totals()
#
#     # 3⃣  Stream customers in batches
#     first_write = not os.path.exists(CSV_PATH)
#     for batch, next_page in customer_batches(start_page):
#         rows = []
#         for c in batch:
#             cid  = c.get("id")
#             rows.append({
#                 "id": cid,
#                 "display_name": c.get("display_name",""),
#                 "mobile":       c.get("mobile",""),
#                 "email":        c.get("email",""),
#                 "created_at":   format_date(c.get("created_at","")),
#                 "billing_address": c.get("billing_address", ""),
#                 "address": c.get("address", ""),
#                 "total_purchase":  format_rupiah(totals.get(cid,0)),
#             })
#
#         # 4⃣  Append chunk to CSV
#         mode = "a" if os.path.exists(CSV_PATH) else "w"
#         with open(CSV_PATH, mode, newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(f, fieldnames=rows[0].keys())
#             if first_write:
#                 writer.writeheader()
#                 first_write = False
#             writer.writerows(rows)
#         print(f"💾 Wrote {len(rows)} customers to {CSV_PATH}")
#
#         # 5⃣  Update checkpoint
#         with open(CHECKPOINT_FILE, "w") as f:
#             f.write(str(next_page))
#         print(f"📌 Checkpoint saved (next page {next_page})")
#
#     # 6⃣  Done – remove checkpoint
#     if os.path.exists(CHECKPOINT_FILE):
#         os.remove(CHECKPOINT_FILE)
#     print("🏁 Completed without errors.")

# ------------------------------------------------------------------
if __name__ == "__main__":
    main()