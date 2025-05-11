import requests
import hashlib
import base64
import hmac
import json
from email.utils import formatdate
from datetime import datetime
import time

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

def get_products():
    method = 'GET'
    query = ''
    full_path = ENDPOINT + query
    url = BASE_URL + full_path

    date_header = get_rfc7231_date()
    auth_header = generate_hmac_header(method, full_path, date_header)

    headers = {
        'Content-Type': 'application/json',
        'Date': date_header,
        'Authorization': auth_header
    }

    skus = ["SSW2SK200X200FI", "SSS2SK200X200FI", "SSG2SK200X200FI", "SSDG2SK200X200FI", "SSSG2SK200X200FI",
            "SSMG2SK200X200FI", "SSBM2SK200X200FI", "SSBO2SK200X200FI", "SSL2SK200X200FI",
            "SSW2K200X180FI", "SSS2K200X180FI", "SSG2K200X180FI", "SSDG2K200X180FI", "SSSG2K180X200FI",
            "SSMG2K180X200FI", "SSBM2K180X200FI", "SSBO2K180X200FI", "SSL2K200X180FI",
            "SSW2Q200X160FI", "SSS2Q200X160FI", "SSG2Q200X160FI", "SSDG2Q200X160FI", "SSSG2Q200X160FI",
            "SSMG2Q200X160FI", "SSBM2Q160X200FI", "SSBO2Q160X200FI",
            "SSW1S200X90FI", "SSS1S200X90FI", "SSG1S200X90FI", "SSDG1S200X90FI", "SSSG1S200X90FI", "SSMG1S200X90FI",
            "SSMG1S200X90FI", "SSBM1S200X90FI"]  # List of SKUs to query
    all_products = []  # List to store products from all SKUs

    for sku in skus:
        params = {
            "keyword": sku,
            "page": 1,
            "type": "product"
        }

        # print(f"📤 Sending GET request for SKU: {sku} to:", url)
        # print("🧾 Headers:", headers)

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if 'products' in data:
                all_products.extend(data['products'])  # Add products to the all_products list
        else:
            print(f"❌ Error {response.status_code} for SKU {sku}:", response.text)
        time.sleep(1)

    # 🛠️ Important: Return the same structure as Mekari API
    return {
        "products": all_products,
        "total_count": len(all_products),
        "before_filter_count": len(all_products),
        "current_page": 1,
        "total_pages": 1
    }
#
# <<<<<<< HEAD
#
# # Fetch the data
# # data = get_products()
#
# # ✅ Pretty print the JSON only if data is returned
# # if data:
# #     print("✅ Formatted Response:")
# #     # print(json.dumps(data, indent=2))
# =======
# #
# # # Fetch the data
# # data = get_products()
# #
# # # ✅ Pretty print the JSON only if data is returned
# # if data:
# #     print("✅ Formatted Response:")
# #     print(json.dumps(data, indent=2))
# >>>>>>> temp-fix

# # ✅ Get the newest (latest) sales order by transaction_date
# if data and "sales_orders" in data and data["sales_orders"]:
#     try:
#         # Convert to list of tuples (parsed_date, order)
#         orders_with_dates = [
#             (datetime.strptime(order["transaction_date"], "%d/%m/%Y"), order)
#             for order in data["sales_orders"]
#         ]
#
#         # Sort by date descending, get the latest
#         latest_order = sorted(orders_with_dates, key=lambda x: x[0], reverse=True)[0][1]
#
#         print("✅ Latest Sales Order:")
#         print(json.dumps(latest_order, indent=2))
#
#     except Exception as e:
#         print(f"⚠️ Error parsing dates: {e}")
# else:
#     print("⚠️ No sales orders found.")

# # ✅ Get the newest (latest) sales order by transaction_date
# if data and "product" in data and data["product"]:
#     try:
#         # Convert to list of tuples (parsed_date, order)
#         orders_with_dates = [
#             (datetime.strptime(order["transaction_date"], "%d/%m/%Y"), order)
#             for order in data["sales_orders"]
#         ]
#
#         # Sort by date descending, get the latest
#         latest_order = sorted(orders_with_dates, key=lambda x: x[0], reverse=True)[0][1]
#
#         # ✅ Simplify the sales order to include only transaction info and products
#         simplified_order = {
#             "transaction_no": latest_order["transaction_no"],
#             "transaction_date": latest_order["transaction_date"],
#             "products": []
#         }
#
#         for line in latest_order.get("transaction_lines_attributes", []):
#             product = line.get("product")
#             if product:
#                 simplified_order["products"].append({
#                     "name": product.get("name"),
#                     # "quantity": product.get("quantity") #product stock qty
#                     "quantity": line.get("quantity")
#                 })
#
#         print("✅ Simplified Sales Order:")
#         print(json.dumps(simplified_order, indent=2))
#
#     except Exception as e:
#         print(f"⚠️ Error parsing or simplifying data: {e}")
# else:
#     print("⚠️ No sales orders found.")
