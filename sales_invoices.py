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


def render_sales_invoices():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    search_query = request.args.get("search", "").lower()

    # Fetch all sales orders
    cursor.execute("SELECT * FROM sales_invoices ORDER BY transaction_date DESC")
    orders = cursor.fetchall()
    results = []

    for order in orders:
        tx_no = order["transaction_no"]

        # ✅ Apply item-level filtering only if search query provided
        if search_query:
            cursor.execute("SELECT item FROM sales_invoices_detail WHERE transaction_no = ?", (tx_no,))
            items = [row["item"].lower() for row in cursor.fetchall()]
            # Skip this order if item doesn't match search
            search_words = search_query.split()
            if not any(all(word in item for word in search_words) for item in items):
                continue

        # Fetch details to determine status
        cursor.execute("SELECT delivered, remain_qty FROM sales_invoices_detail WHERE transaction_no = ?", (tx_no,))
        details = cursor.fetchall()

        # Determine status
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

        order_dict = dict(order)
        order_dict["status"] = status
        results.append(order_dict)

    # ✅ Sort by date
    results.sort(
        key=lambda x: datetime.strptime(x["transaction_date"], "%d/%m/%Y"),
        reverse=True
    )
    conn.close()
    return render_template("sales_invoices.html", orders=results)


# ── FETCH API ───────────────────────────────────────────────────
def fetch_sales_invoices(date_from, date_to):
    all_orders, page = [], 1

    # Load existing transaction_nos from DB
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    existing_tx = set(row[0] for row in cursor.execute("SELECT transaction_no FROM sales_invoices"))
    conn.close()

    while True:
        date_hdr = formatdate(usegmt=True)
        query = (f"?start_date={date_from}&end_date={date_to}"
                 f"&page={page}&sort_by=transaction_date&sort_order=asc")
        full = SALES_INVOICES_ENDPOINT + query
        hdrs = {
            "Date": date_hdr,
            "Authorization": _hmac_header("GET", full, date_hdr),
            "Content-Type": "application/json"
        }
        try:
            r = requests.get(BASE_URL + full, headers=hdrs, timeout=60)
        except Timeout:
            print(f"⚠️  Mekari timeout on page {page}, retrying once …")
            r = requests.get(BASE_URL + full, headers=hdrs, timeout=60)

        if r.status_code != 200:
            raise RuntimeError(f"Mekari error {r.status_code}: {r.text}")

        batch = r.json().get("sales_invoices", [])
        if not batch:
            break

        # Only append invoices that are not in the DB
        new_orders = [o for o in batch if o["transaction_no"] not in existing_tx]
        all_orders.extend(new_orders)

        page += 1

    return all_orders


# ── DB UPSERT ────────────────────────────────────────────────────
def _upsert_header(cur, o):
    cur.execute("""
        INSERT INTO sales_invoices (
            transaction_no, transaction_date, customer,
            balance_due, total, status, etd, po_no, tags, payment
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(transaction_no) DO UPDATE SET
            balance_due = excluded.balance_due,
            total       = excluded.total,
            etd         = excluded.etd,
            po_no       = excluded.po_no,
            tags        = excluded.tags,
            payment     = excluded.payment,
            status      = CASE
                            WHEN sales_invoices.status IS NULL OR sales_invoices.status = ''
                            THEN excluded.status
                            ELSE sales_invoices.status
                          END
    """, (
        o["transaction_no"],
        o["transaction_date"],
        o.get("person", {}).get("display_name", ""),
        format_rupiah(o.get("remaining_currency_format") or o.get("remaining", "")),
        format_rupiah(o.get("original_amount_currency_format") or o.get("total", "")),
        o.get("transaction_status", {}).get("name", ""),
        o.get("etd", ""),
        o.get("po_number", ""),
        o.get("tags_string", ""),
        o["payments"][0]["payment_method_name"] if o.get("payments") else ""
    ))
    return cur.rowcount == 1


def _insert_detail(cur, txn_no, i, ln):
    prod = ln.get("product", {})
    item = prod.get("name", "") if isinstance(prod, dict) else str(prod)
    qty = int(float(ln.get("quantity", 0)))
    unit_val = prod.get("unit", "pcs")
    unit = unit_val["name"] if isinstance(unit_val, dict) else str(unit_val)

    delivered = int(ln.get("delivered", qty))  # fallback to full qty
    remain_qty = qty - delivered

    po_no = ""
    status = "closed"

    # Optional future: extract description, delivery date, warehouse option, etc.
    cur.execute("""
        INSERT INTO sales_invoices_detail (transaction_no, line, item, qty, unit,
                                           delivered, remain_qty, po_no, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(transaction_no, line) DO
        UPDATE SET
            item = excluded.item,
            qty = excluded.qty,
            unit = excluded.unit,
            delivered = excluded.delivered,
            remain_qty = excluded.remain_qty,
            status = excluded.status
        """, (
            txn_no, i,
            prod.get("name", ""),
            qty,
            prod.get("unit", "pcs"),
            delivered,
            remain_qty,
            "",  # po_no
            "closed"
    ))


def bulk_update_status():
    try:
        data = request.get_json()
        print("📦 Received data:", data)

        transaction_nos = data.get("transaction_nos", [])
        status = data.get("status")

        print("🧾 Transactions:", transaction_nos)
        print("🚦 Status:", status)

        if not transaction_nos or status not in ["closed"]:
            return jsonify({"success": False, "message": "Invalid data"})

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        for tx_no in transaction_nos:
            print(f"🔄 Updating tx {tx_no}")
            if status == "closed":
                cursor.execute("""
                               UPDATE sales_invoices_detail
                               SET remain_qty = 0,
                                   delivered  = qty
                               WHERE transaction_no = ?
                               """, (tx_no,))

        conn.commit()
        conn.close()

        print("✅ Bulk update status successful")
        return jsonify({"success": True})

    except Exception as e:
        print("❌ ERROR IN bulk_update_status():", e)
        return jsonify({"success": False, "message": str(e)})


def bulk_update_etd():
    data = request.get_json()
    transaction_nos = data.get("transaction_nos", [])
    etd = data.get("etd")

    if not transaction_nos or not etd:
        return jsonify({"success": False, "message": "Missing data"})

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for tx_no in transaction_nos:
        cursor.execute("UPDATE sales_invoices SET ETD = ? WHERE transaction_no = ?", (etd, tx_no))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


def sync_sales_invoices(date_from, date_to):
    """Fetch from API, upsert into DB, return (added, updated, detail_rows)."""
    orders = fetch_sales_invoices(date_from, date_to)
    conn   = sqlite3.connect(DATABASE)
    cur    = conn.cursor()
    added = updated = detail_rows = 0

    for o in orders:
        if _upsert_header(cur, o):
            added += 1
        else:
            updated += 1

        for i, ln in enumerate(o.get("transaction_lines_attributes", []), start=1):
            _insert_detail(cur, o["transaction_no"], i, ln)
            detail_rows += 1  # ✅ count each detail line

    conn.commit(); conn.close()
    return added, updated, detail_rows



def render_refresh_invoices():
    try:
        # --- 1. choose date window (last 30 days here) ------------------
        date_to   = datetime.now().strftime("%Y-%m-%d")
        date_from = "2025-07-01"  # ← fixed start
        # date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d") #backward 30days from today

        added, updated, detail_rows = sync_sales_invoices(date_from, date_to)

        return jsonify({
            "status": "ok",
            "added": added,
            "updated": updated,
            "detail_rows": detail_rows,
            "last_refresh": datetime.now().isoformat()
        })

    except Exception as e:
        # log to stderr so you can see it in the PA error log
        print("❌ refresh_invoices failed:", e)
        return jsonify({"status": "error", "msg": str(e)}), 500

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
#             "SELECT COUNT(*) FROM sales_invoices WHERE transaction_date >= ?",
#             (test_from,)
#         )
#         count = cur.fetchone()[0]
#         conn.close()
#         print(f"📊  Rows in DB with date ≥ {test_from}: {count}")
#
#     except Exception as e:
#         print("❌  Smoke‑test failed:", e)
