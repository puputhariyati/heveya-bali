let stockDataGlobal = []; // Store fetched stock data globally

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

        // Load previously deleted items from localStorage
        let deletedProducts = JSON.parse(localStorage.getItem("deletedProducts")) || [];

        // Remove deleted items from fetched stock data
        stockData = stockData.filter(item => !deletedProducts.includes(item.product_name));

        // Store updated stock data globally
        stockDataGlobal = stockData;

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

        // ✅ Save filtered stock data to localStorage
        localStorage.setItem("stockData", JSON.stringify(stockData));

        filterTable(); // Apply filtering after fetching stock data
    } catch (error) {
        console.error("Error fetching stock data:", error);
    }
}


document.addEventListener("DOMContentLoaded", function () {
    const searchButton = document.getElementById("searchButton");
    const productNameInput = document.getElementById("productName");

    // Trigger search when the button is clicked
    searchButton.addEventListener("click", filterTable);

    // Trigger search when Enter is pressed in the input field
    productNameInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault(); // Prevent form submission
            filterTable();
        }
    });

    // Trigger search when the input value changes (for autocomplete selections)
    productNameInput.addEventListener("change", function () {
        filterTable();
    });
});

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


// Function to update the stock table based on the search filter
function filterTable() {
    let filter = document.getElementById("productName").value.trim().toLowerCase();
    const stockTableBody = document.getElementById("stockTableBody");
    stockTableBody.innerHTML = ""; // Clear previous content

    stockDataGlobal.reverse().forEach((item, index) => {
        if (!filter || item.product_name.toLowerCase().includes(filter)) {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>
                    ${item.hasBOM
                        ? `<a href="#" class="bom-link" data-product="${encodeURIComponent(item.product_name)}"
                            style="color: blue; text-decoration: underline;">${item.product_name}</a>`
                        : item.product_name}
                </td>
                <td>${item.on_hand}</td>
                <td>${item.sold_qty}</td>
                <td>${item.free_qty}</td>
                <td>${item.upcoming_qty}</td>
                <td>${item.unit_sell_price}</td>
                <td>${item.unit_buy_price}</td>
                <td>${item.tags || ""}</td>
                <td>
                    <button class="edit-btn" onclick="editRow(this)">Edit</button>
                    <button class="delete-btn" onclick="deleteRow(this)">Delete</button>
                </td>
            `;
            stockTableBody.appendChild(row);
        }
    });
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

// Fetch product suggestions dynamically for bom inputs
function suggestBomProducts(inputField) {
    let suggestionsDiv = inputField.closest(".input-container").querySelector(".suggestions");

    let query = inputField.value.trim();
    console.log("User typed for BOM:", query);  // ✅ Check if function runs

    if (query.length < 2) {
        suggestionsDiv.innerHTML = "";
        suggestionsDiv.style.display = "none";
        return;
    }

    fetch(`/get_product_suggestions?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(products => {
            console.log("BOM Suggestions received:", products);  // ✅ Debug API response

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
        .catch(error => console.error("Error fetching BOM suggestions:", error));
}



// Prevent form submission if the product is not valid
document.getElementById("bomForm").addEventListener("submit", function (event) {
    let productInput = document.getElementById("productName");

    if (productInput.getAttribute("data-valid") !== "true") {
        alert("Product not found in stock! Please select a valid product.");
        event.preventDefault(); // Stop form submission
    }
});

// Fetch product suggestions dynamically for searchbar
function suggestSearchProducts() {
    let query = document.getElementById("productName").value.trim();
    let suggestionsDiv = document.getElementById("suggestions");

    if (query.length < 2) {
        suggestionsDiv.innerHTML = "";
        suggestionsDiv.style.display = "none"; // Hide when empty
        return;
    }

    fetch(`/get_product_suggestions?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(products => {
            suggestionsDiv.innerHTML = "";
            suggestionsDiv.style.display = "block";

            if (products.length > 0) {
                products.forEach(product => {
                    let option = document.createElement("div");
                    option.textContent = product;
                    option.classList.add("suggestion-item");
                    option.onclick = function () {
                        document.getElementById("productName").value = product;
                        suggestionsDiv.innerHTML = "";
                        suggestionsDiv.style.display = "none"; // Hide dropdown
                    };
                    suggestionsDiv.appendChild(option);
                });
            } else {
                // If no products found, show "Add New Product" option
                let addOption = document.createElement("div");
                addOption.textContent = "+ Add New Product";
                addOption.style.color = "blue";
                addOption.style.cursor = "pointer";
                addOption.style.textDecoration = "none";

                addOption.classList.add("suggestion-item", "add-product");

                // Add click event listener
                addOption.addEventListener("click", function () {
                    window.location.href = "/inventory";
                });

                suggestionsDiv.appendChild(addOption);
            }
        })
        .catch(error => console.error("Error fetching search suggestions:", error));
}


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

function editRow(button) {
    let row = button.closest("tr"); // Get the row
    let cells = row.getElementsByTagName("td");
    let updatedData = {}; // Object to store new values for database
    let product_name = row.cells[1].textContent.trim(); // Get product name from 2nd column

    // Check if it's already in edit mode
    if (button.innerText === "Save") {
        for (let i = 1; i <= 8; i++) {
            let input = cells[i].querySelector("input");
            if (input) {
                let key = cells[i].getAttribute("data-field"); // Get database field name
                let newValue = input.value;

                updatedData[key] = newValue; // Store value for database update
                cells[i].innerText = newValue; // Save input value back to UI
            }
        }

        // ✅ Ensure product_name is included
        updatedData["product_name"] = product_name;

        // Call function to update calculations (On Hand Qty)
        updateStockData(row);

        // Send updated data to backend
        updateDatabase(updatedData);

        // Change button back to "Edit"
        button.innerText = "Edit";
        return;
    }

    // Convert cells to input fields for editing
    for (let i = 1; i <= 8; i++) {
        let currentValue = cells[i].innerText;
        cells[i].innerHTML = `<input type="text" value="${currentValue}" style="width:100%">`;
    }

    // Change button to "Save"
    button.innerText = "Save";
}



function updateStockData(row) {
    let productName = row.cells[1].innerText.trim(); // Ensure no extra spaces

    // Find the matching product in stockDataGlobal
    let product = stockDataGlobal.find(item => item.product_name === productName);
    if (!product) {
        console.error("Product not found:", productName);
        return;
    }

    // Read and parse input values
    let soldQty = parseInt(row.cells[3].innerText) || 0;
    let freeStock = parseInt(row.cells[4].innerText) || 0;

    // Calculate On Hand
    let onHand = soldQty + freeStock;
    row.cells[2].innerText = onHand; // Update table cell

    // Prepare updated product data
    let updatedData = {
        product_name: productName,  // Ensure product name is included
        on_hand: onHand,
        sold_qty: soldQty,
        free_qty: freeStock,
        upcoming_qty: parseInt(row.cells[5].innerText) || 0,
        unit_sell_price: parseFloat(row.cells[6].innerText) || 0,
        unit_buy_price: parseFloat(row.cells[7].innerText) || 0,
        tags: row.cells[8].innerText.trim()
    };

    // Update local array
    Object.assign(product, updatedData);

    // Save updated data to localStorage
    localStorage.setItem("stockData", JSON.stringify(stockDataGlobal));

    // Send updated data to the database
    updateDatabase(updatedData);
}


function updateDatabase(updatedData) {
    console.log("Sending data to backend:", updatedData); // Debugging step

    fetch("/update_product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData),
    })
    .then(response => response.json())
    .then(data => {
        console.log("Database response:", data);
        if (!data.success) {
            console.error("Update failed:", data.error);
        }
    })
    .catch(error => console.error("Error updating database:", error));
}




// Function to load data from localStorage
function loadStockData() {
    let storedData = localStorage.getItem("stockData");
    if (storedData) {
        stockDataGlobal = JSON.parse(storedData);
        renderTable(); // Function to re-populate the table
    }
}

// Call this function on page load
window.onload = loadStockData;


// Function to delete row
function deleteRow(button) {
    let row = button.parentNode.parentNode;
    let productName = row.cells[1].innerText; // Get product name

    // Send DELETE request to the backend
    fetch("/delete_product", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ product_name: productName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            row.remove(); // Remove row from table only if deletion is successful
        } else {
            alert("Error deleting product.");
        }
    })
    .catch(error => console.error("Error:", error));
}


// Function to populate the table
function populateTable() {
    let tableBody = document.getElementById("table-body");
    tableBody.innerHTML = ""; // Clear existing table

    inventory.forEach((item, index) => {
        let row = tableBody.insertRow();
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${item.product_name}</td>
            <td>${item.on_hand || 0}</td>
            <td>${item.sold_qty}</td>
            <td>${item.free_qty}</td>
            <td>${item.upcoming_qty}</td>
            <td>${item.unit_sell_price}</td>
            <td>${item.unit_buy_price}</td>
            <td>${item.tags || ""}</td>
            <td>
                <button class="edit-btn" onclick="editRow(this)">Edit</button>
                <button class="delete-btn" onclick="deleteRow(this)">Delete</button>
            </td>
        `;
    });
}

// Load inventory when the page loads
window.onload = loadInventory;

