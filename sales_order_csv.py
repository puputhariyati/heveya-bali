import json
import csv

# Load JSON data
with open('sales_orders_May2025.json', 'r', encoding='utf-8') as f:
    sales_orders = json.load(f)

# Function to clean and convert total to numeric
def clean_amount(value):
    if not value:
        return ''
    value = value.replace("Rp", "").replace(".", "").replace(",", "").strip()
    try:
        return int(value)
    except ValueError:
        return ''

# Output CSV
with open('sales_orders_may2025.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['transaction_no', 'transaction_date', 'customer', 'product_name', 'quantity', 'total']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for order in sales_orders:
        lines = order.get('transaction_lines_attributes', [])
        wrote_total = False
        for item in lines:
            product = item.get('product', {})
            writer.writerow({
                'transaction_no': order.get('transaction_no'),
                'transaction_date': order.get('transaction_date'),
                'customer': order.get('person', {}).get('display_name', ''),
                'product_name': product.get('name', ''),
                'quantity': item.get('quantity', 0),
                'total': clean_amount(order.get('original_amount_currency_format')) if not wrote_total else ''
            })
            wrote_total = True

print("✅ CSV export completed with one numeric total per transaction!")
