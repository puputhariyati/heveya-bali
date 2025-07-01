import csv
import os
import sqlite3
import sys
import pandas as pd
import json
from datetime import datetime, date

from flask import Flask, request, jsonify, render_template, redirect, flash, json
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(Path(__file__).parent / "key.env")

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env

DATABASE = "main.db"  # ✅ Now using main.db instead of stock.db

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def render_attendance():
    filter_name = request.args.get("filter_name", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    query = "SELECT date, time, note FROM attendance WHERE 1=1"
    params = []

    if filter_name:
        query += " AND name=?"
        params.append(filter_name)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC, time DESC"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    records = cur.fetchall()

    return render_template("attendance.html",
        records=records,
        filter_name=filter_name,
        start_date=start_date,
        end_date=end_date,
        today_date=date.today()
    )

def render_attendance_checkin():
    user = "sales_person_1"  # Replace with session.get("user") if available
    now = datetime.now()
    note = request.form.get("note", "")

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("INSERT INTO attendance (user, date, time, note) VALUES (?, ?, ?, ?)", (
        user, now.date().isoformat(), now.time().strftime("%H:%M:%S"), note))
    conn.commit()

    return redirect("/attendance")