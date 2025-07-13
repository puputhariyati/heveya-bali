import sqlite3, os
from pathlib import Path

DATABASE = Path(__file__).parent / "main.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# def init_db():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     # Example: your new sales_order_detail table
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS sales_order_detail (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             transaction_no TEXT,
#             line INTEGER,
#             item TEXT,
#             qty INTEGER,
#             unit TEXT,
#             delivered INTEGER DEFAULT 0,
#             remain_qty INTEGER,
#             po_no TEXT,
#             warehouse_option TEXT,
#             delivery_date TEXT,
#             status TEXT
#         )
#     """)
#
#     conn.commit()
#     conn.close()

    # # Create sales_order table if it doesn't exist
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS sales_order (
    #     transaction_no TEXT PRIMARY KEY,
    #     transaction_date TEXT,
    #     customer TEXT,
    #     balance_due TEXT,
    #     total TEXT,
    #     status TEXT,
    #     etd TEXT
    # )
    # """)
    # conn.commit()
    # conn.close()
    # print("✅ sales_order table created.")

# # Add New Column, SQLite can only added 1 column each, cannot multiple
# conn = sqlite3.connect("main.db")
# cursor = conn.cursor()
#
# # Add new columns
# # cursor.execute("ALTER TABLE sales_order ADD COLUMN po_no TEXT")
# # cursor.execute("ALTER TABLE sales_order ADD COLUMN tags TEXT")
# cursor.execute("ALTER TABLE sales_order ADD COLUMN payment TEXT")
#
# conn.commit()
# conn.close()
# print("✅ Column added to sales_order table.")

    # # Create only the new sales_order_detail table or any others you need
    # def init_db():
    #     conn = get_db_connection()
    #     cursor = conn.cursor()
    #     # Example: your new sales_order_detail table
    #     cursor.execute("""
    #         CREATE TABLE IF NOT EXISTS sales_order_detail (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             transaction_no TEXT,
    #             line INTEGER,
    #             item TEXT,
    #             qty INTEGER,
    #             unit TEXT,
    #             delivered INTEGER DEFAULT 0,
    #             remain_qty INTEGER,
    #             po_no TEXT,
    #             warehouse_option TEXT,
    #             delivery_date TEXT,
    #             status TEXT
    #         )
    #     """)
    #     conn.commit()
    #     conn.close()
    # print("✅ sales_order_detail table created.")

    # conn = sqlite3.connect('main.db')
    # cursor = conn.cursor()
    #
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS sales_quotes (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     date TEXT,
    #     customer TEXT,
    #     phone TEXT,
    #     full_amount REAL,
    #     discount REAL,
    #     avg_disc REAL,
    #     grand_total REAL,
    #     margin REAL,
    #     status TEXT,
    #     ETD TEXT
    # )
    # ''')
    #
    # conn.commit()
    # conn.close()
    # print("✅ Table 'sales_quotes' created.")

    # # Update DB in sales_quotes table to add a quote_no column
    # import sqlite3
    #
    # conn = sqlite3.connect('main.db')
    # cursor = conn.cursor()
    #
    # cursor.execute('''
    #     ALTER TABLE sales_quotes ADD COLUMN quote_no TEXT
    # ''')
    #
    # conn.commit()
    # conn.close()
    # print("✅ Added quote_no column to sales_quotes table")

    # conn = sqlite3.connect('main.db')
    # cursor = conn.cursor()
    #
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS sales_quote_items (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     quote_id INTEGER,
    #     description TEXT,
    #     qty REAL,
    #     unit TEXT,
    #     unit_price REAL,
    #     discount REAL,
    #     discounted_price REAL,
    #     amount REAL,
    #     notes TEXT,
    #     full_amount REAL,
    #     unit_cost REAL,
    #     total_cost REAL,
    #     margin REAL
    # )
    # ''')
    # conn.commit()
    # conn.close()
    # print("✅ Table 'sales_quote_items' created.")

    # conn = sqlite3.connect('main.db')
    # cursor = conn.cursor()
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS purchase_orders (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     transaction_no TEXT UNIQUE,
    #     transaction_date TEXT,
    #     vendor TEXT,
    #     eta TEXT,
    #     status TEXT
    # );
    # ''')
    # conn.commit()
    # conn.close()
    # print("✅ Table 'purchase_orders' created.")
    #
    #
    # conn = sqlite3.connect('main.db')
    # cursor = conn.cursor()
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS purchase_order_detail (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     transaction_no TEXT,
    #     product_code TEXT,
    #     description TEXT,
    #     qty INTEGER,
    #     unit TEXT,
    #     unit_cost REAL
    # );
    # ''')
    # conn.commit()
    # conn.close()
    # print("✅ Table 'sales_quote_detail' created.")

    # conn = sqlite3.connect("main.db")
    # c = conn.cursor()
    #
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS transfer_warehouse (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     date TEXT,
    #     from_warehouse TEXT,
    #     to_warehouse TEXT,
    #     approved INTEGER DEFAULT 0,
    #     created_by TEXT,
    #     notes TEXT
    # )
    # """)
    #
    # conn.commit()
    # conn.close()
    #
    # print("✅ transfer_warehouse table created.")

    # conn = sqlite3.connect('main.db')
    # cursor = conn.cursor()
    #
    # cursor.execute('''
    # CREATE TABLE attendance (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     user TEXT,
    #     name TEXT,
    #     date TEXT,
    #     time TEXT,
    #     note TEXT
    # );
    # ''')
    # conn.commit()
    # conn.close()
    # print("✅ Table 'sales_quote_items' created.")