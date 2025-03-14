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

function toggleBOMSection() {
    const productType = document.getElementById("productType").value;
    const bomSection = document.getElementById("bomSection");

    // Show BOM section if "Bundle" is selected
    if (productType === "bundle") {
        bomSection.style.display = "block";
    } else {
        bomSection.style.display = "none";
    }
}

function addBOMEntry() {
    const bomContainer = document.getElementById("bomContainer");
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

document.addEventListener("DOMContentLoaded", function () {
    function updateOnHand() {
        let soldQty = parseInt(document.querySelector(".sold-qty").value) || 0;
        let freeQty = parseInt(document.querySelector(".free-qty").value) || 0;
        document.querySelector(".on-hand").value = soldQty + freeQty;
    }

    document.querySelector(".sold-qty").addEventListener("input", updateOnHand);
    document.querySelector(".free-qty").addEventListener("input", updateOnHand);
});