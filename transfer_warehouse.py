import csv
import os
import sqlite3
import sys
import pandas as pd
import json
from datetime import datetime, date

from flask import Flask, request, jsonify, render_template, redirect, flash, json

def get_all_transfers():
    conn = sqlite3.connect("main.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM transfer_warehouse ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def render_transfer_list():
    transfers = get_all_transfers()  # Fetch from DB
    return render_template('transfer_list.html', transfers=transfers)

def render_create_transfer():
    if request.method == 'POST':
        # Process and save the new transfer
        create_new_transfer(request.form, created_by=current_user.username)
        return redirect(url_for('transfer_list'))
    return render_template('create_transfer.html')