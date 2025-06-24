import sqlite3

def save_quote_to_db(data):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()

    # Extract values from incoming data
    discount = data['discount']
    full_amount = data['full_amount']
    avg_disc = (discount / full_amount) * 100 if full_amount else 0

    # Insert sales quote header
    cursor.execute('''
        INSERT INTO sales_quotes (
            date, customer, phone, full_amount, discount, avg_disc,
            grand_total, margin, status, ETD
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['date'],
        data['customer'],
        data['phone'],
        full_amount,
        discount,
        avg_disc,
        data['grand_total'],
        data['margin'],
        data['status'],
        data['ETD']
    ))
    quote_id = cursor.lastrowid  # ✅ Move this inside the function

    # # Insert each item
    # for item in data['items']:
    #     cursor.execute('''
    #         INSERT INTO sales_quote_items (
    #             quote_id, description, qty, unit, unit_price, discount,
    #             discounted_price, amount, notes, full_amount, unit_cost,
    #             total_cost, margin
    #         )
    #         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #     ''', (
    #         quote_id,
    #         item['description'],
    #         item['qty'],
    #         item['unit'],
    #         item['unit_price'],
    #         item['discount'],
    #         item['discounted_price'],
    #         item['amount'],
    #         item['notes'],
    #         item['full_amount'],
    #         item['unit_cost'],
    #         item['total_cost'],
    #         item['margin']
    #     ))

    conn.commit()
    conn.close()
    return {'status': 'success'}

