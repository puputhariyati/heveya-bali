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

function getSelectedTransactionNos(){
  return Array.from(document.querySelectorAll(".row-check:checked"))
              .map(cb => cb.value);          // read the value attr
}


function updateETD(transactionNo, newDate) {
    fetch("/sales_invoices/update_etd", {
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
  // 1. collect selected transaction numbers
  const txs = Array.from(document.querySelectorAll(".row-check:checked"))
                   .map(cb => cb.value)           // value="<transaction_no>"
                   .filter(Boolean);

  if (!txs.length) {
    alert("Please select at least one order.");
    return;
  }

  // 2. send to backend
  fetch("/sales_invoices/bulk_update_status", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transaction_nos: txs, status })
  })
  .then(res => res.json())
  .then(data => {
    if (!data.success) {
      alert("Update failed: " + (data.message || "unknown error"));
      return;
    }

    // 3. patch each updated row in the DOM (keeps current page)
    data.rows.forEach(r => {
      const row = document
        .querySelector(`input.row-check[value="${r.transaction_no}"]`)
        ?.closest("tr");
      const cell = row ? row.querySelector(".status-cell") : null;
      if (cell) {
        cell.textContent =
          r.status.charAt(0).toUpperCase() + r.status.slice(1);
      }
    });

    alert(`Status updated for ${data.updated} order${data.updated !== 1 ? "s" : ""}!`);

    // optional: uncheck boxes after update
    document.querySelectorAll(".row-check:checked").forEach(cb => cb.checked = false);
  })
  .catch(err => {
    console.error(err);
    alert("Network or server error: " + err);
  });
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

    fetch("/sales_invoices/bulk_update_etd", {
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

// for Calendar View
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth();

function showCalendarView() {
  const modal = document.getElementById("calendarModal");
  modal.style.display = "block";

  populateMonthYearSelectors();
  buildCalendar(); // now a separate function
}

function populateMonthYearSelectors() {
  const monthSelect = document.getElementById("calendarMonth");
  const yearSelect = document.getElementById("calendarYear");

  const monthNames = [...Array(12).keys()].map(i =>
    new Date(0, i).toLocaleString('default', { month: 'long' })
  );

  monthSelect.innerHTML = monthNames.map((m, i) =>
    `<option value="${i}" ${i === currentMonth ? 'selected' : ''}>${m}</option>`
  ).join('');

  const thisYear = new Date().getFullYear();
  yearSelect.innerHTML = "";
  for (let y = thisYear - 2; y <= thisYear + 2; y++) {
    yearSelect.innerHTML += `<option value="${y}" ${y === currentYear ? 'selected' : ''}>${y}</option>`;
  }
}

function buildCalendar() {
  const month = parseInt(document.getElementById("calendarMonth").value);
  const year = parseInt(document.getElementById("calendarYear").value);
  currentMonth = month;
  currentYear = year;

  const grid = document.getElementById("calendarGrid");
  grid.innerHTML = "";

  const monthStart = new Date(year, month, 1);
  const monthEnd = new Date(year, month + 1, 0);
  const daysInMonth = monthEnd.getDate();
  const firstDayOfWeek = monthStart.getDay(); // Sunday = 0

  const orderCountByDate = {};
  salesOrders.forEach(order => {
    if (order.etd) {
      const date = order.etd.slice(0, 10); // yyyy-MM-dd
      orderCountByDate[date] = (orderCountByDate[date] || 0) + 1;
    }
  });

  for (let i = 0; i < firstDayOfWeek; i++) {
    grid.innerHTML += `<div></div>`;
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day);
    const iso = date.toISOString().slice(0, 10);
    const count = orderCountByDate[iso] || 0;

    const cell = document.createElement("div");
    cell.className = "calendar-day";
    if (count > 0) cell.classList.add("has-orders");
    cell.innerHTML = `<strong>${day}</strong><br><small>${count}</small>`;
    cell.onclick = () => {
      filterOrdersByETD(iso);
      closeCalendar();
    };
    grid.appendChild(cell);
  }
}

function prevMonth() {
  if (currentMonth === 0) {
    currentMonth = 11;
    currentYear--;
  } else {
    currentMonth--;
  }
  document.getElementById("calendarMonth").value = currentMonth;
  document.getElementById("calendarYear").value = currentYear;
  buildCalendar();
}

function nextMonth() {
  if (currentMonth === 11) {
    currentMonth = 0;
    currentYear++;
  } else {
    currentMonth++;
  }
  document.getElementById("calendarMonth").value = currentMonth;
  document.getElementById("calendarYear").value = currentYear;
  buildCalendar();
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

function closeCalendar() {
  document.getElementById("calendarModal").style.display = "none";
}

function filterByDateRange() {
  const start = document.getElementById("startDate").value;
  const end = document.getElementById("endDate").value;
  const rows = document.querySelectorAll("#delivery-table tbody tr");

  rows.forEach(row => {
    const txDateText = row.children[1].textContent.trim(); // e.g., "04/06/2025"
    const [dd, mm, yyyy] = txDateText.split("/");
    const txDate = new Date(`${yyyy}-${mm}-${dd}`);

    let show = true;

    if (start) {
      const startDate = new Date(start);
      if (txDate < startDate) show = false;
    }

    if (end) {
      const endDate = new Date(end);
      if (txDate > endDate) show = false;
    }

    row.style.display = show ? "" : "none";
  });
}

/* -------------  PAGINATION STATE ------------- */
let allOrders      = salesOrders;        // array injected from Jinja
let filteredOrders = [...allOrders];     // after search / status filters
let rowsPerPage    = 25;
let currentPage    = 1;

/* ----------  MAIN RENDER FUNCTION ----------- */
function renderTable() {
  const tbody = document.querySelector("#delivery-table tbody");
  tbody.innerHTML = "";

  const total = filteredOrders.length;
  const start = (currentPage - 1) * rowsPerPage;
  const end   = Math.min(start + rowsPerPage, total);

  // slice & build rows
  filteredOrders.slice(start, end).forEach(o => {
    const tr   = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" class="row-check"></td>
      <td>${o.transaction_date}</td>
      <td><a href="/sales_invoices/${o.transaction_no}">${o.transaction_no}</a></td>
      <td>${o.customer || "-"}</td>
      <td>${o.balance_due || "-"}</td>
      <td>${o.total || "-"}</td>
      <td>${(o.status || "").charAt(0).toUpperCase() + (o.status||"").slice(1)}</td>
      <td><input type="date" value="${o.etd || ""}"
                 onchange="updateETD('${o.transaction_no}', this.value)"></td>`;
    tbody.appendChild(tr);
  });

  /* update pagination text / inputs */
  document.getElementById("pageInfo").textContent =
      total ? `Showing ${start + 1}‑${end} of ${total}`: "No data";
  const totalPages = Math.max(1, Math.ceil(total / rowsPerPage));
  document.getElementById("totalPages").textContent = `from ${totalPages} pages`;
  document.getElementById("pageInput").value = currentPage;
}

/* ----------  PAGINATION CONTROL HANDLERS ----------- */
function changeRowsPerPage(val){
  rowsPerPage = parseInt(val, 10) || 25;
  currentPage = 1;
  renderTable();
}
function prevPage(){
  if (currentPage > 1){ currentPage--; renderTable(); }
}
function nextPage(){
  const totalPages = Math.max(1, Math.ceil(filteredOrders.length / rowsPerPage));
  if (currentPage < totalPages){ currentPage++; renderTable(); }
}
function goToPage(val){
  const pageNum    = parseInt(val, 10) || 1;
  const totalPages = Math.max(1, Math.ceil(filteredOrders.length / rowsPerPage));
  currentPage = Math.min(Math.max(pageNum,1), totalPages);
  renderTable();
}

/* ----------  EXISTING FILTERS (hook pagination) ---- */
function filterOrders(){
  const status = document.getElementById("status").value.toLowerCase();
  const query  = document.getElementById("searchBox").value.toLowerCase();

  filteredOrders = allOrders.filter(o => {
    const statusOk = !status || o.status.toLowerCase() === status;
    const searchOk = !query  ||
      (o.customer && o.customer.toLowerCase().includes(query)) ||
      (o.transaction_no && o.transaction_no.toLowerCase().includes(query));
    return statusOk && searchOk;
  });
  currentPage = 1;
  renderTable();
}

/* ----------  INIT ------------- */
document.addEventListener("DOMContentLoaded", () => {
  renderTable();                     // initial draw
});

// Refresh Invoices Button
/* ============  (1) Load last‑refresh label on first load  ============ */
async function fetchLastRefreshLabel(){
  try{
    const res = await fetch("/api/last-refresh");   // backend must return {"last_refresh": "..."}
    const j   = await res.json();
    if (j.last_refresh){
      document.getElementById("lastRefresh").textContent =
        "Last refresh: " + new Date(j.last_refresh).toLocaleString();
    }
  }catch(e){
    console.warn("Could not load last‑refresh label:", e);
  }
}

/* ============  (2) Click handler for 🔄 Refresh orders  ============== */
async function handleRefreshClick(event){
  const btn = event.target;
  const originalLabel = btn.textContent;
  btn.disabled  = true;
  btn.textContent = "Refreshing…";

  try{
    const res = await fetch("/api/refresh-sales-invoices", {method:"POST"});
    const j   = await res.json();

    if (j.status === "ok"){
      alert(`✅ Sync complete — inserted: ${j.added}, updated: ${j.updated}`);
      document.getElementById("lastRefresh").textContent =
        "Last refresh: " + new Date(j.last_refresh).toLocaleString();
      location.reload();                       // rebuild table & pagination
    } else {
      alert("❌ Refresh failed: " + j.msg);
    }
  }catch(err){
    alert("❌ Network / server error: " + err);
  }

  btn.disabled  = false;
  btn.textContent = originalLabel;
}

/* ============  (3) Initialise after DOM ready ======================= */
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btnRefresh")
          .addEventListener("click", handleRefreshClick);

  fetchLastRefreshLabel();       // comment this line out if /api/last-refresh not yet implemented
});

