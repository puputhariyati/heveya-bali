import requests
import hashlib
import base64
import hmac
from email.utils import formatdate
from datetime import datetime
from collections import defaultdict

# Mekari credentials
CLIENT_ID = 'afaku9tq7KET9tMm'
CLIENT_SECRET = '8qTvnRqnasNwCRjf0ocpUlgxkfVN4TBX'
BASE_URL = 'https://api.mekari.com'
ENDPOINT = '/public/jurnal/api/v1/sales_orders'

# HMAC + Date header helpers
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

# GET request
def get_sales_orders():
    method = 'GET'
    full_path = ENDPOINT
    url = BASE_URL + full_path
    date_header = get_rfc7231_date()
    auth_header = generate_hmac_header(method, full_path, date_header)

    headers = {
        'Content-Type': 'application/json',
        'Date': date_header,
        'Authorization': auth_header
    }

    print("📤 Fetching sales orders from:", url)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return None

# Filter by date >= 2025-04-17
def filter_orders_by_date(sales_data):
    threshold_date = datetime.strptime("2025-04-20", "%Y-%m-%d")
    filtered = []

    for order in sales_data.get("sales_orders", []):
        try:
            order_date = datetime.strptime(order["transaction_date"], "%d/%m/%Y")
            if order_date >= threshold_date:
                filtered.append(order)
        except Exception as e:
            print(f"⚠️ Skipping order due to date error: {e}")

    return {"sales_orders": filtered}

# Extract essential fields
def extract_relevant_sales_orders(filtered_data):
    simplified_orders = []

    for order in filtered_data.get("sales_orders", []):
        simplified = {
            "id": order["id"],
            "transaction_no": order["transaction_no"],
            "transaction_date": order["transaction_date"],
            "products": []
        }

        for invoice in order.get("sales_invoices", []):
            for line in invoice.get("transaction_lines_attributes", []):
                product = line.get("product")
                if product:
                    simplified["products"].append({
                        "name": product.get("name", "Unnamed Product"),
                        "quantity": product.get("quantity", 0)
                    })
                else:
                    print(f"⚠️ Missing product info in invoice of order #{order['transaction_no']}")

        simplified_orders.append(simplified)

    return simplified_orders


# Main run
if __name__ == "__main__":
    data = get_sales_orders()

    if data:
        filtered = filter_orders_by_date(data)
        simplified = extract_relevant_sales_orders(filtered)

        # print("\n✅ Orders from April 17, 2025 onward:")
        # for order in simplified:
        #     print(f"\n🧾 Order #{order['transaction_no']} on {order['transaction_date']}")
        #     for p in order["products"]:
        #         print(f"   📦 {p['name']} (Qty: {p['quantity']})")

        # Group by transaction_date
        grouped_by_date = defaultdict(list)
        for order in simplified:
            grouped_by_date[order["transaction_date"]].append(order)

        print("\n✅ Orders from April 20, 2025 onward:\n")

        for date in sorted(grouped_by_date.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y")):
            print(f"📅 Date {date}")
            for order in grouped_by_date[date]:
                print(f"🧾 Order #{order['transaction_no']}")
                for p in order["products"]:
                    print(f"   {p['name']}, {p['quantity']}")
            print()  # extra spacing between dates