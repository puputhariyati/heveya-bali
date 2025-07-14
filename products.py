import sqlite3
import pandas as pd
import os

from flask import render_template, redirect, request, flash, Flask
from collections import defaultdict

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / "key.env")
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "main.db"

def render_products():
    df = pd.read_csv("static/data/products_std.csv")
    df = df.fillna(0)

    # 🔹 Standardize column names
    df.rename(columns={
        'Showroom_Qty': 'showroom_qty',
        'Warehouse_Qty': 'warehouse_qty'
    }, inplace=True)

    # 🔸 Format quantity helper
    def format_qty(value):
        try:
            value = float(value)
            if value == 0:
                return '-'
            elif value.is_integer():
                return str(int(value))
            else:
                return str(value)
        except:
            return '-'

    # 🔹 PILLOWS
    pillow_df = df[df['Category'].str.contains("pillow", case=False, na=False)].copy()

    pillow_df['req_sh'] = pillow_df.apply(
        lambda row: 6 - float(row['showroom_qty']) if float(row['showroom_qty']) < 6 else 0,
        axis=1
    )
    pillow_df['req_wh'] = pillow_df.apply(
        lambda row: 20 - float(row['warehouse_qty']) if float(row['warehouse_qty']) < 20 else 0,
        axis=1
    )

    for col in ['showroom_qty', 'warehouse_qty', 'req_sh', 'req_wh']:
        pillow_df[col] = pillow_df[col].apply(format_qty)

    pillow_products = pillow_df.to_dict(orient='records')

    # 🔹 MATTRESSES
    mattress_df = df[df['Category'] == 'Mattress'].copy()
    mattresses = mattress_df.to_dict(orient='records')

    # 🔹 BEDSHEETS
    bedsheets_df = df[df['Category'].str.contains("Bedsheet", case=False, na=False)].copy()
    bedsheets_df['req_sh'] = bedsheets_df.apply(
        lambda row: 6 - float(row['showroom_qty']) if float(row['showroom_qty']) < 6 else 0,
        axis=1
    )
    bedsheets_df['req_wh'] = bedsheets_df.apply(
        lambda row: 20 - float(row['warehouse_qty']) if float(row['warehouse_qty']) < 20 else 0,
        axis=1
    )

    # Group by sheet type → material → color → size
    grouped_bedsheets = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    for _, row in bedsheets_df.iterrows():
        name = row.get('name', '')
        if not isinstance(name, str) or '-' not in name:
            continue

        parts = name.split('-')
        if len(parts) < 3:
            continue

        color = parts[-1].strip()  # ✅ Now this is 'White'
        size_raw = parts[-2].strip().lower()  # ✅ 'Super King (200x200)'
        size = (
            'SK' if 'super' in size_raw else
            'K' if 'king' in size_raw else
            'Q' if 'queen' in size_raw else
            'S' if 'single' in size_raw else
            'Unknown'
        )

        grouped_bedsheets['Fitted Sheets'][color][size] = {
            'showroom': row['showroom_qty'],
            'warehouse': row['warehouse_qty'],
            'req_sh': row['req_sh'],
            'req_wh': row['req_wh'],
        }

    # 🔹 BATHROOM SERIES (Bath Accessories)
    bathroom_df = df[df['Category'].str.contains("Bath Accessories", case=False, na=False)].copy()
    # Calculate showroom & warehouse requests
    bathroom_df['req_sh'] = bathroom_df.apply(
        lambda row: 6 - float(row['showroom_qty']) if float(row['showroom_qty']) < 6 else 0,
        axis=1
    )
    bathroom_df['req_wh'] = bathroom_df.apply(
        lambda row: 20 - float(row['warehouse_qty']) if float(row['warehouse_qty']) < 20 else 0,
        axis=1
    )
    # # Format values
    # for col in ['showroom_qty', 'warehouse_qty', 'req_sh', 'req_wh']:
    #     bathroom_df[col] = bathroom_df[col].apply(format_qty)
    # Group by item type (excluding color)
    grouped_bathroom = defaultdict(lambda: {
        'Showroom': {},
        'Warehouse': {},
        'ReqSH': {},
        'ReqWH': {},
    })
    for _, row in bathroom_df.iterrows():
        name_parts = row['name'].rsplit('-', 1)
        item_type = name_parts[0].strip()  # e.g., "Heveya Vegan Cotton Face Towel - 30x30cm"
        color = name_parts[1].strip() if len(name_parts) > 1 else 'Unknown'
        grouped_bathroom[item_type]['Showroom'][color] = row['showroom_qty']
        grouped_bathroom[item_type]['Warehouse'][color] = row['warehouse_qty']
        grouped_bathroom[item_type]['ReqSH'][color] = row['req_sh']
        grouped_bathroom[item_type]['ReqWH'][color] = row['req_wh']

    return render_template(
        "products.html",
        pillows=pillow_products,
        mattresses=mattresses,
        grouped_bedsheets=grouped_bedsheets,
        grouped_bathroom=grouped_bathroom
    )