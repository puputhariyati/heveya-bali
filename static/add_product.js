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

function toggleBOMSection(selectElement) {
    const row = selectElement.closest(".productRow"); // Find the parent row
    if (!row) return; // Prevent errors if row is not found

    const bomSection = row.querySelector(".bomSection"); // Find BOM section in the same row
    if (!bomSection) return; // Prevent errors if BOM section is missing

    // Show or hide BOM section based on selection
    bomSection.style.display = selectElement.value === "bundle" ? "block" : "none";
}

function addBOMEntry(button) {
    const row = button.closest(".productRow"); // Find the closest product row
    if (!row) return;

    const bomContainer = row.querySelector(".bomContainer"); // Find BOM container in the same row
    if (!bomContainer) {
        console.error("BOM container not found");
        return;
    }

    const entry = document.createElement("div");
    entry.classList.add("bom-entry");
    entry.innerHTML = `
        <input type="text" placeholder="Product Name">
        <input type="number" placeholder="Qty">
        <button type="button" onclick="removeBOMEntry(this)">Remove</button>
    `;

    bomContainer.appendChild(entry);
}

function removeBOMEntry(button) {
    button.parentElement.remove();
}

function saveBOM(button) {
    const row = button.closest(".productRow");
    if (!row) return;

    const bomEntries = row.querySelectorAll(".bom-entry");
    const bomData = [];

    bomEntries.forEach(entry => {
        const productName = entry.querySelector("input[type='text']").value;
        const quantity = entry.querySelector("input[type='number']").value;
        if (productName && quantity) {
            bomData.push({ productName, quantity });
        }
    });

    console.log("BOM Saved:", bomData);
    alert("BOM saved successfully!");
}

function addNewRow() {
    const productList = document.getElementById("productList");
    const newRow = document.createElement("div");
    newRow.classList.add("productRow");

    newRow.innerHTML = `
        <input type="text" name="product_name" placeholder="Product Name" class="product-name">
        <input type="number" step="0.01" name="unit_buy_price" placeholder="Unit Buy Price" class="unit-price">
        <input type="number" name="quantity" placeholder="Qty" class="quantity">
        <input type="text" name="tags" placeholder="Tags" class="tags">
        <label for="productType">Product Type:</label>
        <select name="product_type" class="product-type" onchange="toggleBOMSection(this)">
            <option value="single">Single Item</option>
            <option value="bundle">Bundle</option>
        </select>
        <button type="button" onclick="removeBOMEntry(this)">Remove</button>
        <div class="bomSection" style="display: none;">
            <h3>Unit Bill Of Materials</h3>
            <div class="bomContainer">
                <div class="bom-entry">
                    <input type="text" placeholder="Product Name">
                    <input type="number" placeholder="Qty">
                    <button type="button" onclick="removeBOMEntry(this)">Remove</button>
                </div>
            </div>
            <button type="button" onclick="addBOMEntry()">+ Add More Component</button>
        </div>
    `;

    productList.appendChild(newRow);
}


//// Function to collect and send multiple products
//function saveProduct() {
//    const products = [];
//    document.querySelectorAll(".productRow").forEach(row => {
//        const productName = row.querySelector(".product-name")?.value || "";
//        const soldQty = row.querySelector(".sold-qty")?.value || "";
//        const freeQty = row.querySelector(".free-qty")?.value || "";
//        const upcomingQty = row.querySelector(".upcoming-qty")?.value || "";
//        const unitSellPrice = row.querySelector(".unit-sell-price")?.value || "";
//        const unitBuyPrice = row.querySelector(".unit-buy-price")?.value || "";
//        const tags = row.querySelector(".tags")?.value || "";
//
//        if (productName && soldQty && freeQty && upcomingQty && unitSellPrice && unitBuyPrice && tags) {
//            products.push({
//                product_name: productName,
//                sold_qty: soldQty,
//                free_qty: freeQty,
//                upcoming_qty: upcomingQty,
//                unit_sell_price: unitSellPrice,
//                unit_buy_price: unitBuyPrice,
//                tags: tags
//            });
//        }
//    });
//
//    if (products.length === 0) {
//        alert("Please fill in product details before saving.");
//        return;
//    }
//
//    fetch("/inventory", {
//        method: "POST",
//        headers: { "Content-Type": "application/json" },
//        body: JSON.stringify({ products: products })
//    })
//    .then(response => response.json())
//    .then(data => {
//        alert("Products saved successfully!");
//        fetchStockData(); // Refresh the stock table
//    })
//    .catch(error => console.error("Error:", error));
//}

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

    // Reverse the stockData array to show the newest first
    stockData.slice().reverse().forEach((item, index) => {
        let row = document.createElement("tr");

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${item.product_name}</td>
            <td>${item.on_hand}</td>
            <td>${item.sold_qty}</td>
            <td>${item.free_qty}</td>
            <td>${item.upcoming_qty}</td>
            <td>${item.unit_sell_price}</td>
            <td>${item.unit_buy_price}</td>
            <td>${item.tags}</td>
        `;

        stockTableBody.appendChild(row);
    });
}

window.onload = fetchStockData; // Load real stock on page load
