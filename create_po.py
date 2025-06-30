import csv
import os
from flask import Flask, render_template, jsonify, request
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "key.env")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

BASE_DIR = Path(__file__).parent
QUOTES_FILE = BASE_DIR / "static/data/sales_quotes.csv"
DETAIL_FILE = BASE_DIR / "static/data/sales_quote_detail.csv"
PRODUCTS_CSV = BASE_DIR / "static/data/products_std.csv"

def render_create_po():
    df = pd.read_csv(PRODUCTS_CSV)
    product_list = df.to_dict(orient='records')
    return render_template("create_po.html", product_list=product_list, quote=None)