import json, csv, re

# # Load JSON data
# with open('product_non_archived.json', 'r', encoding='utf-8') as f:
#     products = json.load(f)
#
# # Output CSV
# with open('products.csv', 'w', newline='', encoding='utf-8') as f:
#     fieldnames = ['id', 'name', 'product_code', 'showroom_qty', 'warehouse_qty',
#                   'product_categories_string', 'buy_account', 'sell_account','inventory_asset_account']
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#
#     for product in products:
#         # Extract warehouse quantities safely
#         warehouses = product.get('warehouses', {})
#         showroom_qty = warehouses.get('183271', {}).get('quantity', 0)
#         warehouse_qty = warehouses.get('183275', {}).get('quantity', 0)
#
#         writer.writerow({
#             'id': product.get('id'),
#             'name': product.get('name'),
#             'product_code': product.get('product_code'),
#             'showroom_qty': showroom_qty,
#             'warehouse_qty': warehouse_qty,
#             'product_categories_string': product.get('product_categories_string', ''),
#             'buy_account' : product.get('buy_account', {}).get('name', ''),
#             'sell_account': product.get('sell_account', {}).get('name', ''),
#             'inventory_asset_account': product.get('inventory_asset_account', {}).get('name', ''),
#         })
#
# print("✅ CSV export completed!")



import json, csv, re, itertools, pathlib

RAW_JSON = pathlib.Path("static/data/sales_orders_010323_300625.json")
OUT_CSV  = pathlib.Path("static/data/sales_orders_sample_100.csv")
MAX_ROWS = 100           # just the first 100 for testing

def clean_amount(val):
    if not val:
        return ""
    val = re.sub(r"[^\d]", "", str(val))
    return int(val) if val.isdigit() else ""

orders = []
with RAW_JSON.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line in ("[", "]", ""):
            continue                     # skip array markers / blanks
        if line.endswith(","):
            line = line[:-1]             # remove trailing comma
        try:
            orders.append(json.loads(line))
            if len(orders) >= MAX_ROWS:
                break
        except json.JSONDecodeError:
            print("⚠️  Hit incomplete JSON line; stopping read.")
            break

print(f"📦 Collected {len(orders)} valid orders.")

with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "transaction_no", "transaction_date", "customer",
        "total", "balance_due", "tags", "payments",
        "product_name", "quantity"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for order in orders:
        tags_str = "; ".join(t["name"] for t in order.get("tags", []))
        payments_str = "; ".join(
            f'{p["amount"]} via {p["payment_method_name"]}'
            for p in order.get("payments", [])
        )

        wrote_totals = False
        for ln in order.get("transaction_lines_attributes", []):
            product = ln.get("product", {})
            writer.writerow({
                "transaction_no":  order.get("transaction_no"),
                "transaction_date":order.get("transaction_date"),
                "customer":        order.get("person", {}).get("display_name", ""),
                "total":           clean_amount(order.get("original_amount_currency_format")) if not wrote_totals else "",
                "balance_due":     clean_amount(order.get("remaining_currency_format"))      if not wrote_totals else "",
                "tags":            tags_str,
                "payments":        payments_str,
                "product_name":    product.get("name", ""),
                "quantity":        ln.get("quantity", 0),
            })
            wrote_totals = True

print(f"✅ Sample CSV written → {OUT_CSV}")




# # Load JSON data
# with open('static/data/sales_orders_010323_300625.json', 'r', encoding='utf-8') as f:
#     sales_orders = json.load(f)
#
# # Function to clean and convert total to numeric
# def clean_amount(value):
#     if not value:
#         return ''
#     value = value.replace("Rp", "").replace(".", "").replace(",", "").strip()
#     try:
#         return int(value)
#     except ValueError:
#         return ''
#
# # Output CSV
# with open('static/data/sales_orders_010323_300625.csv', 'w', newline='', encoding='utf-8') as f:
#     fieldnames = ['transaction_no', 'transaction_date', 'customer', 'total', 'balance due', 'tags', 'payments', 'product_name', 'quantity' ]
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#
#     for order in sales_orders:
#         lines = order.get('transaction_lines_attributes', [])
#         wrote_total = False
#         for item in lines:
#             product = item.get('product', {})
#             writer.writerow({
#                 'transaction_no': order.get('transaction_no'),
#                 'transaction_date': order.get('transaction_date'),
#                 'customer': order.get('person', {}).get('display_name', ''),
#                 'total': clean_amount(order.get('original_amount_currency_format')) if not wrote_total else '',
#                 'balance due': clean_amount(order.get('remaining_currency_format')) if not wrote_total else '',
#                 'tags': order.get('tags'),
#                 'payments': order.get('payments', {}).get('payment_method_name', ''),
#                 'product_name': product.get('name', ''),
#                 'quantity': item.get('quantity', 0),
#
#             })
#             wrote_total = True
#
# print("✅ CSV export completed with one numeric total per transaction!")


# # Load JSON data
# with open('purchase_orders_10_29_jun.json', 'r', encoding='utf-8') as f:
#     purchase = json.load(f)

# # Output CSV
# with open('purchase_10_29_jun.csv', 'w', newline='', encoding='utf-8') as f:
#     fieldnames = ['transaction_no', 'display_name', 'product_code', 'name', 'quantity',
#                   'description']
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#
#     for purchase in purchases:
#         # Extract warehouse quantities safely
#         warehouses = product.get('warehouses', {})
#         showroom_qty = warehouses.get('183271', {}).get('quantity', 0)
#         warehouse_qty = warehouses.get('183275', {}).get('quantity', 0)
#
#         writer.writerow({
#             'id': product.get('id'),
#             'name': product.get('name'),
#             'product_code': product.get('product_code'),
#             'showroom_qty': showroom_qty,
#             'warehouse_qty': warehouse_qty,
#             'product_categories_string': product.get('product_categories_string', ''),
#             'buy_account' : product.get('buy_account', {}).get('name', ''),
#             'sell_account': product.get('sell_account', {}).get('name', ''),
#             'inventory_asset_account': product.get('inventory_asset_account', {}).get('name', ''),
#         })
#
# print("✅ PO CSV export completed!")


# # Load JSON data
# with open('static/data/sales_orders_May2025.json', 'r', encoding='utf-8') as f:
#     sales_orders = json.load(f)
#
# # Function to clean and convert total to numeric
# def clean_amount(value):
#     if not value:
#         return ''
#     value = value.replace("Rp", "").replace(".", "").replace(",", "").strip()
#     try:
#         return int(value)
#     except ValueError:
#         return ''
#
# # Output CSV
# with open('static/data/customers020725.csv', 'w', newline='', encoding='utf-8') as f:
#     fieldnames = ['id', 'display_name', 'mobile', 'email', 'created_at', 'billing_address', 'address']
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#
#     for order in sales_orders:
#         lines = order.get('transaction_lines_attributes', [])
#         wrote_total = False
#         for item in lines:
#             product = item.get('product', {})
#             writer.writerow({
#                 'transaction_no': order.get('transaction_no'),
#                 'transaction_date': order.get('transaction_date'),
#                 'customer': order.get('person', {}).get('display_name', ''),
#                 'product_name': product.get('name', ''),
#                 'quantity': item.get('quantity', 0),
#                 'total': clean_amount(order.get('original_amount_currency_format')) if not wrote_total else ''
#             })
#             wrote_total = True
#
# print("✅ CSV export completed with one numeric total per transaction!")