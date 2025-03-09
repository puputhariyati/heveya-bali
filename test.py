import sqlite3

conn = sqlite3.connect("stock.db")
cursor = conn.cursor()

# Check contents of 'inventory' table
cursor.execute("SELECT * FROM inventory")
inventory_data = cursor.fetchall()
print("\n📌 Inventory Table Data:")
for row in inventory_data:
    print(row)

# Check contents of 'products' table
cursor.execute("SELECT * FROM products")
products_data = cursor.fetchall()
print("\n📌 Products Table Data:")
for row in products_data:
    print(row)

conn.close()
