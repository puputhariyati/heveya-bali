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
            sold_qty INTEGER NOT NULL DEFAULT 0,
            free_qty INTEGER NOT NULL DEFAULT 0,
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
        sold_qty = row["sold_qty"]  # Default from DB

        # If the product has a BOM, calculate its free_qty dynamically
        if product_name in bom_dict:
            min_possible = float('inf')  # Start with a large number
            for component, required_qty in bom_dict[product_name]:
                component_stock = inventory_dict[component]["free_qty"] if component in inventory_dict else 0
                if required_qty > 0:
                    min_possible = min(min_possible, component_stock // required_qty)

            free_qty = min_possible if min_possible != float('inf') else 0  # Ensure valid value
            # Dynamically calculate on_hand: it includes sold, free, and component availability
            on_hand = sold_qty + free_qty

        stock.append({
            "id": row["id"],
            "product_name": product_name,
            "sold_qty": row["sold_qty"],
            "free_qty": free_qty,  # Updated dynamically
            "on_hand": on_hand,  # Updated dynamically
            "upcoming_qty": row["upcoming_qty"],
            "unit_sell_price": row["unit_sell_price"],
            "unit_buy_price": row["unit_buy_price"],
            "tags": row["tags"]
        })

    conn.close()
    return jsonify(stock)


@app.route('/inventory', methods=['GET', 'POST'])
def inventory_page():
    if request.method == 'POST':
        product_name = request.form.getlist('product_name')
        sold_qty = request.form.getlist('sold_qty')
        free_qty = request.form.getlist('free_qty')
        upcoming_qty = request.form.getlist('upcoming_qty')
        unit_sell_price = request.form.getlist('unit_sell_price')
        unit_buy_price = request.form.getlist('unit_buy_price')
        tags = request.form.getlist('tags')

        # Check if any field is empty before inserting
        if not all(product_name) or not all(unit_buy_price) or not all(tags):
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

            # Convert values to integers (handle empty inputs)
            sold = int(sold_qty[i]) if sold_qty[i] else 0
            free = int(free_qty[i]) if free_qty[i] else 0
            upcoming = int(upcoming_qty[i]) if upcoming_qty[i] else 0
            sell_price = float(unit_sell_price[i]) if unit_sell_price[i] else 0.0
            buy_price = float(unit_buy_price[i]) if unit_buy_price[i] else 0.0

            # Auto-calculate on_hand
            on_hand = sold + free

            cursor.execute(
                "INSERT INTO inventory (product_name, on_hand, sold_qty, free_qty, upcoming_qty, unit_sell_price, "
                "unit_buy_price, tags)"
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (product_name[i], on_hand, sold, free, upcoming, sell_price, buy_price, tags[i])
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
            SET on_hand = ?, sold_qty = ?, upcoming_qty = ?, 
                unit_sell_price = ?, unit_buy_price = ?
            WHERE product_name = ?
        """, (
            data.get("on_hand", 0),
            data.get("sold_qty", 0),
            data.get("upcoming_qty", 0),
            data.get("unit_sell_price", 0),
            data.get("unit_buy_price", 0),
            product_name
        ))

        # Fetch updated stock after changes
        cursor.execute("SELECT on_hand, sold_qty FROM inventory WHERE product_name = ?", (product_name,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Product not found"}), 404

        on_hand, sold_qty = row
        free_qty = recalculate_free_stock(cursor, product_name, on_hand, sold_qty)

        # Update inventory with recalculated free_qty
        cursor.execute("UPDATE inventory SET free_qty = ? WHERE product_name = ?", (free_qty, product_name))

        # ✅ UPDATE PARENT PRODUCTS THAT DEPEND ON THIS COMPONENT
        updated_parents = update_parent_products(cursor, product_name)

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "free_qty": free_qty,
            "sold_qty": sold_qty,
            "updated_parents": updated_parents  # Send updated parent products back to frontend
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def recalculate_free_stock(cursor, product_name, on_hand, sold_qty):
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
        return max(on_hand - sold_qty, 0)


def update_parent_products(cursor, component_name):
    """Update all parent products that use the given component."""
    cursor.execute("SELECT product FROM bom WHERE component = ?", (component_name,))
    parent_products = [row[0] for row in cursor.fetchall()]

    if not parent_products:
        return []

    updated_parents = []
    for parent_product in parent_products:
        cursor.execute("SELECT on_hand, sold_qty FROM inventory WHERE product_name = ?", (parent_product,))
        row = cursor.fetchone()
        if row:
            parent_on_hand, parent_sold_qty = row
            parent_free_qty = recalculate_free_stock(cursor, parent_product, parent_on_hand, parent_sold_qty)

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
        cursor.execute("SELECT free_qty, sold_qty FROM inventory WHERE product_name = ?", (product_name,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Product not found"}), 404

        free_qty, sold_qty = row

        # ✅ Allow converting all available free stock
        if qty_to_convert > free_qty:
            qty_to_convert = free_qty  # Convert all available free stock

        # ✅ Update correct fields
        new_free_qty = free_qty - qty_to_convert  # Reduce free stock
        new_sold_qty = sold_qty + qty_to_convert  # Increase booked stock

        cursor.execute("""
            UPDATE inventory
            SET free_qty = ?, sold_qty = ?
            WHERE product_name = ?
        """, (new_free_qty, new_sold_qty, product_name))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "new_free_qty": new_free_qty,
            "new_sold_qty": new_sold_qty
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
