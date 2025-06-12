import json
import csv

# Load the JSON file (a list of product dicts)
with open('product_non_archived.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Choose the fields you want in the CSV
fields = ['name', 'product_code', 'showroom_qty', 'warehouse_qty']

# Write to CSV
with open('products.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for product in products:
        writer.writerow({field: product.get(field, '') for field in fields})

print("✅ Converted product_non_archived.json to products.csv")
