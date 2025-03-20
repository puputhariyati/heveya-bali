import os
import sqlite3
from flask import Flask, request, jsonify, render_template, redirect, flash, json
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

    # # Drop existing inventory table
    # cursor.execute("DROP TABLE IF EXISTS inventory;")

    # Recreate table with correct schema
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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
