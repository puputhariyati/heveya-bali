async function fetchStockData() {
    try {
        const response = await fetch("/api/get_stock");
        if (!response.ok) {
            throw new Error("Failed to fetch stock data.");
        }
        const stockData = await response.json();

        if (!Array.isArray(stockData)) {
            console.error("Stock data is not an array:", stockData);
            return;
        }

        renderStockTable(stockData);
    } catch (error) {
        console.error("Error fetching stock data:", error);
    }
}

function addNewRow() {
    const productList = document.getElementById("productList");
    const newRow = document.createElement("div");
    newRow.classList.add("productRow");

    newRow.innerHTML = `
        <input type="text" placeholder="Product Name" class="product-name">
        <input type="number" placeholder="Unit Buy Price" class="unit-price">
        <input type="number" placeholder="Qty" class="quantity">
        <input type="text" placeholder="Tags" class="tags">
    `;

    productList.appendChild(newRow);
}

// Function to collect and send multiple products
function saveProduct() {
    const products = [];
    document.querySelectorAll(".productRow").forEach(row => {
        const productName = row.querySelector(".product-name")?.value || "";
        const unitPrice = row.querySelector(".unit-price")?.value || "";
        const quantity = row.querySelector(".quantity")?.value || "";
        const tags = row.querySelector(".tags")?.value || "";

        if (productName && unitPrice && quantity && tags) {
            products.push({ product_name: productName, unit_buy_price: unitPrice, quantity, tags });
        }
    });

    if (products.length === 0) {
        alert("Please fill in product details before saving.");
        return;
    }

    fetch("/inventory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ products: products })
    })
    .then(response => response.json())
    .then(data => {
        alert("Products saved successfully!");
        fetchStockData(); // Refresh the stock table
    })
    .catch(error => console.error("Error:", error));
}

// Function to send data to the server
function sendDataToServer(data) {
    fetch('/inventory', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert("Product added successfully!");
            fetchStockData();  // Fetch updated stock list from backend
        } else {
            alert("Error: " + result.error);
        }
    })
    .catch(error => console.error("Error:", error));
}


function renderStockTable(stockData) {
    const stockTableBody = document.getElementById("stockTableBody");

    if (!stockTableBody) {
        console.error("Error: 'stockTableBody' not found in the DOM.");
        return;
    }

    stockTableBody.innerHTML = ""; // Clear previous data

    stockData.forEach((item, index) => {
        let row = document.createElement("tr");

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${item.name}</td>
            <td>${item.price}</td>
            <td>${item.qty}</td>
            <td>${item.tags}</td>
        `;

        stockTableBody.appendChild(row);
    });
}

window.onload = fetchStockData; // Load real stock on page load