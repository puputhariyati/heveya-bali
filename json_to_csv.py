import json
import csv

# Load JSON data
with open('product_non_archived.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Output CSV
with open('products.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['id', 'name', 'product_code', 'showroom_qty', 'warehouse_qty',
                  'product_categories_string', 'buy_account', 'sell_account','inventory_asset_account']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for product in products:
        # Extract warehouse quantities safely
        warehouses = product.get('warehouses', {})
        showroom_qty = warehouses.get('183271', {}).get('quantity', 0)
        warehouse_qty = warehouses.get('183275', {}).get('quantity', 0)

        writer.writerow({
            'id': product.get('id'),
            'name': product.get('name'),
            'product_code': product.get('product_code'),
            'showroom_qty': showroom_qty,
            'warehouse_qty': warehouse_qty,
            'product_categories_string': product.get('product_categories_string', ''),
            'buy_account' : product.get('buy_account', {}).get('name', ''),
            'sell_account': product.get('sell_account', {}).get('name', ''),
            'inventory_asset_account': product.get('inventory_asset_account', {}).get('name', ''),
        })

print("✅ CSV export completed!")
