function checkStock() {
    let productName = document.getElementById("productName").value;

    fetch(`/check_stock?name=${productName}`)
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
