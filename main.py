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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            unit_buy_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
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


@app.route("/check_stock", methods=["GET"])
def check_stock():
    """Check stock from the inventory table"""
    name = request.args.get("name", "").strip().lower()
    print(f"Searching for: {name}")  # Debugging

    with sqlite3.connect("stock.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
                    SELECT product_name, quantity, unit_buy_price, tags 
                    FROM inventory 
                    WHERE LOWER(product_name) LIKE LOWER(?)
                """, ('%' + name + '%',))
        products = cursor.fetchall()

    if not products:
        return jsonify({"message": "No products found"}), 404

    return jsonify([
        {"name": p[0], "stock": p[1], "price": p[2], "tags": p[3].split(", ") if p[3] else []}
        for p in products
    ])


@app.route("/check_stock/<product_name>", methods=["GET"])
def check_bom_stock(product_name):
    """Check if a product can be produced based on available BOM stock"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get BOM for the requested product
    cursor.execute("SELECT material_name, quantity_required FROM bom WHERE product_name = ?", (product_name,))
    bom_items = cursor.fetchall()

    if not bom_items:
        return jsonify({"message": "Product not found or BOM not defined"}), 404

    # Get available stock for each material
    stock_data = {}
    for row in bom_items:
        material_name, quantity_required = row
        cursor.execute("SELECT quantity FROM inventory WHERE product_name = ?", (material_name,))
        stock_result = cursor.fetchone()
        stock_data[material_name] = stock_result[0] if stock_result else 0

    conn.close()

    # Calculate max producible units
    max_producible = min(stock_data[mat] // qty for mat, qty in stock_data.items())

    return jsonify({
        "product_name": product_name,
        "max_producible": max_producible,
        "stock_details": stock_data
    })


@app.route("/api/get_stock", methods=["GET"])
def get_stock():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_name, unit_buy_price, quantity, tags FROM inventory")
    stock = [
        {
            "id": row["id"],
            "name": row["product_name"],
            "price": row["unit_buy_price"],
            "qty": row["quantity"],
            "tags": row["tags"]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(stock)


@app.route('/add_product')
def add_product_page():
    return render_template('add_product.html')


@app.route('/inventory', methods=['GET', 'POST'])
def inventory_page():
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.get_json()

        if not data or "products" not in data:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400

        products = data["products"]

        if not isinstance(products, list) or len(products) == 0:
            return jsonify({'success': False, 'error': 'No products provided'}), 400

        # Insert products into the database
        for product in products:
            product_name = product.get("product-name")
            unit_buy_price = product.get("unit-price")
            quantity = product.get("quantity")
            tags = product.get("tags")

            # Validate that no fields are missing
            if not all([product_name, unit_buy_price, quantity, tags]):
                return jsonify({'success': False, 'error': 'All fields must be filled'}), 400

            cursor.execute(
                "INSERT INTO inventory (product_name, unit_buy_price, quantity, tags) VALUES (?, ?, ?, ?)",
                (product_name, unit_buy_price, quantity, tags)
            )

            # Debugging: Print the received form data
            print("Received Data:")
            print("Product Names:", product_name)
            print("Unit Buy Prices:", unit_buy_price)
            print("Quantities:", quantity)
            print("Tags:", tags)

        conn.commit()

        # Fetch updated inventory after insertion
        cursor.execute("SELECT * FROM inventory ORDER BY id DESC")
        stock_data = cursor.fetchall()
        conn.close()

        return jsonify({"success": True, "stock_data": stock_data})

    # If GET request, return the stock inventory
    cursor.execute("SELECT * FROM inventory ORDER BY id DESC")
    stock_data = cursor.fetchall()
    conn.close()

    return render_template('inventory.html', stock_data=stock_data)


# Route to add a new product's BOM
@app.route("/add_product", methods=["POST"])
def add_product():
    """Add or update product in the inventory table"""
    data = request.get_json()
    product_name = data.get("name")
    stock = int(data.get("stock", 0))
    unit_buy_price = float(data.get("price", 0))
    tags = data.get("tags", "")
    materials = data.get("materials", [])  # List of {material_name, quantity_required}

    if not product_name or stock < 0 or unit_buy_price < 0:
        return jsonify({"message": "Invalid input"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert or update inventory
    cursor.execute("""
            INSERT INTO inventory (product_name, unit_buy_price, quantity, tags)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(product_name) DO UPDATE 
            SET quantity = quantity + ?, unit_buy_price = ?, tags = ?
        """, (product_name, unit_buy_price, stock, tags, stock, unit_buy_price, tags))

    # Insert BOM (delete existing BOM first to avoid duplicates)
    cursor.execute("DELETE FROM bom WHERE product_name = ?", (product_name,))

    for material in materials:
        cursor.execute("""
                INSERT INTO bom (product_name, material_name, quantity_required)
                VALUES (?, ?, ?)
            """, (product_name, material["name"], material["quantity"]))

    conn.commit()
    conn.close()

    return jsonify({"message": f"Product '{product_name}' added/updated successfully!"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
