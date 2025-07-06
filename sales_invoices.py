# fetch_to_db.py  (API → SQLite with pre‑formatted currency)
import os, json, requests, sqlite3, base64, hashlib, hmac, re
from requests.exceptions import Timeout
from email.utils import formatdate
from datetime import datetime, timezone
from flask import Flask, render_template, redirect, flash, json, request, jsonify

from pathlib import Path

DOTENV_PATH = Path(__file__).parent / "key.env"
# print("🔎  Expecting .env at:", DOTENV_PATH.resolve())
# print("🔎  Exists? →", DOTENV_PATH.exists())

from dotenv import load_dotenv
load_dotenv(DOTENV_PATH, override=True)

# ── CONFIG ───────────────────────────────────────────────────────
BASE_URL   = "https://api.mekari.com"
SALES_INVOICES_ENDPOINT   = "/public/jurnal/api/v1/sales_invoices"
DATE_FROM  = "2025-07-01"                 # adjust as needed
DATE_TO    = datetime.now().strftime("%Y-%m-%d")
CLIENT_ID  = os.getenv("CLIENT_ID")
CLIENT_SEC = os.getenv("CLIENT_SECRET")

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "main.db"
# ── HELPERS ──────────────────────────────────────────────────────
def _hmac_header(method, path, date_hdr):
    signing = f"date: {date_hdr}\n{method} {path} HTTP/1.1"
    sig     = base64.b64encode(
        hmac.new(CLIENT_SEC.encode(), signing.encode(), hashlib.sha256).digest()
    ).decode()
    return (f'hmac username="{CLIENT_ID}", algorithm="hmac-sha256", '
            f'headers="date request-line", signature="{sig}"')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def format_rupiah(value):
    """Accept int/float/str and return 'Rp. 1.234.567'."""
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return "Rp. {:,}".format(int(value)).replace(",", ".")
    # string: already formatted?
    if isinstance(value, str) and value.strip().startswith("Rp"):
        return value.strip().replace(",", ".")          # normalise commas→dots
    # fallback: strip non‑digits, convert
    digits = re.sub(r"[^\d]", "", str(value))
    return "Rp. {:,}".format(int(digits or 0)).replace(",", ".")


def render_refresh_invoices():
    try:
        # --- 1. choose date window (last 30 days here) ------------------
        date_to   = datetime.now().strftime("%Y-%m-%d")
        date_from = "2025-07-01"  # ← fixed start
        # date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d") #backward 30days from today

        # --- 2. pull & upsert ------------------------------------------
        added, updated = sync_sales_invoices(date_from, date_to)

        # make 100 % sure we pass *real* JSON‑serialisable values
        added        = int(added or 0)
        updated      = int(updated or 0)
        last_refresh = datetime.now(timezone.utc)\
                              .isoformat(timespec="seconds")\
                              .replace("+00:00", "Z")

        return jsonify({
            "status"      : "ok",
            "added"       : added,
            "updated"     : updated,
            "last_refresh": last_refresh
        })

    except Exception as e:
        # log to stderr so you can see it in the PA error log
        print("❌ refresh_invoices failed:", e)
        return jsonify({"status": "error", "msg": str(e)}), 500


# def render_sales_invoices():
#     conn = get_db_connection()
#     cur  = conn.execute("""
#         SELECT
#           transaction_no,
#           transaction_date,              -- may be ISO or DD/MM/YYYY
#           COALESCE(customer,'')    AS customer,
#           COALESCE(balance_due,'') AS balance_due,
#           COALESCE(total,'')       AS total,
#           COALESCE(status,'')      AS status,
#           COALESCE(etd,'')         AS etd
#         FROM sales_order
#     """)
#     rows_raw = cur.fetchall()
#     conn.close()
#
#     rows = []
#     for r in rows_raw:
#         d = dict(r)
#
#         # --- Parse the date safely ---------------------------------
#         iso = d["transaction_date"]
#         try:
#             # try ISO first
#             dt = datetime.strptime(iso, "%Y-%m-%d")
#             display_date = dt.strftime("%d/%m/%Y")
#         except ValueError:
#             # fallback: DD/MM/YYYY in DB already
#             try:
#                 dt = datetime.strptime(iso, "%d/%m/%Y")
#                 display_date = iso                # already formatted
#             except ValueError:
#                 dt = datetime.min                 # put bad rows at bottom
#                 display_date = iso
#
#         d["transaction_date"] = display_date
#         d["_dt_obj"] = dt        # helper key for sorting
#         rows.append(d)
#     # --- Sort newest → oldest using _dt_obj -------------------------
#     rows.sort(key=lambda x: x["_dt_obj"], reverse=True)
#     # Remove helper key before sending to template
#     for d in rows:
#         d.pop("_dt_obj", None)
#     return render_template("sales_invoices.html", orders=rows)

def render_sales_invoices():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all sales orders
    cursor.execute("SELECT * FROM sales_order ORDER BY transaction_date DESC")
    orders = cursor.fetchall()

    results = []

    for order in orders:
        tx_no = order["transaction_no"]
        # Fetch details to determine status
        cursor.execute("SELECT delivered, remain_qty FROM sales_order_detail WHERE transaction_no = ?", (tx_no,))
        details = cursor.fetchall()

        # Default status logic
        if not details:
            status = "closed"
        else:
            all_remain_zero = all(d["remain_qty"] == 0 for d in details)
            any_delivered_gt_zero = any(d["delivered"] > 0 for d in details)

            if all_remain_zero:
                status = "closed"
            elif any_delivered_gt_zero:
                status = "partially sent"
            else:
                status = "open"

        # Merge status into order
        order_dict = dict(order)
        order_dict["status"] = status
        results.append(order_dict)

    # ✅ Sort by newest date using datetime.strptime
    results.sort(
        key=lambda x: datetime.strptime(x["transaction_date"], "%d/%m/%Y"),
        reverse=True
    )

    conn.commit()
    conn.close()
    return render_template("sales_invoices.html", orders=results)

# ── FETCH API ────────────────────────────────────────────────────
def fetch_sales_invoices(date_from, date_to):
    all_orders, page = [], 1
    while True:
        date_hdr = formatdate(usegmt=True)
        query = (f"?start_date={date_from}&end_date={date_to}"
                 f"&page={page}&sort_by=transaction_date&sort_order=asc")
        full = SALES_INVOICES_ENDPOINT + query
        hdrs = {"Date": date_hdr,
                "Authorization": _hmac_header("GET", full, date_hdr),
                "Content-Type": "application/json"}
        try:
            r = requests.get(BASE_URL + full, headers=hdrs, timeout=60)  # ⬅ timeout 60 s
        except Timeout:
            print(f"⚠️  Mekari timeout on page {page}, retrying once …")
            r = requests.get(BASE_URL + full, headers=hdrs, timeout=60)

        if r.status_code != 200:
            raise RuntimeError(f"Mekari error {r.status_code}: {r.text}")

        batch = r.json().get("sales_invoices", [])
        if not batch:
            break
        all_orders.extend(batch)
        page += 1
    return all_orders

# ── DB UPSERT ────────────────────────────────────────────────────
def _upsert_header(cur, o):
    cur.execute("""
        INSERT INTO sales_order (
            transaction_no, transaction_date, customer,
            balance_due, total, status, etd
        ) VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(transaction_no) DO UPDATE SET
            balance_due = excluded.balance_due,
            etd         = excluded.etd,
            status      = CASE
                            WHEN sales_order.status IS NULL OR sales_order.status = ''
                            THEN excluded.status
                            ELSE sales_order.status
                          END
    """, (
        o["transaction_no"],
        o["transaction_date"],
        o.get("person", {}).get("display_name", ""),
        format_rupiah(o.get("remaining_currency_format") or o.get("remaining", "")),
        format_rupiah(o.get("original_amount_currency_format") or o.get("total", "")),
        o.get("transaction_status", {}).get("name", ""),
        o.get("etd", "")
    ))
    return cur.rowcount == 1


def _insert_detail(cur, txn_no, i, ln):
    prod = ln.get("product", {})
    cur.execute("""
        INSERT OR IGNORE INTO sales_order_detail (
            transaction_no, line, item, qty, unit,
            delivered, remain_qty, po_no, status
        ) VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        txn_no, i,
        prod.get("name", ""),
        int(float(ln.get("quantity", 0))),
        prod.get("unit", "pcs"),
        0,
        int(float(ln.get("quantity", 0))),
        "",
        "open"
    ))

def bulk_update_status():
    data = request.get_json()
    txn_nos  = data.get("transaction_nos", [])
    new_stat = data.get("status")

    if not txn_nos or new_stat not in ("closed",):
        return jsonify(success=False, message="Invalid data"), 400

    conn = get_db_connection()
    cur  = conn.cursor()

    cur.executemany(
        "UPDATE sales_order SET status=? WHERE transaction_no=?",
        [(new_stat, tx) for tx in txn_nos]
    )
    conn.commit()

    # return patched rows so JS can update DOM
    placeholders = ",".join("?"*len(txn_nos))
    cur.execute(f"""
        SELECT transaction_no, status
        FROM sales_order
        WHERE transaction_no IN ({placeholders})
    """, txn_nos)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify(success=True, updated=len(rows), rows=rows)


def bulk_update_etd():
    data = request.get_json()
    transaction_nos = data.get("transaction_nos", [])
    etd = data.get("etd")

    if not transaction_nos or not etd:
        return jsonify({"success": False, "message": "Missing data"})

    conn = sqlite3.connect("main.db")
    cursor = conn.cursor()

    for tx_no in transaction_nos:
        cursor.execute("UPDATE sales_order SET ETD = ? WHERE transaction_no = ?", (etd, tx_no))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

def sync_sales_invoices(date_from, date_to):
    """Fetch from API, upsert into DB, return (added, updated)."""
    orders = fetch_sales_invoices(date_from, date_to)
    conn   = sqlite3.connect(DATABASE)
    cur    = conn.cursor()
    added = updated = 0

    for o in orders:
        if _upsert_header(cur, o): added += 1
        else:                      updated += 1
        for i, ln in enumerate(o.get("transaction_lines_attributes", []), start=1):
            _insert_detail(cur, o["transaction_no"], i, ln)

    conn.commit(); conn.close()
    return added, updated



# # ───────────────  QUICK SELF‑TEST  ───────────────────────────────
# if __name__ == "__main__":
#     # Make sure env vars are present
#     if not (CLIENT_ID and CLIENT_SEC):
#         raise SystemExit("⚠️  CLIENT_ID / CLIENT_SECRET not set in your shell or key.env")
#
#     # Pick a short date window first
#     test_from = "2025-07-01"
#     test_to   = datetime.now().strftime("%Y-%m-%d")
#
#     print(f"🔎  Smoke‑test: {test_from} → {test_to}")
#     try:
#         added, updated = sync_sales_invoices(test_from, test_to)
#         print(f"✅  Sync complete — inserted: {added}, updated: {updated}")
#
#         # quick check: count rows we just touched
#         conn = sqlite3.connect(DATABASE)
#         cur  = conn.cursor()
#         cur.execute(
#             "SELECT COUNT(*) FROM sales_order WHERE transaction_date >= ?",
#             (test_from,)
#         )
#         count = cur.fetchone()[0]
#         conn.close()
#         print(f"📊  Rows in DB with date ≥ {test_from}: {count}")
#
#     except Exception as e:
#         print("❌  Smoke‑test failed:", e)
