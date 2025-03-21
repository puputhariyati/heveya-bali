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

        // Store data globally for filtering
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

//        checkStock(stockData);
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


// Fetch product suggestions dynamically
function suggestProducts() {
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
        .catch(error => console.error("Error fetching suggestions:", error));
}

// Hide suggestions when clicking outside
document.addEventListener("click", function (event) {
    let suggestionsDiv = document.getElementById("suggestions");
    if (!document.getElementById("productName").contains(event.target)) {
        suggestionsDiv.style.display = "none";
    }
});


// ✅ Attach event listener ONCE, outside the function
document.addEventListener("click", function (event) {
    if (event.target.classList.contains("bom-link")) {
        event.preventDefault();
        const productName = decodeURIComponent(event.target.dataset.product);
        fetchBomData(productName);
    }
});

window.onload = fetchStockData; // Load real stock on page load

//to show BOM pop up
function openBomModal(productName, bomData) {
    const modal = document.getElementById("bomModal");
    const modalContent = document.getElementById("bomModalContent");

    modalContent.innerHTML = `<h3>BOM for ${productName}</h3><ul>` +
        bomData.map(item => `<li>${item.component} - ${item.quantity}</li>`).join("") +
        `</ul>`;

    modal.style.display = "block";
}

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

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("productName").addEventListener("input", filterTable);
    fetchStockData();
});

// Function to update the stock table based on the search filter
function filterTable() {
    let filter = document.getElementById("productName").value.trim().toLowerCase();
    const stockTableBody = document.getElementById("stockTableBody");
    stockTableBody.innerHTML = ""; // Clear previous content

    stockDataGlobal.reverse().forEach(item => {
        if (!filter || item.product_name.toLowerCase().includes(filter)) {
            const row = document.createElement("tr");
            row.innerHTML = `
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
            `;
            stockTableBody.appendChild(row);
        }
    });
}

