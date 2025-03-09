document.getElementById("productName").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        checkStock();  // Call the function when Enter is pressed
    }
});

function checkStock() {
    let productName = document.getElementById("productName").value.trim();
//    console.log("Searching for:", productName); // Debugging line

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
}

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

// Attach click event listener to the button
document.getElementById("addProduct").addEventListener("click", addProduct);

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

