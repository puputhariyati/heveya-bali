document.addEventListener("DOMContentLoaded", function () {
const path = window.location.pathname;
const buttons = document.querySelectorAll(".sidebar button");

buttons.forEach(btn => {
  if (btn.getAttribute("onclick")?.includes(`'${path}'`)) {
    btn.classList.add("active");
  }
});
});

let stockDataGlobal = []; // Store fetched stock data globally


async function fetchBomData(productName) {
    try {
        const response = await fetch(`/api/get_bom?product_name=${encodeURIComponent(productName)}`);
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


// ✅ Attach event listener ONCE, outside the function
document.addEventListener("click", function (event) {
    if (event.target.classList.contains("bom-link")) {
        event.preventDefault();
        const productName = decodeURIComponent(event.target.dataset.product);
        fetchBomData(productName);
    }
});


//to show BOM pop up
function openBomModal(productName, bomData) {
    const modal = document.getElementById("bomModal");
    const modalContent = document.getElementById("bomModalContent");

    modalContent.innerHTML = `<h3>BOM for ${productName}</h3><ul>` +
        bomData.map(item => `<li>${item.component_name} - ${item.quantity_required}</li>`).join("") +
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
                <td>${item.free_qty}</td>
                <td>${item.booked_qty}</td>
                <td>${item.upcoming_qty}</td>
                <td>${item.unit_sell_price}</td>
                <td>${item.unit_buy_price}</td>
                <td>${item.tags || ""}</td>
            `;
            stockTableBody.appendChild(row);
        }
    });
}
