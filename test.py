import sqlite3

conn = sqlite3.connect("stock.db")
cursor = conn.cursor()

# Check contents of 'inventory' table
cursor.execute("SELECT * FROM inventory")
inventory_data = cursor.fetchall()
print("\n📌 Inventory Table Data:")
for row in inventory_data:
    print(row)

# Check existing columns
cursor.execute("PRAGMA table_info(inventory);")
columns = cursor.fetchall()
print("\n Existing Columns:", columns)

conn.close()
