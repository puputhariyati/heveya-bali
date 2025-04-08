let stockDataGlobal = []; // Store fetched stock data globally

async function fetchStockData() {
    try {
        const response = await fetch(`/api/get_stock?t=${Date.now()}`, { cache: "no-store" }); // Ensure fresh data
        if (!response.ok) throw new Error("Failed to fetch stock data.");

        let stockData = await response.json(); // Store fresh data temporarily
        console.log("Fetched Stock Data:", stockData); // Debugging log

        // 🔹 Fetch BOM status for each product
        await Promise.all(stockData.map(async (item) => {
            try {
                const productName = encodeURIComponent(item.product_name.trim());
                console.log(`Fetching BOM for: "${item.product_name}"`);

                const bomResponse = await fetch(`/api/get_bom?product_name=${productName}`);
                if (!bomResponse.ok) throw new Error(`Error fetching BOM for ${item.product_name}: ${bomResponse.statusText}`);

                const bomData = await bomResponse.json();
                console.log(`BOM Data for ${item.product_name}:`, bomData);

                item.hasBOM = !!(Array.isArray(bomData) && bomData.length);
            } catch (error) {
                console.error(`Failed to fetch BOM for ${item.product_name}:`, error);
                item.hasBOM = false;
            }
        }));

        // ✅ Store updated stock data globally and refresh table
        stockDataGlobal = stockData;
        filterTable(stockDataGlobal);
    } catch (error) {
        console.error("Error fetching stock data:", error);
    }
}

document.addEventListener("DOMContentLoaded", fetchStockData); // Fetch data on page load


async function fetchBomData(productName) {
    try {
        const response = await fetch(`/api/get_bom?product_name=${encodeURIComponent(productName)}`);
        if (!response.ok) {
            throw new Error("Failed to fetch BOM data.");
        }

        const bomData = await response.json();
        console.log("🔍 BOM Data Received:", bomData); // 👈 Check what's really returned
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
            <input type="text" id="productName" placeholder="Select Product" oninput="suggestBomProducts(this)">
            <div class="suggestions"></div> <!-- Use class instead of ID -->
        </div>
        <input type="number" placeholder="Qty">
        <button type="button" onclick="removeBOMEntry(this)">X</button>
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

    const product_name = row.querySelector(".product-name").value;
    const bomEntries = row.querySelectorAll(".bom-entry");
    const bomData = [];

    bomEntries.forEach(entry => {
        const component_name = entry.querySelector("input[type='text']").value;
        const quantity_required = entry.querySelector("input[type='number']").value;
        if (component_name && quantity_required) {
            bomData.push({ product_name, component_name, quantity_required });
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


// Function to update the stock table based on the search filter
function filterTable() {
    let filter = document.getElementById("productName").value.trim().toLowerCase();
    const stockTableBody = document.getElementById("stockTableBody");
    stockTableBody.innerHTML = ""; // Clear previous content

    if (!Array.isArray(stockDataGlobal) || stockDataGlobal.length === 0) {
        console.warn("Stock data is empty or not an array.");
        return;
    }

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

                    ${createNoteCell(item.free_qty, item.cell_notes)}
                    ${createNoteCell(item.booked_qty, item.cell_notes)}
                    ${createNoteCell(item.delivered_qty, item.cell_notes)}
                    ${createNoteCell(item.upcoming_qty, item.cell_notes)}

                    <td>${item.unit_sell_price}</td>
                    <td>${item.unit_buy_price}</td>
                    <td>${item.tags || ""}</td>
                    <td>

                    <select onchange="handleAction(this, '${item.product_name}')">
                        <option value="">⬇️ Actions</option>
                        <option value="convert">Convert to Booked</option>
                        <option value="deliver">Delivered</option>
                        <option value="edit">Edit/Adjust</option>
                        <option value="return">Return</option>
                        <option value="delete">Delete</option>
                    </select>
                </td>
            `;
            stockTableBody.appendChild(row);
        }
    });
}


// Function to handle dropdown actions
function handleAction(selectElement, productName) {
    let action = selectElement.value;
    selectElement.value = ""; // Reset dropdown after selection

    // Find the row with the matching product name
    let row = [...document.querySelectorAll("#stockTableBody tr")]
        .find(tr => tr.cells[1].textContent.trim() === productName);

    if (!row) return; // Exit if row is not found

    switch (action) {
        case "convert":
            convertToBooked(productName);
            break;
        case "deliver":
            deliverProduct(productName);
            break;
        case "edit":
            editRow(row); // ✅ Directly pass the row instead of looking for `.edit-btn`
            break;
        case "return":
            returnProduct(productName);
            break;
        case "delete":
            deleteRow(row);
            break;
        default:
            console.log("No action selected");
    }
}

// Function to calculate On-Hand Stock for a Composite Product
document.addEventListener("DOMContentLoaded", function () {
    function updateOnHand(row) {
        let bookedQty = parseInt(row.querySelector(".booked-qty").textContent) || 0;
        let freeQty = parseInt(row.querySelector(".free-qty").textContent) || 0;
        row.querySelector(".on-hand").textContent = bookedQty + freeQty;
    }

    function attachEventListeners() {
        document.querySelectorAll("#stockTableBody tr").forEach((row) => {
            updateOnHand(row); // Ensure it calculates on load

            let bookedQtyCell = row.querySelector(".booked-qty");
            let freeQtyCell = row.querySelector(".free-qty");

            if (bookedQtyCell && freeQtyCell) {
                bookedQtyCell.addEventListener("input", () => updateOnHand(row));
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

//// ✅ Fetch stock data on window load
//window.onload = fetchStockData;


//to show BOM pop up
function openBomModal(productName, bomData) {
    console.log("🧪 BOM Modal Triggered For:", productName);
    console.log("🧪 BOM Items:", bomData);

    const modal = document.getElementById("bomModal");
    const modalContent = document.getElementById("bomModalContent");

    modalContent.innerHTML = `<h3>BOM for ${productName}</h3><ul>` +
        bomData.map(item => {
            console.log("↪️ item keys:", Object.keys(item));  // Check keys inside each item
            return `<li>${item.component_name} - ${item.quantity_required}</li>`;
        }).join("") +
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
const bomForm = document.getElementById("bomForm");
if (bomForm) {
    bomForm.addEventListener("submit", function (event) {
        let productInput = document.getElementById("productName");
        if (productInput.getAttribute("data-valid") !== "true") {
            alert("Product not found in stock! Please select a valid product.");
            event.preventDefault(); // Stop form submission
        }
    });
}


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



function convertToBooked(productName) {

    // Locate the row by product name
    let row = [...document.querySelectorAll("#stockTableBody tr")]
        .find(tr => tr.cells[1].textContent.trim() === productName);

    if (!row) {
        alert("Product not found in table!");
        return;
    }

    // Get table cell references
    let onHandCell = row.cells[2];  // Adjust index based on your table
    let bookedCell = row.cells[4];  // Adjust index based on your table
    let freeCell = row.cells[3];    // Adjust index based on your table

    // Convert text content to numbers
    let onHandQty = parseInt(onHandCell.textContent.trim()) || 0;
    let bookedQty = parseInt(bookedCell.textContent.trim()) || 0;
    let freeQty = parseInt(freeCell.textContent.trim()) || 0;

    // ✅ Move prompt AFTER freeQty is defined
    let qty = prompt(`Enter quantity to convert for ${productName} (max: ${freeQty}):`, freeQty);

    if (!qty || isNaN(qty) || qty <= 0) {
        alert("Invalid quantity! Please enter a positive number.");
        return;
    }

    qty = parseInt(qty);

    if (qty > freeQty) {
        alert("Not enough stock available to convert!");
        return;
    }

    // ✅ Temporarily update UI (Optimistic UI update)
    freeCell.textContent = freeQty - qty;
    bookedCell.textContent = bookedQty + qty;

    // Send update to backend
    fetch("/convert_to_booked", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_name: productName, qty: qty })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Backend Response:", data);  // ✅ Debugging
        if (!data.success) {
            alert("Error: " + data.error);
            return;
        }

        // ✅ Update current product
        if (data.updated_product) {
            freeCell.textContent = data.updated_product.free_qty;
            bookedCell.textContent = data.updated_product.booked_qty;
        }

        // ✅ Update affected parent or component rows
        if (Array.isArray(data.updated_others)) {
            data.updated_others.forEach(item => {
                const otherRow = [...document.querySelectorAll("#stockTableBody tr")]
                    .find(tr => tr.cells[1].textContent.trim() === item.product_name);
                if (otherRow) {
                    otherRow.cells[3].textContent = item.free_qty;
                    otherRow.cells[4].textContent = item.booked_qty;
                }
            });
        }
        alert(`✅ Updated Free: ${data.updated_product?.free_qty}, Booked: ${data.updated_product?.booked_qty}`);
    })
    .catch(error => {
        console.error("Fetch error:", error);
        alert("Failed to update stock. Please try again.");
    });
}


function editRow(row) {
    let cells = row.getElementsByTagName("td");
    let updatedData = {};
    let product_name = row.cells[1].textContent.trim();
    let isEditing = row.getAttribute("data-editing") === "true";

    if (isEditing) {
        // ✅ Save Changes
        for (let i = 2; i <= 9; i++) {
            if ([2, 4, 5].includes(i)) continue; // ❌ Skip "On Hand," "Booked," and "Delivered"

            let input = cells[i].querySelector("input");
            if (input) {
                let key = cells[i].getAttribute("data-field");
                let newValue = input.value.trim();
                updatedData[key] = newValue;
                cells[i].innerText = newValue;
            }
        }

        updatedData["product_name"] = product_name;
        updateStockData(row); // ✅ Handle database update & UI refresh

        row.setAttribute("data-editing", "false");
        row.style.backgroundColor = "";

        // ✅ Remove Save Button
        let saveBtn = row.querySelector(".save-btn");
        if (saveBtn) saveBtn.remove();

        return;
    }

    // ✅ Convert editable cells to input fields
    for (let i = 2; i <= 9; i++) {
        if ([2, 4, 5].includes(i)) continue; // ❌ Skip these columns

        let currentValue = cells[i].innerText;
        cells[i].innerHTML = `<input type="text" value="${currentValue}" style="width:100%">`;
    }

    // ✅ Add Save Button
    let actionsCell = cells[10]; // Last column for actions
    let saveButton = document.createElement("button");
    saveButton.innerText = "Save";
    saveButton.classList.add("save-btn");
    saveButton.style.marginLeft = "5px";
    saveButton.onclick = function () {
        editRow(row);
    };

    actionsCell.appendChild(saveButton);

    row.setAttribute("data-editing", "true");
    row.style.backgroundColor = "#ffffcc";
}

//Action: Delivered
function deliverProduct(productName) {
    let qty = prompt(`Enter quantity to deliver for ${productName}:`);

    if (!qty || isNaN(qty) || qty <= 0) {
        alert("Invalid quantity.");
        return;
    }

    qty = parseInt(qty);

    fetch("/deliver_product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_name: productName, qty })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            alert("❌ " + data.error);
            return;
        }

        alert("✅ Delivery recorded.");

        // ✅ Optimistically update table UI
        data.updated.forEach(item => {
            const row = [...document.querySelectorAll("#stockTableBody tr")]
                .find(tr => tr.cells[1].textContent.trim() === item.product_name);
            if (row) {
                row.cells[4].textContent = item.booked_qty;    // Booked column
                row.cells[5].textContent = item.delivered_qty; // Delivered column
            }
        });
    })
    .catch(err => {
        console.error("Delivery failed:", err);
        alert("Something went wrong while delivering.");
    });
}


function updateStockData(row) {
    let productName = row.cells[1].innerText.trim();
    let product = stockDataGlobal.find(item => item.product_name === productName);

    if (!product) {
        console.error("Product not found:", productName);
        return;
    }

    let bookedQty = parseInt(row.cells[4].innerText) || 0;
    let freeStock = parseInt(row.cells[3].innerText) || 0;
    let onHand = bookedQty + freeStock;

    let updatedData = {
        product_name: productName,
        on_hand: onHand,
        booked_qty: bookedQty,
        free_qty: freeStock,
        delivered_qty: parseInt(row.cells[5].innerText) || 0,
        upcoming_qty: parseInt(row.cells[6].innerText) || 0,
        unit_sell_price: parseFloat(row.cells[7].innerText) || 0,
        unit_buy_price: parseFloat(row.cells[8].innerText) || 0,
        tags: row.cells[9].innerText.trim()
    };

    Object.assign(product, updatedData);
//    localStorage.setItem("stockData", JSON.stringify(stockDataGlobal));

    // ✅ Send update request to backend
    updateDatabase(updatedData).then(response => {
        if (response.success) {
            console.log("✅ Database update confirmed.");

            if (response.updated_parents && response.updated_parents.length > 0) {
                fetchStockData(); // ✅ Refresh everything if parent stocks were affected
            } else {
                // ✅ Update only the changed product manually for speed
                let product = stockDataGlobal.find(p => p.product_name === updatedData.product_name);
                if (product) {
                    product.free_qty = response.updatedData.free_qty;
                    product.booked_qty = response.updatedData.booked_qty;
                }
                updateStockTable(stockDataGlobal); // Refresh only affected row
            }
        }
    });

}

function updateParentStock(parentData) {
    let parentRow = [...document.querySelectorAll("#stockTable tr")].find(row =>
        row.cells[1].innerText.trim() === parentData.product_name
    );

    if (parentRow) {
        parentRow.cells[4].innerText = parentData.booked_qty; // Update sold stock
        parentRow.cells[3].innerText = parentData.free_qty; // Update free stock
        parentRow.cells[2].innerText = parentData.on_hand; // Update on-hand total
    } else {
        console.warn(`Could not find parent row for ${parentData.product_name}`);
    }
}

function updateDatabase(updatedData) {
    if (!updatedData.product_name || updatedData.product_name.trim() === "") {
        console.error("Error: Missing product_name in update request.");
        return;
    }

    return fetch("/update_product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData),
    })
    .then(response => response.json())
    .then(data => {
        console.log("Database response:", data);

        if (!data.success) {
            console.error("Update failed:", data.error);
            return { success: false, error: data.error };
        }

        // ✅ Update free stock for edited product
        const productElement = document.querySelector(`[data-product-name="${updatedData.product_name}"]`);
        if (productElement) {
            const freeStockElement = productElement.querySelector(".free-stock");
            const bookedStockElement = productElement.querySelector(".booked-stock");

            if (freeStockElement && bookedStockElement) {
                freeStockElement.textContent = data.free_qty;   // ✅ Correct Free Stock
                bookedStockElement.textContent = data.booked_qty; // ✅ Correct Booked Stock
            } else {
                console.warn(`Could not find stock elements for ${updatedData.product_name}`);
            }
        } else {
            console.warn(`Could not find element for ${updatedData.product_name}`);
        }

        // ✅ Update parent products' free stock
        if (data.updated_parents) {
            data.updated_parents.forEach(parent => {
                updateParentStock(parent);
            });
        }

        // ✅ Refresh entire stock list after database update
        fetchStockData();

        return { success: true, updated_parents: data.updated_parents };
    })
    .catch(error => {
        console.error("Error updating database:", error);
        return { success: false, error };
    });
}

//// Call this function on page load (to persist data after page refresh)
//window.onload = fetchStockData;

// Function to return product
function returnProduct(productName) {
    let qty = prompt(`Enter quantity to return for ${productName}:`);
    if (!qty || isNaN(qty) || qty <= 0) return alert("Invalid quantity!");

    fetch("/return_product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_name: productName, qty: parseInt(qty) })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) return alert("❌ " + data.error);

        data.updated_items.forEach(item => {
            const row = [...document.querySelectorAll("#stockTableBody tr")]
                .find(tr => tr.cells[1].textContent.trim() === item.product_name);
            if (row) {
                row.cells[3].textContent = item.free_qty;
                row.cells[5].textContent = item.delivered_qty;
            }
        });

        alert(`✅ Returned ${qty} pcs of ${productName}`);
    })
    .catch(err => {
        console.error("Return failed:", err);
        alert("Error returning product");
    });
}

// Function to delete row
function deleteRow(row) {
    let productName = row.cells[1].innerText.trim(); // Get product name

    if (!confirm(`Are you sure you want to delete "${productName}"? This action cannot be undone.`)) {
        return;
    }

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
            row.remove(); // ✅ Remove row from table if deletion is successful
        } else {
            console.error("Backend deletion failed:", data.error);
            alert("Error deleting product: " + (data.error || "Unknown error"));
        }
    })
    .catch(error => {
        console.error("Error deleting:", error);
        alert("An error occurred while deleting.");
    });
}

//Make Comments / noted on the cell

function createNoteCell(value, note = "") {
    return `
        <td class="note-cell">
            ${value}
            <span class="note-icon" data-note="${note}">📝</span>
        </td>
    `;
}

let noteBox;

document.addEventListener("DOMContentLoaded", () => {
    noteBox = document.createElement("div");
    noteBox.className = "note-popup";
    document.body.appendChild(noteBox);

    document.getElementById("stockTableBody").addEventListener("click", (e) => {
        const icon = e.target.closest(".note-icon");
        if (icon) {
            const cell = icon.closest(".note-cell");
            const currentNote = icon.getAttribute("data-note") || "";
            noteBox.innerHTML = `
                <textarea style="width: 100%; height: 60px;">${currentNote}</textarea>
                <button onclick="saveNote()">Save</button>
            `;
            noteBox.style.top = `${e.pageY}px`;
            noteBox.style.left = `${e.pageX}px`;
            noteBox.style.display = "block";
            noteBox.targetIcon = icon;
            noteBox.targetCell = cell;
        }
    });

    document.addEventListener("click", (e) => {
        if (!noteBox.contains(e.target) && !e.target.classList.contains("note-icon")) {
            noteBox.style.display = "none";
        }
    });
});

function saveNote() {
    const textarea = noteBox.querySelector("textarea");
    const newNote = textarea.value.trim();
    const icon = noteBox.targetIcon;
    const cell = noteBox.targetCell;

    // Get product name (from the same row)
    const row = cell.closest("tr");
    const productName = row.cells[1].innerText.trim();

    // Update UI
    icon.setAttribute("data-note", newNote);
    noteBox.style.display = "none";

    // Send to backend to save
    fetch("/update_note", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            product_name: productName,
            note: newNote
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            console.log("✅ Note saved");
        } else {
            console.error("❌ Failed to save note:", data.error);
            alert("Failed to save note");
        }
    })
    .catch(err => {
        console.error("Fetch error:", err);
        alert("Error saving note");
    });
}



function filterRowsByNote(keyword) {
    const rows = document.querySelectorAll("#stockTableBody tr");
    keyword = keyword.toLowerCase();

    rows.forEach(row => {
        const noteIcons = row.querySelectorAll(".note-icon");
        let match = false;

        noteIcons.forEach(icon => {
            const note = icon.getAttribute("data-note") || "";
            if (note.toLowerCase().includes(keyword)) match = true;
        });

        row.style.display = match || keyword === "" ? "" : "none";
    });
}


//End of Make Comments / noted on the cell