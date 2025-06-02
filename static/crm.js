document.addEventListener("DOMContentLoaded", () => {
  loadSummary();
  loadLeads();

  const form = document.getElementById("lead-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = Object.fromEntries(new FormData(form).entries());

    try {
      const res = await fetch("/api/crm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to add lead.");

      alert("Lead added successfully!");
      form.reset();
      loadLeads();
      loadSummary();
    } catch (err) {
      alert(err.message);
    }
  });
});

async function loadSummary() {
  const res = await fetch("/api/summary");
  const data = await res.json();

  document.getElementById("total-leads").textContent = `Total Leads: ${data.total_leads}`;
  document.getElementById("success-leads").textContent = `Success: ${data.success}`;
  document.getElementById("fail-leads").textContent = `Fail: ${data.fail}`;
  document.getElementById("followup-leads").textContent = `Follow-up: ${data.follow_up}`;
  document.getElementById("total-amount").textContent = `Total Amount: $${data.total_amount}`;
}

const customerContacts = {};

async function loadLeads() {
  const res = await fetch("/api/crm");
  const leads = await res.json();

  const tbody = document.querySelector("#leads-table tbody");
  tbody.innerHTML = "";

  // Clear and rebuild contact dictionary
  Object.keys(customerContacts).forEach(key => delete customerContacts[key]);

  leads.forEach(lead => {
    // ✅ Store contact info
    customerContacts[lead.customer] = {
      mobile: lead.mobile,
      email: lead.email
    };

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${lead.customer}</td>
      <td>${lead.product}</td>
      <td>${lead.status}</td>
      <td>${lead.sales_person}</td>
      <td>$${lead.amount}</td>
      <td>${lead.date}</td>
      <td>${lead.source}</td>
      <td>${lead.mobile}<br>${lead.email}</td>
    `;
    tbody.appendChild(tr);
  });

  // ✅ Re-bind auto-fill listener AFTER loading contacts
  setupAutoFill();
}

let productPieChart;

async function renderProductPie() {
  const res = await fetch("/api/crm");
  const leads = await res.json();

  const productMap = {};
  leads.forEach(lead => {
    if (!productMap[lead.product]) productMap[lead.product] = [];
    productMap[lead.product].push(lead.customer);
  });

  const products = Object.keys(productMap);
  const counts = products.map(p => productMap[p].length);
  const colors = products.map(() => `hsl(${Math.random() * 360}, 60%, 60%)`);

  const ctx = document.getElementById("productPie").getContext("2d");
  if (productPieChart) productPieChart.destroy();

  productPieChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: products,
      datasets: [{
        label: "Leads by Product",
        data: counts,
        backgroundColor: colors,
      }]
    },
    options: {
      onClick: function (evt, elements) {
        if (elements.length > 0) {
          const index = elements[0].index;
          const product = products[index];
          const customers = productMap[product];
          const container = document.getElementById("productDetails");
          container.innerHTML = `<strong>${product} (${customers.length} leads):</strong><br>` +
            customers.map(c => `• ${c}`).join("<br>");
        }
      },
      plugins: {
        legend: {
          position: "bottom"
        }
      }
    }
  });
}

// Call this when the page loads
document.addEventListener("DOMContentLoaded", () => {
  renderProductPie();
  renderStatusPie(); // 👈 Add this
  setTodayAsDefaultDate(); // ✅ Set today's date by default
  setupAutoFill();
});


let statusPieChart;

async function renderStatusPie() {
  const res = await fetch("/api/crm");
  const leads = await res.json();

  const statusMap = {};
  leads.forEach(lead => {
    if (!statusMap[lead.status]) statusMap[lead.status] = [];
    statusMap[lead.status].push(lead.customer);
  });

  const statuses = Object.keys(statusMap);
  const counts = statuses.map(s => statusMap[s].length);
  const colors = statuses.map(() => `hsl(${Math.random() * 360}, 60%, 70%)`);

  const ctx = document.getElementById("statusPie").getContext("2d");
  if (statusPieChart) statusPieChart.destroy();

  statusPieChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: statuses,
      datasets: [{
        label: "Leads by Status",
        data: counts,
        backgroundColor: colors,
      }]
    },
    options: {
      onClick: function (evt, elements) {
        if (elements.length > 0) {
          const index = elements[0].index;
          const status = statuses[index];
          const customers = statusMap[status];
          const container = document.getElementById("statusDetails");
          container.innerHTML = `<strong>${status} (${customers.length} leads):</strong><br>` +
            customers.map(c => `• ${c}`).join("<br>");
        }
      },
      plugins: {
        legend: {
          position: "bottom"
        }
      }
    }
  });
}

// ✅ Autofill listener (called from loadLeads)
function setupAutoFill() {
  const nameInput = document.querySelector('input[placeholder="Customer Name"]');
  const mobileInput = document.querySelector('input[placeholder="Mobile"]');
  const emailInput = document.querySelector('input[placeholder="Email"]');

  if (!nameInput || !mobileInput || !emailInput) return;

  nameInput.removeEventListener("input", autoFillHandler); // Avoid multiple bindings
  nameInput.addEventListener("input", autoFillHandler);

  function autoFillHandler() {
    const name = nameInput.value.trim();
    const contact = customerContacts[name];
    if (contact) {
      mobileInput.value = contact.mobile;
      emailInput.value = contact.email;
    } else {
      mobileInput.value = "";
      emailInput.value = "";
    }
  }
}

// ✅ Set today's date as default
function setTodayAsDefaultDate() {
  const dateInput = document.querySelector('input[type="date"]');
  if (dateInput) {
    const today = new Date().toISOString().split("T")[0];
    dateInput.value = today;
  }
}

// Filter table rows by customer name
function filterTable() {
  const input = document.getElementById("searchInput");
  const filter = input.value.toLowerCase();
  const table = document.querySelector("table");
  const rows = table.getElementsByTagName("tr");

  for (let i = 1; i < rows.length; i++) { // skip header
    const customerCell = rows[i].getElementsByTagName("td")[0];
    if (customerCell) {
      const txtValue = customerCell.textContent || customerCell.innerText;
      rows[i].style.display = txtValue.toLowerCase().includes(filter) ? "" : "none";
    }
  }
}