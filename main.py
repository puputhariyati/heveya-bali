from flask import Flask, request, jsonify, render_template, redirect
import sqlite3

app = Flask(__name__)


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


@app.route('/inventory', methods=['GET', 'POST'])
def inventory_page():
    if request.method == 'POST':
        product_name = request.form.getlist('product_name')
        unit_buy_price = request.form.getlist('unit_buy_price')
        quantity = request.form.getlist('quantity')
        tags = request.form.getlist('tags')

        conn = sqlite3.connect('stock.db')
        cursor = conn.cursor()

        for i in range(len(product_name)):
            cursor.execute(
                "INSERT INTO inventory (product_name, unit_buy_price, quantity, tags) VALUES (?, ?, ?, ?)",
                (product_name[i], unit_buy_price[i], quantity[i], tags[i])
            )

        conn.commit()
        conn.close()
        return redirect('/inventory')

    return render_template('inventory.html')

@app.route("/add_product", methods=["POST"])
def add_product():
    data = request.get_json()
    name = data.get("name")
    stock = int(data.get("stock", 0))
    price = int(data.get("price", 0))
    tags = data.get("tags", "")

    if not name or stock < 0 or price < 0:
        return jsonify({"message": "Invalid input"}), 400

    with sqlite3.connect("stock.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, stock, price, tags)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET stock = stock + ?, price = ?, tags = ?
        """, (name, stock, price, tags, stock, price, tags))
        conn.commit()

    return jsonify({"message": f"{name} added successfully!"})


@app.route("/check_stock", methods=["GET"])
def check_stock():
    name = request.args.get("name", "")

    with sqlite3.connect("stock.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, stock, price, tags FROM products WHERE name LIKE ?", ('%' + name + '%',))
        products = cursor.fetchall()

    if not products:
        return jsonify({"message": "No products found"}), 404

    return jsonify([
        {"name": p[0], "stock": p[1], "price": p[2], "tags": p[3].split(", ")} for p in products
    ])


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
