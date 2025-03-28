import os
import sqlite3
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
            tags TEXT
        )
    ''')

    # Create BOM table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            material_name TEXT NOT NULL,
            quantity_required INTEGER NOT NULL
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
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch inventory data
    cursor.execute("SELECT * FROM inventory")
    stock_data = cursor.fetchall()

    # Fetch BOM components and their required quantity
    cursor.execute("SELECT product, component, quantity FROM bom")
    bom_data = cursor.fetchall()

    # Convert BOM to a dictionary: {product_name: [(component_name, required_qty), ...]}
    bom_dict = {}
    for product, component, quantity in bom_data:
        if product not in bom_dict:
            bom_dict[product] = []
        bom_dict[product].append((component, quantity))

    # Convert inventory to dictionary for quick lookup
    inventory_dict = {row["product_name"]: dict(row) for row in stock_data}

    # Process stock with BOM dependencies
    stock = []
    for row in stock_data:
        product_name = row["product_name"]
        free_qty = row["free_qty"]  # Default from DB
        on_hand = row["on_hand"]  # Default from DB
        booked_qty = row["booked_qty"]  # Default from DB
        delivered_qty = row["delivered_qty"]  # Default from DB

        # If the product has a BOM, calculate its free_qty dynamically
        if product_name in bom_dict:
            min_possible = float('inf')  # Start with a large number
            for component, required_qty in bom_dict[product_name]:
                component_stock = inventory_dict.get(component, {}).get("free_qty", 0)
                if required_qty > 0:
                    min_possible = min(min_possible, component_stock // required_qty)

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
            "booked_qty": booked_qty,
            "delivered_qty": delivered_qty,
            "upcoming_qty": row["upcoming_qty"],
            "unit_sell_price": row["unit_sell_price"],
            "unit_buy_price": row["unit_buy_price"],
            "tags": row["tags"]
        })

    conn.close()

    # Add cache-busting headers
    response = jsonify(stock)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"

    return response


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
            free = int(free_qty[i]) if free_qty[i] else 0
            booked = int(booked_qty[i]) if booked_qty[i] else 0
            delivered = int(delivered_qty[i]) if delivered_qty[i] else 0
            upcoming = int(upcoming_qty[i]) if upcoming_qty[i] else 0
            sell_price = float(unit_sell_price[i]) if unit_sell_price[i] else 0.0
            buy_price = float(unit_buy_price[i]) if unit_buy_price[i] else 0.0

            # Auto-calculate on_hand
            on_hand = booked + free

            cursor.execute(
                "INSERT INTO inventory (product_name, on_hand, free_qty, booked_qty, delivered_qty, upcoming_qty, "
                "unit_sell_price, unit_buy_price, tags) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (product_name[i], on_hand, free, booked, delivered, upcoming, sell_price, buy_price, tags[i])
            )

        conn.commit()
        conn.close()
        flash("Data saved successfully!", "success")  # Show success message
        return redirect('/inventory')

    return render_template('add_product.html')


# Route to add a new product's BOM
@app.route('/save_bom', methods=['POST'])
def save_bom():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    for entry in data:
        cursor.execute("INSERT INTO bom (product, component, quantity) VALUES (?, ?, ?)",
                       (entry['product'], entry['component'], entry['quantity']))

    conn.commit()
    conn.close()

    return jsonify({"message": "✅ BOM saved successfully."})


# API to get BOM data for a specific product
@app.route('/api/get_bom', methods=['GET'])
def get_bom():
    product_name = request.args.get('product')

    if not product_name:
        return jsonify({"error": "Product name is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bom WHERE product = ?", (product_name,))
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

        if not product_name:
            return jsonify({"success": False, "error": "Missing product name"}), 400

        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()

        # Delete from BOM table first (if applicable)
        cursor.execute("DELETE FROM bom WHERE product = ?", (product_name,))

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

        for component, required_qty in bom_components:
            component_free_qty = component_stocks.get(component, 0)
            if required_qty > 0:
                min_possible = min(min_possible, component_free_qty // required_qty)

        return min_possible if min_possible != float('inf') else 0
    else:
        return max(on_hand - booked_qty, 0)


def update_parent_products(cursor, component_name):
    """Update all parent products that use the given component."""
    cursor.execute("SELECT product FROM bom WHERE component = ?", (component_name,))
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

        # ✅ Allow converting all available free stock
        if qty_to_convert > free_qty:
            qty_to_convert = free_qty  # Convert all available free stock

        # ✅ Update correct fields
        new_free_qty = free_qty - qty_to_convert  # Reduce free stock
        new_booked_qty = booked_qty + qty_to_convert  # Increase booked stock

        cursor.execute("""
            UPDATE inventory
            SET free_qty = ?, booked_qty = ?
            WHERE product_name = ?
        """, (new_free_qty, new_booked_qty, product_name))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "new_free_qty": new_free_qty,
            "new_booked_qty": new_booked_qty
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
