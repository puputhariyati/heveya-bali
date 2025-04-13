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

async function loadLeads() {
  const res = await fetch("/api/crm");
  const leads = await res.json();

  const tbody = document.querySelector("#leads-table tbody");
  tbody.innerHTML = "";

  leads.forEach(lead => {
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
  loadSummary();
  loadLeads();
  renderProductPie();
  renderStatusPie(); // 👈 Add this
  ...
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
