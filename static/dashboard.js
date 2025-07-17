function loadAllCharts() {
  console.log("🔁 Apply button clicked");
    const startDate = document.getElementById("startDate").value;
    const endDate = document.getElementById("endDate").value;
  Promise.all([
    fetch(`/api/sales-by-category?start_date=${startDate}&end_date=${endDate}`).then(res => res.json()),
    fetch("/static/data/products_std.csv").then(res => res.text()),
    fetch("/static/data/customer_total_payments.csv").then(res => res.text())
  ])
    .then(([salesData, inventoryCSV, customerCSV]) => {
      console.log("📦 Sales Data:", salesData);
      console.log("📦 Inventory CSV:", inventoryCSV.slice(0, 200)); // Just a preview
      console.log("📦 Customer CSV:", customerCSV.slice(0, 200));

      // ✅ Safely parse the CSVs to arrays of objects
      const inventoryData = parseCSV(inventoryCSV);
      const customerData = parseCSV(customerCSV);

      // ✅ Render each chart
      renderSalesPie(salesData);
      renderInventoryPie(inventoryData);
      renderCustomerPie(customerData);
    })
    .catch(err => {
      console.error("🚨 Dashboard load failed:", err);
    });
}


function renderSalesPie(data) {
  console.log("🟢 Sales Pie Data Received:", data);
  const labels = data.map(d => d.name);
  const values = data.map(d => d.value);

  Plotly.newPlot("salesPieChart", [{
    type: "pie",
    showlegend: true,
    labels,
    values,
    textinfo: "label+percent+value",
    textposition: "inside",
    insidetextorientation: "radial",
    textfont: { size: 12 },
  }], {
    height: 500,     // keep height
    // remove width
    legend: {
      orientation: "h",
      x: 0.9,
      xanchor: "right",
      y: -0.3,
      itemwidth: 50,// ⬅️ Reduce this to pull text closer to the color box
      yanchor: "middle",
      font: { size: 12 }
    },
    margin: { l: 30, r: 50, t: 50, b: 40 }
  }, {
    responsive: true
  });

  document.getElementById("salesPieChart").on('plotly_click', function(eventData) {
    const clickedCategory = eventData.points[0].label;
    const startDate = document.getElementById("startDate").value;
    const endDate = document.getElementById("endDate").value;

    fetch(`/api/sales-by-subcategory?category=${encodeURIComponent(clickedCategory)}&start_date=${startDate}&end_date=${endDate}`)
      .then(res => res.json())
      .then(renderSubcategoryPie);
  });
}


function renderSubcategoryPie(data) {
  Plotly.newPlot("salesPieChart", [{
    type: "pie",
    labels: data.map(d => d.name),
    values: data.map(d => d.value),
    textinfo: "label+percent+value",
    textposition: "inside",
  }], {
    title: "Subcategory Breakdown",
    height: 500,
    legend: {
      orientation: "h",
      x: 0.9,
      xanchor: "right",
      y: -0.3,
      font: { size: 12 }
    }
  });
}



// Basic CSV parser
function parseCSV(csvText) {
  const [headerLine, ...lines] = csvText.trim().split("\n");
  const headers = headerLine.split(",").map(h => h.trim());

  return lines.map(line => {
    const values = line.split(",").map(v => v.trim());
    const obj = {};
    headers.forEach((h, i) => {
      obj[h] = values[i];
    });
    return obj;
  });
}


function renderInventoryPie(data) {
  const totals = {};
  for (const row of data) {
    const cat = row.Category || "Unknown";
    const qty = parseFloat(row.warehouse_qty || 0);
    totals[cat] = (totals[cat] || 0) + qty;
  }

  const labels = Object.keys(totals);
  const values = Object.values(totals);

  Plotly.newPlot("inventoryPieChart", [{
    type: "pie",
    showlegend: true,
    labels,
    values,
    textinfo: "label+percent+value",
    textposition: "inside",
    insidetextorientation: "radial",
    textfont: { size: 12 },
  }], {
    height: 500,     // keep height
    // remove width
    legend: {
      orientation: "h",
      x: 0.9,
      xanchor: "right",
      y: -0.3,
      itemwidth: 50,// ⬅️ Reduce this to pull text closer to the color box
      yanchor: "middle",
      font: { size: 12 }
    },
    margin: { l: 30, r: 50, t: 50, b: 40 }
  }, {
    responsive: true
  });
}

function renderCustomerPie(data) {
  const buckets = {
    "<100mio": 0,
    "100–150mio": 0,
    "150–200mio": 0,
    ">200mio": 0
  };

  for (const row of data) {
    const rawPayment = row.total_payment || "0";  // ✅ Handle missing values
    const cleanPayment = parseFloat(rawPayment.replace(/[^0-9.]/g, "")) || 0;

    if (cleanPayment < 100_000_000) buckets["<100mio"]++;
    else if (cleanPayment <= 150_000_000) buckets["100–150mio"]++;
    else if (cleanPayment <= 200_000_000) buckets["150–200mio"]++;
    else buckets[">200mio"]++;
  }

  Plotly.newPlot("customerPieChart", [{
    type: "pie",
    labels: Object.keys(buckets),
    values: Object.values(buckets),
    textinfo: "label+percent+value",
    textposition: "inside",
  }], {
    height: 500,     // keep height
    // remove width
    legend: {
      orientation: "h",
      x: 0.9,
      xanchor: "right",
      y: -0.3,
      itemwidth: 50,// ⬅️ Reduce this to pull text closer to the color box
      yanchor: "middle",
      font: { size: 12 }
    },
    margin: { l: 30, r: 50, t: 50, b: 40 }
  }, {
    responsive: true
  });
}

document.addEventListener("DOMContentLoaded", loadAllCharts);
