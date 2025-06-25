function filterOrders() {
    const status = document.getElementById("status").value.toLowerCase();
    const search = document.getElementById("searchBox").value.toLowerCase();

    const rows = document.querySelectorAll("#delivery-table tbody tr");
    rows.forEach(row => {
        const rowStatus = row.cells[6].textContent.trim().toLowerCase();
        const customer = row.cells[3].textContent.trim().toLowerCase();
        const orderNo = row.cells[2].textContent.trim().toLowerCase();
        const matchSearch = customer.includes(search) || orderNo.includes(search);
        const matchStatus = !status || rowStatus === status;
        row.style.display = (matchStatus && matchSearch) ? "" : "none";
    });
}
