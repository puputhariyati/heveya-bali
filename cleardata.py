import sqlite3

# Connect to your database
conn = sqlite3.connect("stock.db")
cursor = conn.cursor()

# Delete all rows from the stock table
cursor.execute("DELETE FROM inventory;")

# Reset auto-increment ID (optional)
cursor.execute("DELETE FROM sqlite_sequence WHERE name='inventory';")

# Commit changes and close connection
conn.commit()
conn.close()

print("Stock database has been cleared.")
