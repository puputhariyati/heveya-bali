import requests
import hashlib
import base64
import hmac
import json
import csv
from email.utils import formatdate
from collections import defaultdict


# Mekari credentials
CLIENT_ID = 'afaku9tq7KET9tMm'
CLIENT_SECRET = '8qTvnRqnasNwCRjf0ocpUlgxkfVN4TBX'
BASE_URL = 'https://api.mekari.com'
ENDPOINT = '/public/jurnal/api/v1/sales_invoices'

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

def format_rupiah(amount):
    return f"Rp. {int(amount):,}".replace(",", ".")

def sales_invoices():
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
    params = {
        'status': 'paid',
        'page': 1
    }
    paid_invoices = []

    while True:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        invoices = data.get('sales_invoices', [])
        if not invoices:
            break

        paid_invoices.extend(invoices)
        print(f"✅ Fetched {len(invoices)} invoices from page {params['page']}")

        params['page'] += 1  # Go to next page

    customer_totals = defaultdict(float)
    customer_names = {}

    for invoice in paid_invoices:
        person = invoice.get('person')
        if person:
            person_id = person.get('id')
            display_name = person.get('display_name', 'Unknown')
            payment_amount_str = invoice.get('payment_received_amount', '0')
            payment_amount = float(payment_amount_str)

            customer_totals[person_id] += payment_amount
            customer_names[person_id] = display_name
        else:
            print(f"❗ Skipped invoice without person info: {invoice}")

    # Sort customers alphabetically
    sorted_customers = sorted(customer_totals.items(), key=lambda x: customer_names.get(x[0], ''))

    # Export to CSV
    with open('customer_total_payments.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['No', 'Customer Name', 'Customer ID', 'Total Payment (formatted)', 'Total Payment (raw)'])

        for idx, (person_id, total_payment) in enumerate(sorted_customers, start=1):
            display_name = customer_names.get(person_id, 'Unknown')
            formatted_payment = format_rupiah(total_payment)
            writer.writerow([idx, display_name, person_id, formatted_payment, total_payment])

            # Print too
            print(f"{idx}. {display_name} (ID {person_id}) total paid: {formatted_payment}")

    print("\n📁 Exported to 'customer_total_payments.csv' successfully!")

#     print("📤 Sending GET to:", url)
#     print("🧾 Headers:", headers)
#
#     response = requests.get(url, headers=headers)
#
#     if response.status_code == 200:
#         return response.json()  # Return the parsed JSON, not print it yet
#     else:
#         print(f"❌ Error {response.status_code}:", response.text)
#         return None
#
# Fetch the data
data = sales_invoices()

# ✅ Pretty print the JSON only if data is returned
if data:
    print("✅ Formatted Response:")
    print(json.dumps(data, indent=2))
