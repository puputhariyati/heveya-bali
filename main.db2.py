import sqlite3
import pandas as pd

# Connect to your SQLite database
conn = sqlite3.connect("main.db")
c = conn.cursor()

# Load the sales_order table into a DataFrame
df = pd.read_sql_query("SELECT * FROM sales_order", conn)

# Parse to datetime safely (supporting mixed formats)
df['parsed_date'] = pd.to_datetime(df['transaction_date'], errors='coerce', dayfirst=True)

# Drop rows where date couldn't be parsed
valid_rows = df[df['parsed_date'].notna()].copy()

# Format to 'dd/mm/yyyy'
valid_rows['formatted_date'] = valid_rows['parsed_date'].dt.strftime('%d/%m/%Y')

# Update only valid rows
for _, row in valid_rows.iterrows():
    c.execute("""
        UPDATE sales_order
        SET transaction_date = ?
        WHERE transaction_no = ?
    """, (row['formatted_date'], row['transaction_no']))

conn.commit()
conn.close()

print(f"✅ Reformatted and updated {len(valid_rows)} dates to dd/mm/yyyy.")
