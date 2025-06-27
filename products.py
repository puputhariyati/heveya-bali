import sqlite3
import pandas as pd

from flask import Flask, render_template, jsonify, request

# def render_products():
#     df = pd.read_csv("static/data/products_std.csv")
#     # Filter only pillow products
#     pillow_df = df[df['Category'].str.contains("pillow", case=False, na=False)].copy()
#     # Rename quantity columns for easier handling
#     pillow_df.rename(columns={
#         'Showroom_Qty': 'showroom_qty',
#         'Warehouse_Qty': 'warehouse_qty'
#     }, inplace=True)
#     # Compute required to showroom (req_sh)
#     pillow_df['req_sh'] = pillow_df.apply(
#         lambda row: 6 - row['showroom_qty'] if row['showroom_qty'] < 6 else 0,
#         axis=1
#     )
#     # Compute required to warehouse (req_wh)
#     pillow_df['req_wh'] = pillow_df.apply(
#         lambda row: 20 - row['warehouse_qty'] if row['warehouse_qty'] < 20 else 0,
#         axis=1
#     )
#     # Format numeric values for display
#     def format_qty(value):
#         try:
#             value = float(value)
#             if value == 0:
#                 return '-'
#             elif value.is_integer():
#                 return str(int(value))
#             else:
#                 return str(value)
#         except:
#             return '-'
#     for col in ['showroom_qty', 'warehouse_qty', 'req_sh', 'req_wh']:
#         pillow_df[col] = pillow_df[col].apply(format_qty)
#
#     # Convert to list of dicts for template rendering
#     pillow_products = pillow_df.to_dict(orient='records')
#     return render_template("products.html", pillows=pillow_products)

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

    return render_template(
        "products.html",
        pillows=pillow_products,
        mattresses=mattresses
    )
