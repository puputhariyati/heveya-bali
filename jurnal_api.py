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

def get_sales_orders():
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

    print("📤 Sending GET to:", url)
    print("🧾 Headers:", headers)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Return the parsed JSON, not print it yet
    else:
        print(f"❌ Error {response.status_code}:", response.text)
        return None

# Fetch the data
#data = get_sales_orders()

# # ✅ Pretty print the JSON only if data is returned
# if data:
#     print("✅ Formatted Response:")
#     print(json.dumps(data, indent=2))

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

# ✅ Get the newest (latest) sales order by transaction_date
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
