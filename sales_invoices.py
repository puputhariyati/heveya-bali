# fetch_to_db.py  (API → SQLite with pre‑formatted currency)
import os, json, requests, sqlite3, base64, hashlib, hmac, re
from email.utils import formatdate
from datetime import datetime, timezone

from pathlib import Path
DOTENV_PATH = Path(__file__).parent / "key.env"
print("🔎  Expecting .env at:", DOTENV_PATH.resolve())
print("🔎  Exists? →", DOTENV_PATH.exists())

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

# ── FETCH API ────────────────────────────────────────────────────
def fetch_sales_invoices(date_from, date_to) -> list:
    """Return ALL sales invoices between date_from and date_to (YYYY‑MM‑DD)."""
    all_orders, page = [], 1
    while True:
        date_hdr = formatdate(usegmt=True)
        query = (f"?start_date={date_from}&end_date={date_to}"
                 f"&page={page}&sort_by=transaction_date&sort_order=asc")
        full = SALES_INVOICES_ENDPOINT + query
        hdrs = {"Date": date_hdr,
                "Authorization": _hmac_header("GET", full, date_hdr),
                "Content-Type": "application/json"}
        r = requests.get(BASE_URL + full, headers=hdrs, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"Mekari API error {r.status_code}: {r.text}")
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
            status      = excluded.status,
            etd         = excluded.etd
    """, (
        o["transaction_no"],
        o["transaction_date"],
        o.get("person", {}).get("display_name", ""),
        format_rupiah(o.get("remaining_currency_format") or o.get("remaining", "")),
        format_rupiah(o.get("original_amount_currency_format") or o.get("total", "")),
        o.get("status", ""),
        o.get("etd", "")
    ))
    return cur.rowcount == 1          # 1=insert, 2=update

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
