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

# Check contents of 'bom' table
cursor.execute("SELECT * FROM bom")
bom_data = cursor.fetchall()

print("\n📌 BOM Table Data:")
for row in bom_data:
    print(row)

# Check if 'bom' table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bom'")
table_exists = cursor.fetchone()
if table_exists:
    print("✅ BOM table exists.")
else:
    print("❌ BOM table does NOT exist.")

# Check BOM Table Structure
cursor.execute("PRAGMA table_info(bom)")
columns = cursor.fetchall()
print("\n📌 BOM Table Structure:", columns)

# Check If BOM Table Has Data
cursor.execute("SELECT COUNT(*) FROM bom")
row_count = cursor.fetchone()[0]
print(f"\n📌 BOM Table Row Count: {row_count}")


conn.close()
