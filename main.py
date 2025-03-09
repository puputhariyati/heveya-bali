import os
import sqlite3
from flask import Flask, request, jsonify, render_template, redirect, flash
from dotenv import load_dotenv

load_dotenv("key.env")  # Load environment variables from .env file

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")  # Retrieve secret key from .env

# Ensure the database and table are created
def init_db():
    conn = sqlite3.connect('stock.db')
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


@app.route('/add_product')
def add_product_page():
    return render_template('add_product.html')


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


@app.route('/inventory', methods=['GET', 'POST'])
def inventory_page():
    if request.method == 'POST':
        product_name = request.form.getlist('product_name')
        unit_buy_price = request.form.getlist('unit_buy_price')
        quantity = request.form.getlist('quantity')
        tags = request.form.getlist('tags')

        # Debugging: Print the received form data
        print("Received Data:")
        print("Product Names:", product_name)
        print("Unit Buy Prices:", unit_buy_price)
        print("Quantities:", quantity)
        print("Tags:", tags)

        # Check if any field is empty before inserting
        if not all(product_name) or not all(unit_buy_price) or not all(quantity) or not all(tags):
            flash("Error: All fields must be filled", "danger")
            return redirect('/inventory')

        conn = sqlite3.connect('stock.db')
        cursor = conn.cursor()

        for i in range(len(product_name)):
            cursor.execute(
                "INSERT INTO inventory (product_name, unit_buy_price, quantity, tags) VALUES (?, ?, ?, ?)",
                (product_name[i], unit_buy_price[i], quantity[i], tags[i])
            )

        conn.commit()
        conn.close()
        flash("Data saved successfully!", "success")  # Show success message
        return redirect('/inventory')

    return render_template('inventory.html')

@app.route("/add_product", methods=["POST"])
def add_product(quantity=None):
    """Add or update product in the inventory table"""
    data = request.get_json()
    product_name = data.get("name")
    stock = int(data.get("stock", 0))
    unit_buy_price = float(data.get("price", 0))
    tags = data.get("tags", "")

    if not product_name or quantity < 0 or unit_buy_price < 0:
        return jsonify({"message": "Invalid input"}), 400

    with sqlite3.connect("stock.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inventory (product_name, unit_buy_price, quantity, tags)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(product_name) DO UPDATE 
            SET quantity = quantity + ?, unit_buy_price = ?, tags = ?
        """, (product_name, unit_buy_price, quantity, tags, quantity, unit_buy_price, tags))
        conn.commit()

    return jsonify({"message": f"{product_name} added/updated successfully!"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
