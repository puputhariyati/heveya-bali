document.querySelectorAll('.sidebar-link').forEach(link => {
  link.addEventListener('click', () => {
    if (window.innerWidth <= 768) {
      document.querySelector('.sidebar').classList.remove('active'); // if using toggle logic
      document.querySelector('.main-content').style.display = 'block';
    }
  });
});


// static/dashboard_charts.js

// Load CSVs and render charts
Promise.all([
  fetch('/static/data/sales_orders_jun2025.csv').then(res => res.text()),
  fetch('/static/data/products_std.csv').then(res => res.text()),
  fetch('/static/data/customer_total_payments.csv').then(res => res.text())
]).then(([salesCSV, productsCSV, customersCSV]) => {
  renderSalesPie(parseCSV(salesCSV));
  renderInventoryPie(parseCSV(productsCSV));
  renderCustomerPie(parseCSV(customersCSV));
});

function parseCSV(str) {
  const [headerLine, ...lines] = str.trim().split("\n");
  const headers = headerLine.split(",").map(h => h.trim());
  return lines.map(line => {
    const values = line.split(",");
    return Object.fromEntries(headers.map((h, i) => [h, values[i]]));
  });
}

// Sales by Product (Category > Subcategory > Size > Color)
function renderSalesPie(data) {
  const groupBy = (arr, key) => {
    return arr.reduce((acc, obj) => {
      const group = obj[key] || "Unknown";
      acc[group] = acc[group] || 0;
      acc[group] += parseFloat(obj.quantity || 0);
      return acc;
    }, {});
  };
  const byCategory = groupBy(data, 'category');

  const labels = Object.keys(byCategory);
  const values = Object.values(byCategory);

  const trace = {
    labels,
    values,
    type: 'pie',
    textinfo: 'label+percent',
    hoverinfo: 'label+value',
  };

  Plotly.newPlot('salesPieChart', [trace], {
    title: 'Sales by Category',
    responsive: true
  });
}

// Inventory by Products (Category > Subcategory > Warehouse)
function renderInventoryPie(data) {
  const groupBy = (arr, key) => {
    return arr.reduce((acc, obj) => {
      const group = obj[key] || "Unknown";
      acc[group] = acc[group] || 0;
      acc[group] += parseFloat(obj.showroom_qty || 0) + parseFloat(obj.warehouse_qty || 0);
      return acc;
    }, {});
  };

  const byCategory = groupBy(data, 'Category');

  const labels = Object.keys(byCategory);
  const values = Object.values(byCategory);

  Plotly.newPlot('inventoryPieChart', [{
    labels,
    values,
    type: 'pie',
    textinfo: 'label+percent',
    hoverinfo: 'label+value'
  }], {
    title: 'Inventory by Category',
    responsive: true
  });
}

// Customers by Total Payment Bucket
function renderCustomerPie(data) {
  const buckets = {
    '<100 mio': 0,
    '100-150 mio': 0,
    '150-200 mio': 0,
    '>200 mio': 0
  };

  data.forEach(cust => {
    const amt = parseInt(cust.total.replace(/\D/g, '')) || 0;
    if (amt < 100000000) buckets['<100 mio'] += amt;
    else if (amt < 150000000) buckets['100-150 mio'] += amt;
    else if (amt < 200000000) buckets['150-200 mio'] += amt;
    else buckets['>200 mio'] += amt;
  });

  Plotly.newPlot('customerPieChart', [{
    labels: Object.keys(buckets),
    values: Object.values(buckets),
    type: 'pie',
    textinfo: 'label+percent',
    hoverinfo: 'label+value'
  }], {
    title: 'Customers by Total Order Amount',
    responsive: true
  });
}

// #sales report

// static/dashboard_kpi.js
Promise.all([
  fetch('/static/data/sales_orders_may2025.csv').then(res => res.text()),
  fetch('/static/data/sales_orders_jun2025.csv').then(res => res.text())
]).then(([mayCsv, junCsv]) => {
  const mayOrders = parseCSV(mayCsv);
  const junOrders = parseCSV(junCsv);
  renderKPI(mayOrders, junOrders);
});

function parseCSV(str) {
  const [headerLine, ...lines] = str.trim().split("\n");
  const headers = headerLine.split(",");
  return lines.map(line => {
    const values = line.split(',');
    return Object.fromEntries(headers.map((h, i) => [h.trim(), values[i]?.trim() || '']));
  });
}

function sumAmount(orders) {
  return orders.reduce((sum, row) => {
    const amount = parseInt((row.total || '').replace(/\D/g, '')) || 0;
    return sum + amount;
  }, 0);
}

function formatRupiah(num) {
  return 'Rp' + num.toLocaleString('id-ID');
}

function percent(actual, target) {
  return (actual / target * 100).toFixed(1) + '%';
}

function renderKPI(mayOrders, junOrders) {
  const targets = {
    yearly: 28000000000,
    Q1: 5880000000,
    Q2: 6160000000,
    Q3: 7280000000,
    Q4: 8680000000,
    April: 1745333333,
    May: 2258666667,
    June: 2156000000
  };

  const totals = {
    May: sumAmount(mayOrders),
    June: sumAmount(junOrders),
    April: 1825524138, // assumed fixed
    Q1: 4432484593,    // assumed fixed
  };
  totals.Q2 = totals.April + totals.May + totals.June;
  totals.yearly = totals.Q1 + totals.Q2;

  // Draw Chart.js line chart (optional)
  new Chart(document.getElementById("monthlyChart"), {
    type: 'bar',
    data: {
      labels: ["April", "May", "June"],
      datasets: [{
        label: 'Actual Sales',
        backgroundColor: '#5a9c4a',
        data: [totals.April, totals.May, totals.June]
      }]
    }
  });

  // Fill table
  const tbody = document.querySelector('#kpiTable tbody');
  tbody.innerHTML = `
    <tr class="highlight">
      <td>Yearly</td>
      <td>${formatRupiah(targets.yearly)}</td>
      <td>${formatRupiah(totals.yearly)}</td>
      <td>${percent(totals.yearly, targets.yearly)}</td>
    </tr>
    <tr><td>Q1</td><td>${formatRupiah(targets.Q1)}</td><td>${formatRupiah(totals.Q1)}</td><td>${percent(totals.Q1, targets.Q1)}</td></tr>
    <tr><td>Q2</td><td>${formatRupiah(targets.Q2)}</td><td>${formatRupiah(totals.Q2)}</td><td>${percent(totals.Q2, targets.Q2)}</td></tr>
    <tr><td>April</td><td>${formatRupiah(targets.April)}</td><td>${formatRupiah(totals.April)}</td><td>${percent(totals.April, targets.April)}</td></tr>
    <tr><td>May</td><td>${formatRupiah(targets.May)}</td><td>${formatRupiah(totals.May)}</td><td>${percent(totals.May, targets.May)}</td></tr>
    <tr><td>June</td><td>${formatRupiah(targets.June)}</td><td>${formatRupiah(totals.June)}</td><td>${percent(totals.June, targets.June)}</td></tr>
  `;
}
