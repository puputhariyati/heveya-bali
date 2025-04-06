import os
import sqlite3
import traceback
from flask import Flask, request, jsonify, render_template, redirect, flash
from dotenv import load_dotenv

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
                    if quantity_required > 0 and component_stock > 0:
                        min_possible = min(min_possible, component_stock // quantity_required)

                free_qty = min_possible if min_possible != float('inf') else 0  # Ensure valid value
            else:
                free_qty = row["free_qty"]  # Keep the original DB value for non-BOM items

            # Ensure on_hand is properly recalculated
            on_hand = row["on_hand"]  # Default from DB
            if product_name in bom_dict:
                on_hand = free_qty + booked_qty  # On-hand should be the calculated free stock

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
                "product_type": row["product_type"]
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
        updated_parents = update_parent_products(cursor, product_name)

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "free_qty": free_qty,
            "booked_qty": booked_qty,
            "updated_parents": updated_parents  # Send updated parent products back to frontend
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def recalculate_free_stock(cursor, product_name, on_hand, booked_qty):
    """Recalculate free stock based on BOM components."""
    cursor.execute("SELECT component, quantity FROM bom WHERE product = ?", (product_name,))
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
    cursor.execute("SELECT product_name FROM bom WHERE component = ?", (component_name,))
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


@app.route("/convert_to_booked", methods=["POST"])
def convert_to_booked():
    try:
        data = request.json
        product_name = data.get("product_name")
        qty_to_convert = int(data.get("qty", 0))

        print(f"🔹 Received request: {product_name}, Qty: {qty_to_convert}")  # Debug

        if qty_to_convert <= 0:
            return jsonify({"success": False, "error": "Invalid quantity"}), 400

        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()

        # Fetch current stock levels
        cursor.execute("SELECT free_qty, booked_qty FROM inventory WHERE product_name = ?", (product_name,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Product not found"}), 404

        free_qty, booked_qty = row
        print(f"🔹 Before update - Free: {free_qty}, Booked: {booked_qty}")  # Debug

        # ✅ Allow converting all available free stock
        if qty_to_convert > free_qty:
            qty_to_convert = free_qty  # Convert all available free stock

        # ✅ Update correct fields
        new_free_qty = free_qty - qty_to_convert  # Reduce free stock
        new_booked_qty = booked_qty + qty_to_convert  # Increase booked stock

        print(f"🔹 After update - Free: {new_free_qty}, Booked: {new_booked_qty}")  # Debug

        cursor.execute("""
            UPDATE inventory
            SET free_qty = ?, booked_qty = ?
            WHERE product_name = ?
        """, (new_free_qty, new_booked_qty, product_name))

        # 🔄 Check if this is a bundle product
        cursor.execute("SELECT product_type FROM inventory WHERE product_name = ?", (product_name,))
        product_type = cursor.fetchone()
        if product_type and product_type[0] == 'bundle':
            # Get components from BOM
            cursor.execute("SELECT component_name, quantity_required FROM bom WHERE product_name = ?", (product_name,))
            components = cursor.fetchall()

            for component_name, quantity_required in components:
                total_required = qty_to_convert * quantity_required

                # Fetch component stock
                cursor.execute("SELECT free_qty, booked_qty FROM inventory WHERE product_name = ?", (component_name,))
                comp_row = cursor.fetchone()
                if comp_row:
                    comp_free, comp_booked = comp_row
                    new_comp_free = max(comp_free - total_required, 0)
                    new_comp_booked = comp_booked + total_required

                    # Update component stock
                    cursor.execute("""
                        UPDATE inventory
                        SET free_qty = ?, booked_qty = ?
                        WHERE product_name = ?
                    """, (new_comp_free, new_comp_booked, component_name))

                    # Update affected parents of this component
                    update_parent_products(cursor, component_name)

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "new_free_qty": new_free_qty,
            "new_booked_qty": new_booked_qty
        })

    except Exception as e:
        print(f"❌ Error: {e}")  # Debug
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
