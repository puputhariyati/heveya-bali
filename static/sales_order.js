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

function getSelectedTransactionNos() {
    return Array.from(document.querySelectorAll('.row-check:checked')).map(row => {
        return row.closest('tr').querySelector('a').textContent.trim(); // get transaction_no
    });
}

function updateETD(transactionNo, newDate) {
    fetch("/sales_order/update_etd", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            transaction_no: transactionNo,
            etd: newDate
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("✅ ETD saved for order " + transactionNo);
        } else {
            alert("❌ Failed to save ETD for " + transactionNo + ": " + data.message);
        }
    })
    .catch(err => {
        alert("❌ Error saving ETD for " + transactionNo + ": " + err);
    });
}



function bulkUpdateStatus(status) {
    const transactionNos = getSelectedTransactionNos();
    if (!transactionNos.length) {
        alert("Please select at least one order.");
        return;
    }

    fetch("/sales_order/bulk_update_status", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            transaction_nos: transactionNos,
            status: status
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Status updated successfully!");
            location.reload();
        } else {
            alert("Update failed: " + data.message);
        }
    })
    .catch(err => alert("Error: " + err));
}

function bulkUpdateETD() {
    const etd = document.getElementById("bulk-etd").value;
    const transactionNos = getSelectedTransactionNos();

    if (!etd) {
        alert("Please choose a date.");
        return;
    }
    if (!transactionNos.length) {
        alert("Please select at least one order.");
        return;
    }

    fetch("/sales_order/bulk_update_etd", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            transaction_nos: transactionNos,
            etd: etd
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("ETD updated successfully!");
            location.reload();
        } else {
            alert("Update failed: " + data.message);
        }
    })
    .catch(err => alert("Error: " + err));
}

