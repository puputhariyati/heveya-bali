async function fetchStockData() {
    try {
        const response = await fetch("/api/get_stock");
        if (!response.ok) throw new Error("Failed to fetch stock data.");

        let stockData = await response.json();
        console.log("Fetched Stock Data:", stockData); // Debugging log

        if (!Array.isArray(stockData)) {
            console.error("Stock data is not an array:", stockData);
            return;
        }

        // Fetch BOM status for each product
        await Promise.all(stockData.map(async (item) => {
            try {
                const productName = encodeURIComponent(item.product_name.trim());
                console.log(`Fetching BOM for: "${item.product_name}"`);

                const bomResponse = await fetch(`/api/get_bom?product=${productName}`);
                if (!bomResponse.ok) {
                    console.error(`Error fetching BOM for ${item.product_name}:`, bomResponse.statusText);
                    item.hasBOM = false;
                    return;
                }

                const bomData = await bomResponse.json();
                console.log(`BOM Data for ${item.product_name}:`, bomData);

                // Assign BOM status correctly
                item.hasBOM = !!(Array.isArray(bomData) && bomData.length);
            } catch (error) {
                console.error(`Failed to fetch BOM for ${item.product_name}:`, error);
                item.hasBOM = false;
            }
        }));

        renderStockTable(stockData);
    } catch (error) {
        console.error("Error fetching stock data:", error);
    }
}

async function fetchBomData(productName) {
    try {
        const response = await fetch(`/api/get_bom?product=${encodeURIComponent(productName)}`);
        if (!response.ok) {
            throw new Error("Failed to fetch BOM data.");
        }

        const bomData = await response.json();
        openBomModal(productName, bomData); // Ensure this function is defined
    } catch (error) {
        console.error("Error fetching BOM data:", error);
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
    const row = button.closest(".productRow"); // Find the closest row
    if (!row) {
        console.error("Row not found");
        return;
    }

    const bomContainer = row.querySelector(".bomContainer"); // Find BOM container
    if (!bomContainer) {
        console.error("BOM container not found");
        return;
    }

    // Create a new BOM entry
    const entry = document.createElement("div");
    entry.classList.add("bom-entry");
    entry.innerHTML = `
        <div class="input-container">
            <input type="text" id="productName" placeholder="Select Product" oninput="suggestProducts(this)">
            <div class="suggestions"></div> <!-- Use class instead of ID -->
        </div>
        <input type="number" placeholder="Qty">
        <button type="button" onclick="removeBOMEntry(this)">Remove</button>
    `;

    // Append to BOM container
    bomContainer.appendChild(entry);
}


function removeBOMEntry(button) {
    button.parentElement.remove();
}

function saveBOM(button) {
    const row = button.closest(".productRow");
    if (!row) return;

    const product = row.querySelector(".product-name").value;
    const bomEntries = row.querySelectorAll(".bom-entry");
    const bomData = [];

    bomEntries.forEach(entry => {
        const component = entry.querySelector("input[type='text']").value;
        const quantity = entry.querySelector("input[type='number']").value;
        if (component && quantity) {
            bomData.push({ product, component, quantity });
        }
    });

    // Send BOM data to Python backend
    fetch('/save_bom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bomData)
    })
    .then(response => response.json())
    .then(data => alert(data.message))
    .catch(error => console.error("Error:", error));
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
    stockTableBody.innerHTML = ""; // Clear previous content

    // Reverse the stockData array to show the newest first
    stockData.reverse().forEach((item, index) => {
        console.log(`Product: ${item.product_name}, hasBOM: ${item.hasBOM}`); // Debugging log

        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>
                ${item.hasBOM
                    ? `<a href="#" class="bom-link" data-product="${encodeURIComponent(item.product_name)}"
                        style="color: blue; text-decoration: underline;">${item.product_name}</a>`
                    : item.product_name}
            </td>
            <td class="on-hand">${item.on_hand || 0}</td>
            <td class="sold-qty">${item.sold_qty}</td>
            <td class="free-qty">${item.free_qty}</td>
            <td>${item.upcoming_qty}</td>
            <td>${item.unit_sell_price}</td>
            <td>${item.unit_buy_price}</td>
            <td>${item.tags || ""}</td>
        `;

        stockTableBody.appendChild(row); // ✅ Fix here
    });

    attachEventListeners(); // ✅ Ensure function exists before calling
}

// Function to calculate On-Hand Stock for a Composite Product
document.addEventListener("DOMContentLoaded", function () {
    function updateOnHand(row) {
        let soldQty = parseInt(row.querySelector(".sold-qty").textContent) || 0;
        let freeQty = parseInt(row.querySelector(".free-qty").textContent) || 0;
        row.querySelector(".on-hand").textContent = soldQty + freeQty;
    }

    function attachEventListeners() {
        document.querySelectorAll("#stockTableBody tr").forEach((row) => {
            updateOnHand(row); // Ensure it calculates on load

            let soldQtyCell = row.querySelector(".sold-qty");
            let freeQtyCell = row.querySelector(".free-qty");

            if (soldQtyCell && freeQtyCell) {
                soldQtyCell.addEventListener("input", () => updateOnHand(row));
                freeQtyCell.addEventListener("input", () => updateOnHand(row));
            }
        });
    }

    attachEventListeners();
});

// ✅ Define attachEventListeners function
function attachEventListeners() {
    document.querySelectorAll(".bom-link").forEach(link => {
        link.addEventListener("click", function (event) {
            event.preventDefault();
            const productName = decodeURIComponent(event.target.dataset.product);
            fetchBomData(productName);
        });
    });
}

// ✅ Fetch data and populate table
fetchStockData();

// ✅ Attach global click listener
document.addEventListener("click", function (event) {
    if (event.target.classList.contains("bom-link")) {
        event.preventDefault();
        const productName = decodeURIComponent(event.target.dataset.product);
        fetchBomData(productName);
    }
});

// ✅ Fetch stock data on window load
window.onload = fetchStockData;


//to show BOM pop up
function openBomModal(productName, bomData) {
    const modal = document.getElementById("bomModal");
    const modalContent = document.getElementById("bomModalContent");

    modalContent.innerHTML = `<h3>BOM for ${productName}</h3><ul>` +
        bomData.map(item => `<li>${item.component} - ${item.quantity}</li>`).join("") +
        `</ul>`;

    modal.style.display = "block";
}

// Fetch product suggestions dynamically
function suggestProducts(inputField) {
    let suggestionsDiv = inputField.closest(".input-container").querySelector(".suggestions");

    let query = inputField.value.trim();
    if (query.length < 2) {
        suggestionsDiv.innerHTML = "";
        suggestionsDiv.style.display = "none";
        return;
    }

    fetch(`/get_product_suggestions?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(products => {
            suggestionsDiv.innerHTML = ""; // Clear previous suggestions
            suggestionsDiv.style.display = "block"; // Show suggestions

            if (products.length > 0) {
                products.forEach(product => {
                    let option = document.createElement("div");
                    option.textContent = product;
                    option.classList.add("suggestion-item");
                    option.onclick = function () {
                        inputField.value = product;
                        suggestionsDiv.innerHTML = "";
                        suggestionsDiv.style.display = "none";
                    };
                    suggestionsDiv.appendChild(option);
                });
            } else {
                suggestionsDiv.style.display = "none";
            }
        })
        .catch(error => console.error("Error fetching suggestions:", error));
}


// Prevent form submission if the product is not valid
document.getElementById("bomForm").addEventListener("submit", function (event) {
    let productInput = document.getElementById("productName");

    if (productInput.getAttribute("data-valid") !== "true") {
        alert("Product not found in stock! Please select a valid product.");
        event.preventDefault(); // Stop form submission
    }
});

// Hide suggestions when clicking outside
document.addEventListener("click", function (event) {
    let suggestionsDiv = document.getElementById("suggestions");
    if (!document.getElementById("productName").contains(event.target)) {
        suggestionsDiv.style.display = "none";
    }
});


// Function to calculate Free Stock for a Composite Product
function calculateFreeStock(bom, inventory) {
    let minStock = Infinity;

    for (const component in bom) {
        if (inventory[component]) {
            const maxPossible = Math.floor(inventory[component].free / bom[component]);
            minStock = Math.min(minStock, maxPossible);
        } else {
            return 0; // If any component is missing, the product cannot be made
        }
    }

    return minStock;
}

// Calculate Free Stock for Heveya Mattress
const freeMattresses = calculateFreeStock(bom, stockInventory);

