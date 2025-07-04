import json, csv, re, pathlib

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


# # Load JSON data
# with open('static/data/sales_invoices_2022_0106.json', 'r', encoding='utf-8') as f:
#     sales_invoices = json.load(f)
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
# with open('static/data/sales_invoices_2022_0106.csv', 'w', newline='', encoding='utf-8') as f:
#     fieldnames = ['transaction_no', 'transaction_date', 'customer', 'total', 'balance due',
#                   'tags', 'payments', 'product_name', 'quantity' ]
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#
#     for order in sales_invoices:
#         lines = order.get('transaction_lines_attributes', [])
#         payment_methods = ", ".join(
#             p.get("payment_method_name", "")  # take the name
#             for p in order.get("payments", [])  # iterate payments
#             if p.get("payment_method_name")  # keep only truthy
#         )
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
#                 'payments': payment_methods,
#                 'product_name': product.get('name', ''),
#                 'quantity': item.get('quantity', 0),
#
#             })
#             wrote_total = True
#
# print("✅ CSV export completed with one numeric total per transaction!")

#
# # ── 1.  paths to your yearly JSON files ──────────────────────────
# json_files = [
#     "static/data/sales_invoices_2022_0106.json",
#     "static/data/sales_invoices_2022_0712.json",
#     "static/data/sales_invoices_2023_0106.json",
#     "static/data/sales_invoices_2023_0712.json",
#     "static/data/sales_invoices_2024_0106.json",
#     "static/data/sales_invoices_2024_0712.json"
# ]
#
# # ── 2.  load & concat all invoices ───────────────────────────────
# sales_invoices = []
# for fp in json_files:
#     path = pathlib.Path(fp)
#     if not path.exists():
#         print(f"⚠️  {fp} not found – skipping")
#         continue
#     with path.open("r", encoding="utf-8") as f:
#         try:
#             sales_invoices.extend(json.load(f))
#             print(f"📥  Loaded {fp} – {len(sales_invoices)} total so far")
#         except json.JSONDecodeError as e:
#             print(f"❌  {fp} is not valid JSON: {e}")
#
# # ── 3.  helper to clean "Rp 1.234.567" → 1234567  -----------------
# def clean_amount(val):
#     if not val:
#         return ""
#     num = re.sub(r"[^\d]", "", str(val))
#     return int(num) if num.isdigit() else ""
#
# # ── 4.  write combined CSV  --------------------------------------
# out_csv = "static/data/sales_invoices_2022_2024.csv"
# fieldnames = [
#     "transaction_no", "transaction_date", "customer",
#     "total", "balance_due",
#     "tags", "payment_methods",
#     "product_name", "quantity"
# ]
#
# with open(out_csv, "w", newline="", encoding="utf-8") as f:
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#
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
# print(f"✅  CSV export completed → {out_csv}")



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



import os

file_path = "static/data/sales_invoices_2022_2024.csv"
size_bytes = os.path.getsize(file_path)
size_mb = size_bytes / (1024 * 1024)

print(f"📦 File size: {size_mb:.2f} MB")
