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

function showCalendarView() {
  const modal = document.getElementById("calendarModal");
  const grid = document.getElementById("calendarGrid");
  const title = document.getElementById("calendarTitle");

  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth(); // 0-indexed
  const monthStart = new Date(year, month, 1);
  const monthEnd = new Date(year, month + 1, 0);
  const daysInMonth = monthEnd.getDate();

  title.textContent = `${monthStart.toLocaleString("default", { month: "long" })} ${year}`;
  grid.innerHTML = "";

  // Build order count by date
  const orderCountByDate = {};
  salesOrders.forEach(order => {
    if (order.etd) {
      const date = order.etd.slice(0, 10); // "2025-06-25"
      orderCountByDate[date] = (orderCountByDate[date] || 0) + 1;
    }
  });

  // Add empty slots for days before 1st of month
  const firstDayOfWeek = monthStart.getDay(); // 0 = Sunday
  for (let i = 0; i < firstDayOfWeek; i++) {
    grid.innerHTML += `<div></div>`;
  }

  // Render each day
  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day);
    const iso = date.toISOString().slice(0, 10);
    const count = orderCountByDate[iso] || 0;

    const cell = document.createElement("div");
    cell.className = "calendar-day";
    if (count > 0) {
      cell.classList.add("has-orders");
    }
    cell.innerHTML = `<strong>${day}</strong><br><small>${count}</small>`;
    cell.onclick = () => {
      filterOrdersByETD(iso);
      closeCalendar();
    };

    grid.appendChild(cell);
  }

  modal.style.display = "block";
}

function closeCalendar() {
  document.getElementById("calendarModal").style.display = "none";
}

// Filter sales orders in table by ETD date
function filterOrdersByETD(etdDate) {
  const rows = document.querySelectorAll("#delivery-table tbody tr");
  rows.forEach(row => {
    const etdInput = row.querySelector("input[type='date']");
    if (etdInput && etdInput.value === etdDate) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}

