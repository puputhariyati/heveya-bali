document.addEventListener("DOMContentLoaded", function () {
    let productInput = document.getElementById("productName");
    if (productInput) {  // Check if it exists
        productInput.addEventListener("keypress", function (event) {
            if (event.key === "Enter") {
                checkStock();
            }
        });
    }
});

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
                addOption.innerHTML = `<a href="/add_product" style="color: white; text-decoration: none;">➕ Add New Product</a>`;
                addOption.classList.add("suggestion-item", "add-product");
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


function checkStock() {
    let productName = document.getElementById("productName").value.trim();
    let suggestionsDiv = document.getElementById("suggestions");
    suggestionsDiv.innerHTML = "";
    suggestionsDiv.style.display = "none"; // Hide dropdown
//    console.log("Searching for:", productName); // Debugging line

    // Fetch general stock data
    fetch(`/check_stock?name=${encodeURIComponent(productName)}`)
        .then(response => response.json())
        .then(data => {
            let tableBody = document.querySelector("#resultTable tbody");
            tableBody.innerHTML = "";

            if (data.message) {
                tableBody.innerHTML = `<tr><td colspan="4">${data.message}</td></tr>`;
            } else {
                data.forEach(product => {
                    let row = `
                        <tr>
                            <td>${product.name}</td>
                            <td>${product.stock}</td>
                            <td>${product.price.toLocaleString()}</td>
                            <td>${product.tags.join(", ")}</td>
                        </tr>
                    `;
                    tableBody.innerHTML += row;
                });
            }
            console.log("Response:", data); // Debugging line
        })
        .catch(error => console.error("Error:", error));

    // Fetch BOM-based stock availability
    fetch(`/check_stock/${productName}`)
        .then(response => response.json())
        .then(data => {
            if (data.max_producible !== undefined) {
                alert(`You can produce ${data.max_producible} units of '${data.product_name}'.`);
            }
        })
        .catch(error => console.error("Error fetching BOM stock:", error));
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("addProduct").addEventListener("click", addProduct);
    document.getElementById("createProduct").addEventListener("click", addProductWithBOM);
});

function addProduct() {
    let name = document.getElementById("productName").value;
    let stock = document.getElementById("productStock").value;
    let price = document.getElementById("productPrice").value;
    let tags = document.getElementById("productTags").value;

    fetch("/add_product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, stock, price, tags })
    })
    .then(response => response.json())
    .then(data => alert(data.message))
    .catch(error => console.error("Error:", error));
}

function addProductWithBOM() {
    alert("Create Product button clicked!"); // Debugging
    let productName = document.getElementById("productName").value;
    let materials = [];

    // Collect material data dynamically (checks for elements)
    let materialInputs = document.querySelectorAll("[data-material]");
    materialInputs.forEach(input => {
        let materialName = input.dataset.material;
        let quantity = parseInt(input.value);

        if (!isNaN(quantity) && quantity > 0) {
            materials.push({ name: materialName, quantity: quantity });
        }
    });

    fetch("/add_product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_name: productName, materials: materials })
    })
    .then(response => response.json())
    .then(data => alert(data.message))
    .catch(error => console.error("Error:", error));
}


document.querySelector("form").addEventListener("submit", function(event) {
    let inputs = document.querySelectorAll("input");
    let allFilled = true;

    inputs.forEach(input => {
        if (input.value.trim() === "") {
            allFilled = false;
            input.style.border = "2px solid red";  // Highlight empty fields
        } else {
            input.style.border = "";  // Reset border if filled
        }
    });

    if (!allFilled) {
        event.preventDefault();  // Prevent form submission
        alert("All fields must be filled!");
    }
});

