import sqlite3

# Connect to your database
conn = sqlite3.connect("main.db")
cursor = conn.cursor()

# # ✅ Clear the table first
# cursor.execute("DELETE FROM sales_order_detail")
# deleted_rows = cursor.rowcount
# print(f"🗑️ Deleted {deleted_rows} existing rows from sales_order_detail")
# conn.commit()
# conn.close()


#
# # Delete table from the stock table
# cursor.execute("DROP TABLE IF EXISTS inventory;")
#
# # Delete all rows from the BOM Table
# cursor.execute("DELETE FROM bom;")
#
# # # Reset auto-increment ID (optional)
# # cursor.execute("DELETE FROM sqlite_sequence WHERE name='inventory';")
#
# # Commit changes and close connection
# conn.commit()
# conn.close()
#
# print("Stock database has been cleared.")

# Add Column into existing table
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
# cursor.execute("ALTER TABLE sales_order_detail ADD COLUMN description TEXT")
# conn.commit()
# conn.close()
#
# To see what tables list in my main.db
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
#
# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
# tables = cursor.fetchall()
#
# for table in tables:
#     print(table[0])
#
# conn.close()

# Export your SQLite tables to .csv
import pandas as pd
# Export each table
for table in ["sales_quotes"]:
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    df.to_csv(f"{table}.csv", index=False)
conn.close()

# # Run a quick count test
# cursor.execute("SELECT COUNT(*) FROM sales_order_detail")
# count = cursor.fetchone()[0]
# print("Total rows in sales_order_detail:", count)
