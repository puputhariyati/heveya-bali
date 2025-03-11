import tkinter as tk
from tkinter import messagebox

# Define your components and stock
components = {
    #block base
    "(D70) 210 x 80 x 15cm (full piece) (with inner cover)": 1,
    "(D80) 210 x 80 x 15cm (full piece) (with inner cover)": 1,

    "(D70) 200 x 90 x 15cm (full piece) (with inner cover)": 2,
    "(D80) 200 x 90 x 15cm (full piece) (with inner cover)": 6,
    "(D95) 200 x 90 x 15cm (full piece) (with inner cover)": 2,

    "(D70) 200 x 100 x 15cm (full piece) (with inner cover)": 2,
    "(D80) 200 x 100 x 15cm (full piece) (with inner cover)": 6,
    "(D95) 200 x 100 x 15cm (full piece) (with inner cover)": 2,

    "(D70) 200 x 160 x 15cm (full piece) (with inner cover)": 2,
    "(D80) 200 x 160 x 15cm (full piece) (with inner cover)": 6,
    "(D95) 200 x 160 x 15cm (full piece) (with inner cover)": 2,

    "Heveya Natural Organic Latex 15cm - King - Medium": 6,
    "Heveya Natural Organic Latex 5cm - King - Soft":6,
    "Heveya Bamboo Fiber Quilted Outer Cover 2 - King":9,

    #topper (inner & outer)
    "(D65) 200 x 90 x 5cm (full piece) (with inner cover)": 8,
    "(D65) 200 x 100 x 5cm (full piece) (with inner cover)": 8,
    "(D65) 200 x 160 x 5cm (full piece) (with inner cover)": 6,
    "(D65) 200 x 180 x 5cm (full piece) (with inner cover)": 6,
    "(D65) 200 x 200 x 5cm (full piece) (with inner cover)": 6,

    "(D80) 200 x 90 x 5cm (full piece) (with inner cover)": 8,
    "(D80) 200 x 100 x 5cm (full piece) (with inner cover)": 8,
    "(D80) 200 x 160 x 5cm (full piece) (with inner cover)": 6,


    #quilted cover (mattress & topper)
    "quilted cover 200 x 90 x 5cm": 2,
    "quilted cover 200 x 160 x 5cm": 2,
    "quilted cover 200 x 180 x 5cm": 2,
    "quilted cover 200 x 200 x 5cm": 2,

    "quilted cover 200 x 90 x 15cm": 2,
    "quilted cover 200 x 160 x 15cm": 2,
    "quilted cover 200 x 180 x 15cm": 2,
    "quilted cover 200 x 200 x 15cm": 2,

    "quilted cover 200 x 90 x 20cm": 2,
    "quilted cover 200 x 160 x 20cm": 2,
    "quilted cover 200 x 180 x 20cm": 2,
    "quilted cover 200 x 200 x 20cm": 2,
}

# Define the Bill of Materials (BOM) for each product
products = {
    "Heveya Mattress III - Super King (200x200) - Soft": {
        "(D70) 200 x 100 x 15cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 100 x 5cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 200 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 200 x 20cm": 1,
        "quilted cover 200 x 200 x 5cm": 1,
    },
    "Heveya Mattress III - Super King (200x200) - Medium": {
        "(D80) 200 x 100 x 15cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 100 x 5cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 200 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 200 x 20cm": 1,
        "quilted cover 200 x 200 x 5cm": 1,
    },
    "Heveya Mattress III - Super King (200x200) - Firm": {
        "(D95) 200 x 100 x 15cm (full piece) (with inner cover)": 2,
        "(D80) 200 x 100 x 5cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 200 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 200 x 20cm": 1,
        "quilted cover 200 x 200 x 5cm": 1,
    },

    "Heveya Mattress III - King (180x200) - Soft": {
        "(D70) 200 x 90 x 15cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 90 x 5cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 180 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 180 x 20cm": 1,
        "quilted cover 200 x 180 x 5cm": 1,
    },
    "Heveya Mattress III - King (180x200) - Medium": {
        "(D80) 200 x 90 x 15cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 90 x 5cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 180 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 180 x 20cm": 1,
        "quilted cover 200 x 180 x 5cm": 1,
    },
    "Heveya Mattress III - King (180x200) - Firm": {
        "(D95) 200 x 90 x 15cm (full piece) (with inner cover)": 2,
        "(D80) 200 x 90 x 5cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 180 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 180 x 20cm": 1,
        "quilted cover 200 x 180 x 5cm": 1,
    },

    "Heveya Mattress III - Queen (160x200) - Soft": {
        "(D70) 200 x 160 x 15cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 160 x 5cm (full piece) (with inner cover)": 2,
        "quilted cover 200 x 160 x 20cm": 1,
        "quilted cover 200 x 160 x 5cm": 1,
    },
    "Heveya Mattress III - Queen (160x200) - Medium": {
        "(D80) 200 x 160 x 15cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 160 x 5cm (full piece) (with inner cover)": 2,
        "quilted cover 200 x 160 x 20cm": 1,
        "quilted cover 200 x 160 x 5cm": 1,
    },
    "Heveya Mattress III - Queen (160x200) - Firm": {
        "(D95) 200 x 160 x 15cm (full piece) (with inner cover)": 1,
        "(D80) 200 x 160 x 5cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 160 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 160 x 20cm": 1,
        "quilted cover 200 x 160 x 5cm": 1,
    },

    "Heveya Mattress III - Single (90x200) - Soft": {
        "(D70) 200 x 90 x 15cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 90 x 5cm (full piece) (with inner cover)": 2,
        "quilted cover 200 x 90 x 20cm": 1,
        "quilted cover 200 x 90 x 5cm": 1,
    },
    "Heveya Mattress III - Single (90x200) - Medium": {
        "(D80) 200 x 90 x 15cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 90 x 5cm (full piece) (with inner cover)": 2,
        "quilted cover 200 x 90 x 20cm": 1,
        "quilted cover 200 x 90 x 5cm": 1,
    },
    "Heveya Mattress III - Single (90x200) - Firm": {
        "(D95) 200 x 90 x 15cm (full piece) (with inner cover)": 1,
        "(D80) 200 x 90 x 5cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 90 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 90 x 20cm": 1,
        "quilted cover 200 x 90 x 5cm": 1,
    },

    "Heveya Mattress II - Super King (200x200) - Soft": {
        "(D70) 200 x 100 x 15cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 100 x 5cm (full piece) (with inner cover)": 2,
        "quilted cover 200 x 200 x 15cm": 1,
    },
    "Heveya Mattress II - Super King (200x200) - Medium": {
        "(D80) 200 x 100 x 15cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 100 x 5cm (full piece) (with inner cover)": 2,
        "quilted cover 200 x 200 x 15cm": 1,
    },
    "Heveya Mattress II - Super King (200x200) - Firm": {
        "(D95) 200 x 100 x 15cm (full piece) (with inner cover)": 2,
        "(D80) 200 x 100 x 5cm (full piece) (with inner cover)": 2,
        "quilted cover 200 x 200 x 15cm": 1,
    },

    "Heveya Mattress II - King (180x200) - Soft": {
        "(D70) 200 x 90 x 15cm (full piece) (with inner cover)": 2,
        "(D65) 200 x 90 x 5cm (full piece) (with inner cover)": 2,
        "quilted cover 200 x 180 x 15cm": 1,
    },
    "Heveya Mattress II - King (180x200) - Firm": {
        "(D95) 200 x 90 x 15cm (full piece) (with inner cover)": 2,
        "(D80) 200 x 90 x 5cm (full piece) (with inner cover)": 2,
        "quilted cover 200 x 180 x 15cm": 1,
    },

    "Heveya Mattress II - Queen (160x200) - Soft": {
        "(D70) 200 x 160 x 15cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 160 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 160 x 15cm": 1,
    },
    "Heveya Mattress II - Queen (160x200) - Medium": {
        "(D80) 200 x 160 x 15cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 160 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 160 x 15cm": 1,
    },
    "Heveya Mattress II - Queen (160x200) - Firm": {
        "(D95) 200 x 160 x 15cm (full piece) (with inner cover)": 1,
        "(D80) 200 x 160 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 160 x 15cm": 1,
    },

    "Heveya Mattress II - Single (90x200) - Soft": {
        "(D70) 200 x 90 x 15cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 90 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 90 x 15cm": 1,
    },
    "Heveya Mattress II - Single (90x200) - Medium": {
        "(D80) 200 x 90 x 15cm (full piece) (with inner cover)": 1,
        "(D65) 200 x 90 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 90 x 15cm": 1,
    },
    "Heveya Mattress II - Single (90x200) - Firm": {
        "(D95) 200 x 90 x 15cm (full piece) (with inner cover)": 1,
        "(D80) 200 x 90 x 5cm (full piece) (with inner cover)": 1,
        "quilted cover 200 x 90 x 15cm": 1,
    },
    "Heveya Mattress II - King (180x200) - Medium": {
        "Heveya Natural Organic Latex 15cm - King - Medium": 1,
        "Heveya Natural Organic Latex 5cm - King - Soft": 1,
        "Heveya Bamboo Fiber Quilted Outer Cover 2 - King": 1,
    }
}

# Function to calculate product availability
def calculate_availability(products, components):
    availability = {}
    for product, materials in products.items():
        # Calculate the availability based on the components
        min_stock = float('inf')
        for component, qty_needed in materials.items():
            if component in components:
                available_qty = components[component] // qty_needed
                min_stock = min(min_stock, available_qty)
            else:
                min_stock = 0
        availability[product] = min_stock
    return availability

# Function to search for products based on keywords
def search_product_stock(keyword, availability):
    keywords = keyword.lower().split()  # Split the search term into individual words
    matching_products = {}

    for product, stock in availability.items():
        product_lower = product.lower()
        # Check if all keywords are in the product name
        if all(kw in product_lower for kw in keywords):
            matching_products[product] = stock

    if matching_products:
        result = "\n".join([f"{product}: {stock} available" for product, stock in matching_products.items()])
    else:
        result = "No matching products found."

    return result

# Function to handle search button click or Enter key press
def handle_search(event=None):  # Accept `event` for key binding
    keyword = search_entry.get()
    if not keyword:
        messagebox.showerror("Error", "Please enter a keyword.")
        return

    result = search_product_stock(keyword, availability)
    result_label.config(text=result)

# Calculate initial availability
availability = calculate_availability(products, components)

# GUI Setup
root = tk.Tk()
root.title("Product Stock Checker")

# Search bar and button
search_label = tk.Label(root, text="Enter Product Keyword:")
search_label.pack(pady=5)

search_entry = tk.Entry(root, width=50)
search_entry.pack(pady=5)

# Bind the Enter key to the handle_search function
search_entry.bind("<Return>", handle_search)  # Bind Enter key

search_button = tk.Button(root, text="Check Stock", command=handle_search)
search_button.pack(pady=10)

# Result display
result_label = tk.Label(root, text="", font=("Arial", 12), fg="blue", justify="left")
result_label.pack(pady=20)

# Run the GUI loop
root.mainloop()
