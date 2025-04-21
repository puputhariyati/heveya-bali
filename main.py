import os
import sqlite3
import traceback

from flask import Flask, request, jsonify, render_template, redirect, flash
from dotenv import load_dotenv

from jurnal_api import get_sales_orders

load_dotenv("key.env")  # Load environment variables from .env file

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env
DATABASE = "stock.db"  # Path to your database file




def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables accessing rows as dictionaries
    return conn


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


# Ensure the database and table are created
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            on_hand INTEGER NOT NULL DEFAULT 0,
            free_qty INTEGER NOT NULL DEFAULT 0, 
            booked_qty INTEGER NOT NULL DEFAULT 0,
            delivered_qty INTEGER NOT NULL DEFAULT 0,
            upcoming_qty INTEGER NOT NULL DEFAULT 0,
            unit_sell_price REAL NOT NULL DEFAULT 0,
            unit_buy_price REAL NOT NULL DEFAULT 0,
            tags TEXT,
            product_type TEXT NOT NULL DEFAULT 'single'
        )
    ''')

    # 🔄 Add 'product_type' only if it doesn't exist
    if not column_exists(cursor, "inventory", "product_type"):
        cursor.execute("ALTER TABLE inventory ADD COLUMN product_type TEXT")

    # Add 'cell_notes' if it doesn't exist
    if not column_exists(cursor, "inventory", "cell_notes"):
        cursor.execute("ALTER TABLE inventory ADD COLUMN cell_notes TEXT DEFAULT ''")

    # Create BOM table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            component_name TEXT NOT NULL,
            quantity_required INTEGER NOT NULL
        )
    ''')

    # 🔄 Rename old column names if table already exists with legacy names
    # Check current column names
    cursor.execute("PRAGMA table_info(bom)")
    columns = [col[1] for col in cursor.fetchall()]

    rename_map = {
        "product": "product_name",
        "component": "component_name",
        "quantity": "quantity_required"
    }

    for old_col, new_col in rename_map.items():
        if old_col in columns and new_col not in columns:
            try:
                cursor.execute(f"ALTER TABLE bom RENAME COLUMN {old_col} TO {new_col}")
                print(f"Renamed column {old_col} to {new_col}")
            except sqlite3.OperationalError as e:
                print(f"Error renaming {old_col}: {e}")

    # Create leads table for CRM dashboard
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            status TEXT NOT NULL,
            sales_person TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            date TEXT NOT NULL,
            source TEXT,
            mobile TEXT UNIQUE,
            email TEXT
        )
    ''')

    conn.commit()
    conn.close()


# Call the function to create the table at startup
init_db()


@app.route('/')
def home():
    return render_template('index.html')




@app.route("/get_product_suggestions", methods=["GET"])
def get_product_suggestions():
    """Fetch product name suggestions based on input"""
    query = request.args.get("query", "").strip().lower()

    with sqlite3.connect("stock.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT product_name FROM inventory
            WHERE LOWER(product_name) LIKE LOWER(?)
            LIMIT 10
        """, ('%' + query + '%',))
        products = [row[0] for row in cursor.fetchall()]

    return jsonify(products)


@app.route("/api/get_stock", methods=["GET"])
def get_stock():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch inventory data
        cursor.execute("SELECT * FROM inventory")
        stock_data = cursor.fetchall()

        # Fetch BOM components and their required quantity
        cursor.execute("SELECT product_name, component_name, quantity_required FROM bom")
        bom_data = cursor.fetchall()

        # Convert BOM to a dictionary: {product_name: [(component_name, required_qty), ...]}
        bom_dict = {}
        for product_name, component_name, quantity_required in bom_data:
            if product_name not in bom_dict:
                bom_dict[product_name] = []
            bom_dict[product_name].append((component_name, quantity_required))

        # Convert inventory to dictionary for quick lookup
        inventory_dict = {row["product_name"]: {k: row[k] for k in row.keys()} for row in stock_data}

        # Process stock with BOM dependencies
        stock = []
        for row in stock_data:
            product_name = row["product_name"]
            # free_qty = row["free_qty"]  # Default from DB
            # on_hand = row["on_hand"]  # Default from DB
            booked_qty = row["booked_qty"]  # Default from DB
            delivered_qty = row["delivered_qty"]  # Default from DB

            # If the product has a BOM, calculate its free_qty dynamically
            if product_name in bom_dict:
                min_possible = float('inf')  # Start with a large number
                for component_name, quantity_required in bom_dict[product_name]:
                    component_stock = inventory_dict.get(component_name, {}).get("free_qty", 0)

                    # ❗ Important: If component is missing or has 0 stock, bundle is unavailable
                    if quantity_required <= 0 or component_stock <= 0:
                        min_possible = 0
                        break

                    max_producible = component_stock // quantity_required
                    min_possible = min(min_possible, max_producible)

                free_qty = int(min_possible)
                on_hand = free_qty + booked_qty  # Consistent with updated logic
            else:
                free_qty = row["free_qty"]
                on_hand = row["on_hand"]

            # # Ensure on_hand is properly recalculated
            # on_hand = row["on_hand"]  # Default from DB
            # if product_name in bom_dict:
            #     on_hand = free_qty + booked_qty  # On-hand should be the calculated free stock

            stock.append({
                "id": row["id"],
                "product_name": product_name,
                "on_hand": on_hand,  # Updated dynamically
                "free_qty": free_qty,  # Updated dynamically
                "booked_qty": booked_qty, # Updated dynamically
                "delivered_qty": delivered_qty,
                "upcoming_qty": row["upcoming_qty"],
                "unit_sell_price": row["unit_sell_price"],
                "unit_buy_price": row["unit_buy_price"],
                "tags": row["tags"],
                "product_type": row["product_type"],
                "cell_notes": row["cell_notes"]  # ✅ Add this line
            })

        conn.close()

        # Add cache-busting headers
        response = jsonify(stock)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"

        return response

    except Exception as e:
        print("❌ ERROR in /api/get_stock:")
        traceback.print_exc()  # 🔥 this shows detailed error info
        return jsonify({"error": str(e)}), 500


@app.route('/inventory', methods=['GET', 'POST'])
def inventory_page():
    if request.method == 'POST':
        product_name = request.form.getlist('product_name')
        free_qty = request.form.getlist('free_qty') or ["0"]
        unit_buy_price = request.form.getlist('unit_buy_price') or ["0.0"]
        unit_sell_price = request.form.getlist('unit_sell_price') or ["0.0"]
        tags = request.form.getlist('tags') or [""]
        product_type = request.form.getlist('product_type') or ["single"]

        # Retrieve missing quantities
        booked_qty = request.form.getlist('booked_qty') or ["0"]
        delivered_qty = request.form.getlist('delivered_qty') or ["0"]
        upcoming_qty = request.form.getlist('upcoming_qty') or ["0"]

        # Ensure all lists have the same length
        if len(set(map(len, [product_name, free_qty, unit_buy_price, unit_sell_price, tags, product_type, booked_qty,
                             delivered_qty, upcoming_qty]))) > 1:
            flash("Error: Mismatch in field lengths. Please fill all fields properly.", "danger")
            return redirect('/inventory')

        # Check if required fields are filled
        if not all(product_name) or not all(tags):
            flash("Error: All fields must be filled", "danger")
            return redirect('/inventory')

        conn = sqlite3.connect('stock.db')
        cursor = conn.cursor()

        for i in range(len(product_name)):
            # Check if product already exists in the database
            cursor.execute("SELECT COUNT(*) FROM inventory WHERE product_name = ?", (product_name[i],))
            existing_count = cursor.fetchone()[0]

            if existing_count > 0:
                flash(f"Error: Product '{product_name[i]}' already exists!", "danger")
                conn.close()
                return redirect('/inventory')

            # Convert values to appropriate types
            free_qty = int(free_qty[i]) if free_qty[i] else 0
            booked_qty = int(booked_qty[i]) if booked_qty[i] else 0
            delivered_qty = int(delivered_qty[i]) if delivered_qty[i] else 0
            upcoming_qty = int(upcoming_qty[i]) if upcoming_qty[i] else 0
            unit_sell_price = float(unit_sell_price[i]) if unit_sell_price[i] else 0.0
            unit_buy_price = float(unit_buy_price[i]) if unit_buy_price[i] else 0.0

            # Auto-calculate on_hand
            on_hand = free_qty + booked_qty

            cursor.execute(
                "INSERT INTO inventory (product_name, on_hand, free_qty, booked_qty, delivered_qty, upcoming_qty, "
                "unit_sell_price, unit_buy_price, tags, product_type) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (product_name[i], on_hand, free_qty, booked_qty, delivered_qty, upcoming_qty, unit_sell_price,
                 unit_buy_price, tags[i], product_type[i])
            )

        conn.commit()
        conn.close()
        flash("Data saved successfully!", "success")  # Show success message
        return redirect('/inventory')

    return render_template('add_product.html')


# Route to add a new product's BOM
@app.route('/save_bom', methods=['POST'])
def save_bom():
    if not request.is_json:
        return jsonify({"error": "Invalid JSON format"}), 400
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    for entry in data:
        cursor.execute("INSERT INTO bom (product_name, component_name, quantity_required) VALUES (?, ?, ?)",
                       (entry['product_name'], entry['component_name'], entry['quantity_required']))

    conn.commit()
    conn.close()

    return jsonify({"message": "✅ BOM saved successfully."})


# API to get BOM data for a specific product
@app.route('/api/get_bom', methods=['GET'])
def get_bom():
    product_name = request.args.get('product_name')

    if not product_name:
        return jsonify({"error": "Product name is required"}), 400

    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # Allow dict-like access
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM bom WHERE product_name = ?", (product_name,))
        bom_data = cursor.fetchall()
        conn.close()

        return jsonify([dict(row) for row in bom_data])  # Convert SQLite result to JSON

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete_product", methods=["POST"])
def delete_product():
    try:
        data = request.json
        product_name = data.get("product_name")

        if not isinstance(product_name, str) or not product_name.strip():
            return jsonify({"success": False, "error": "Invalid product name"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete from BOM table first (if applicable)
        cursor.execute("DELETE FROM bom WHERE product_name = ?", (product_name,))

        # Delete from inventory table
        cursor.execute("DELETE FROM inventory WHERE product_name = ?", (product_name,))

        conn.commit()
        conn.close()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/convert_to_booked", methods=["POST"])
def convert_to_booked():
    try:
        data = request.json
        product_name = data.get("product_name")
        qty = int(data.get("qty", 0))

        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()

        # Check if this is a bundle (has BOM components)
        cursor.execute("SELECT component_name, quantity_required FROM bom WHERE product_name = ?", (product_name,))
        bom = cursor.fetchall()

        updated_others = []

        if bom:
            # 🔎 PHASE 1: Validate all components
            for component_name, quantity_required in bom:
                total_needed = qty * quantity_required
                cursor.execute("SELECT free_qty FROM inventory WHERE product_name = ?", (component_name,))
                result = cursor.fetchone()
                if not result:
                    return jsonify({"success": False, "error": f"Component '{component_name}' not found"}), 400

                free_qty = result[0]
                print(f"[DEBUG CHECK] {component_name.strip()} needs {total_needed}, has {free_qty}")

                if total_needed > free_qty:
                    print(f"[DEBUG BLOCKED] {component_name} conversion blocked! Needed: {total_needed}, Available: {free_qty}")
                    return jsonify({
                        "success": False,
                        "error": f"Not enough stock for component '{component_name}' (needs {total_needed}, has {free_qty})"
                    }), 400

            # ✅ PHASE 2: Update all components
            for component_name, quantity_required in bom:
                total_needed = qty * quantity_required
                cursor.execute("""
                    UPDATE inventory
                    SET free_qty = free_qty - ?, booked_qty = booked_qty + ?
                    WHERE product_name = ?
                """, (total_needed, total_needed, component_name))

                # Recalculate and sync free stock
                cursor.execute("SELECT on_hand, booked_qty FROM inventory WHERE product_name = ?", (component_name,))
                comp_on_hand, comp_booked_qty = cursor.fetchone()
                recalc_free = recalculate_free_stock(cursor, component_name, comp_on_hand, comp_booked_qty)

                cursor.execute("UPDATE inventory SET free_qty = ? WHERE product_name = ?", (recalc_free, component_name))

                updated_others.append({
                    "product_name": component_name,
                    "free_qty": recalc_free,
                    "booked_qty": comp_booked_qty
                })

            # ✅ Track booked_qty for the bundle itself (virtual stock)
            cursor.execute("SELECT booked_qty FROM inventory WHERE product_name = ?", (product_name,))
            row = cursor.fetchone()
            if row:
                bundle_booked_qty = row[0] + qty
                cursor.execute("UPDATE inventory SET booked_qty = ? WHERE product_name = ?", (bundle_booked_qty, product_name))
            else:
                bundle_booked_qty = qty
                cursor.execute(
                    "INSERT INTO inventory (product_name, on_hand, booked_qty, free_qty) VALUES (?, 0, ?, 0)",
                    (product_name, bundle_booked_qty)
                )

            updated_product = {
                "product_name": product_name,
                "free_qty": None,
                "booked_qty": bundle_booked_qty
            }

        else:
            # 🔧 SINGLE PRODUCT: fetch current stock
            cursor.execute("SELECT on_hand, booked_qty FROM inventory WHERE product_name = ?", (product_name,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"success": False, "error": "Product not found"}), 404

            on_hand, booked_qty = row
            current_free_qty = recalculate_free_stock(cursor, product_name, on_hand, booked_qty)

            if qty > current_free_qty:
                return jsonify({"success": False, "error": "Not enough free stock available."}), 400

            # Update booked
            booked_qty += qty
            new_free_qty = recalculate_free_stock(cursor, product_name, on_hand, booked_qty)
            new_on_hand = new_free_qty + booked_qty

            cursor.execute("""
                UPDATE inventory 
                SET booked_qty = ?, free_qty = ?, on_hand = ?
                WHERE product_name = ?
            """, (booked_qty, new_free_qty, new_on_hand, product_name))

            updated_parents = update_parent_products(cursor, product_name)
            updated_others.extend(updated_parents)

            updated_product = {
                "product_name": product_name,
                "free_qty": new_free_qty,
                "booked_qty": booked_qty
            }

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "updated_product": updated_product,
            "updated_others": updated_others
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/update_product", methods=["POST"])
def update_product():
    try:
        data = request.json
        product_name = data.get("product_name")
        if not product_name:
            return jsonify({"success": False, "error": "Missing product_name"}), 400

        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()

        # Update stock values (except free_qty, which we recalculate)
        cursor.execute("""
            UPDATE inventory
            SET on_hand = ?, booked_qty = ?, upcoming_qty = ?, 
                unit_sell_price = ?, unit_buy_price = ?
            WHERE product_name = ?
        """, (
            data.get("on_hand", 0),
            data.get("booked_qty", 0),
            data.get("upcoming_qty", 0),
            data.get("unit_sell_price", 0),
            data.get("unit_buy_price", 0),
            product_name
        ))

        # Fetch updated stock after changes
        cursor.execute("SELECT on_hand, booked_qty FROM inventory WHERE product_name = ?", (product_name,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Product not found"}), 404

        on_hand, booked_qty = row
        free_qty = recalculate_free_stock(cursor, product_name, on_hand, booked_qty)

        # Update inventory with recalculated free_qty
        cursor.execute("UPDATE inventory SET free_qty = ? WHERE product_name = ?", (free_qty, product_name))

        # ✅ UPDATE PARENT PRODUCTS THAT DEPEND ON THIS COMPONENT
        updated_parents = update_parent_products(cursor, product_name) # For components
        updated_components = update_component_products(cursor, product_name)  # For bundles

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "free_qty": free_qty,
            "booked_qty": booked_qty,
            "updated_parents": updated_parents,  # Send updated parent products back to frontend
            "updated_components": updated_components
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def recalculate_free_stock(cursor, product_name, on_hand, booked_qty):
    """Recalculate free stock based on BOM components."""
    cursor.execute("SELECT component_name, quantity_required FROM bom WHERE product_name = ?", (product_name,))
    bom_components = cursor.fetchall()

    if bom_components:
        min_possible = float('inf')
        component_names = [component for component, _ in bom_components]

        # Fetch all component stocks in one query
        cursor.execute(
            f"SELECT product_name, free_qty FROM inventory WHERE product_name IN ({','.join(['?'] * len(component_names))})",
            component_names)
        component_stocks = dict(cursor.fetchall())  # Convert to dict {component_name: free_qty}

        for component_name, quantity_required in bom_components:
            component_free_qty = component_stocks.get(component_name, 0)
            if quantity_required > 0:
                min_possible = min(min_possible, component_free_qty // quantity_required)

        return min_possible if min_possible != float('inf') else 0
    else:
        return max(on_hand - booked_qty, 0)


def update_parent_products(cursor, component_name):
    """Update all parent products that use the given component."""
    cursor.execute("SELECT product_name FROM bom WHERE component_name = ?", (component_name,))
    parent_products = [row[0] for row in cursor.fetchall()]

    if not parent_products:
        return []

    updated_parents = []
    for parent_product in parent_products:
        cursor.execute("SELECT on_hand, booked_qty FROM inventory WHERE product_name = ?", (parent_product,))
        row = cursor.fetchone()
        if row:
            parent_on_hand, parent_booked_qty = row
            parent_free_qty = recalculate_free_stock(cursor, parent_product, parent_on_hand, parent_booked_qty)

            cursor.execute("UPDATE inventory SET free_qty = ? WHERE product_name = ?",
                           (parent_free_qty, parent_product))
            updated_parents.append({"product_name": parent_product, "free_qty": parent_free_qty})

    return updated_parents


def update_component_products(cursor, bundle_name):
    """Update free_qty of components used by this bundle product."""
    cursor.execute("SELECT component_name FROM bom WHERE product_name = ?", (bundle_name,))
    components = [row[0] for row in cursor.fetchall()]

    if not components:
        return []

    updated_components = []
    for component in components:
        cursor.execute("SELECT on_hand, booked_qty FROM inventory WHERE product_name = ?", (component,))
        row = cursor.fetchone()
        if row:
            on_hand, booked_qty = row
            free_qty = recalculate_free_stock(cursor, component, on_hand, booked_qty)
            cursor.execute("UPDATE inventory SET free_qty = ? WHERE product_name = ?", (free_qty, component))
            updated_components.append({"product_name": component, "free_qty": free_qty})

    return updated_components


# Action: Delivered
@app.route("/deliver_product", methods=["POST"])
def deliver_product():
    try:
        data = request.json
        product_name = data.get("product_name")
        qty = int(data.get("qty", 0))

        if not product_name or qty <= 0:
            return jsonify({"success": False, "error": "Invalid product or quantity."}), 400

        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()

        updated = []

        # ✅ Update main product booked → delivered
        cursor.execute("SELECT booked_qty, delivered_qty FROM inventory WHERE product_name = ?", (product_name,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Product not found"}), 404

        booked, delivered = row
        if qty > booked:
            return jsonify({"success": False, "error": "Not enough booked quantity to deliver."}), 400

        booked -= qty
        delivered += qty

        cursor.execute("UPDATE inventory SET booked_qty = ?, delivered_qty = ? WHERE product_name = ?",
                       (booked, delivered, product_name))

        updated.append({
            "product_name": product_name,
            "booked_qty": booked,
            "delivered_qty": delivered
        })

        # ✅ If bundle, update components too
        cursor.execute("SELECT component_name, quantity_required FROM bom WHERE product_name = ?", (product_name,))
        components = cursor.fetchall()
        for comp_name, qty_needed in components:
            total_qty = qty_needed * qty
            cursor.execute("SELECT booked_qty, delivered_qty FROM inventory WHERE product_name = ?", (comp_name,))
            b, d = cursor.fetchone()
            b -= total_qty
            d += total_qty

            cursor.execute("UPDATE inventory SET booked_qty = ?, delivered_qty = ? WHERE product_name = ?",
                           (b, d, comp_name))

            updated.append({
                "product_name": comp_name,
                "booked_qty": b,
                "delivered_qty": d
            })

        conn.commit()
        conn.close()

        return jsonify({"success": True, "updated": updated})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/return_product", methods=["POST"])
def return_product():
    try:
        data = request.json
        product_name = data.get("product_name")
        qty = int(data.get("qty", 0))

        if not product_name or qty <= 0:
            return jsonify({"success": False, "error": "Invalid product or quantity."}), 400

        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()

        updated_items = []

        # 1️⃣ Update main product
        cursor.execute("SELECT delivered_qty, free_qty FROM inventory WHERE product_name = ?", (product_name,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Product not found"}), 404

        delivered, free = row
        if qty > delivered:
            return jsonify({"success": False, "error": "Not enough delivered quantity to return."}), 400

        new_delivered = delivered - qty
        new_free = free + qty

        cursor.execute("UPDATE inventory SET delivered_qty = ?, free_qty = ? WHERE product_name = ?",
                       (new_delivered, new_free, product_name))

        updated_items.append({
            "product_name": product_name,
            "free_qty": new_free,
            "delivered_qty": new_delivered
        })

        # 2️⃣ Check BOM (if it's a bundle, update components)
        cursor.execute("SELECT component_name, quantity_required FROM bom WHERE product_name = ?", (product_name,))
        components = cursor.fetchall()

        for comp_name, qty_required in components:
            total_return = qty * qty_required

            cursor.execute("SELECT delivered_qty, free_qty FROM inventory WHERE product_name = ?", (comp_name,))
            d, f = cursor.fetchone()
            d -= total_return
            f += total_return

            cursor.execute("UPDATE inventory SET delivered_qty = ?, free_qty = ? WHERE product_name = ?",
                           (d, f, comp_name))

            updated_items.append({
                "product_name": comp_name,
                "free_qty": f,
                "delivered_qty": d
            })

        conn.commit()
        conn.close()

        return jsonify({"success": True, "updated_items": updated_items})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/update_note", methods=["POST"])
def update_note():
    data = request.get_json()
    product_name = data.get("product_name")
    note = data.get("note", "")

    if not product_name:
        return jsonify({"success": False, "error": "Missing product name"}), 400

    conn = sqlite3.connect("stock.db")
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE inventory SET cell_notes = ? WHERE product_name = ?", (note, product_name))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/crm')
def crm():
    return render_template('crm.html')


@app.route('/api/crm', methods=['GET', 'POST'])
def crm_data():
    if request.method == 'POST':
        data = request.get_json()
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO leads (customer, product, status, sales_person, amount, date, source, mobile, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['customer'],
                data['product'],
                data['status'],
                data['sales_person'],
                float(data['amount']),
                data['date'],
                data['source'],
                data['mobile'],
                data['email'] if data['email'] else None
            ))
            conn.commit()
            conn.close()
            return jsonify({"success": True}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # For GET
    conn = get_db_connection()
    leads = conn.execute('SELECT * FROM leads').fetchall()
    conn.close()
    return jsonify([dict(lead) for lead in leads])


@app.route('/api/summary')
def summary():
    conn = get_db_connection()
    leads = conn.execute('SELECT status, amount FROM leads').fetchall()
    conn.close()

    total_leads = len(leads)
    success = sum(1 for lead in leads if lead['status'].lower() == 'success')
    fail = sum(1 for lead in leads if lead['status'].lower() == 'fail')
    follow_up = sum(1 for lead in leads if 'follow' in lead['status'].lower())
    total_amount = sum(float(lead['amount']) for lead in leads)

    return jsonify({
        'total_leads': total_leads,
        'success': success,
        'fail': fail,
        'follow_up': follow_up,
        'total_amount': total_amount
    })

@app.route("/sync_sales", methods=["GET"])
def sync_sales():
    data = get_sales_orders()
    if not data or "sales_orders" not in data:
        return jsonify([])

    items = []
    for order in data["sales_orders"]:
        for line in order.get("transaction_lines_attributes", []):
            product = line.get("product")
            if product:
                items.append({
                    "name": product.get("name"),
                    "quantity": line.get("quantity")
                })
    return jsonify(items)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
