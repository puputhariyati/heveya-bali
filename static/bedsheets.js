const colors = ["White", "Sand", "Grey", "Dark Grey", "Sage", "Moss Green", "Blush Mauve", "Burnt Orange", "Lilac"].sort((a, b) => b.length - a.length);
const materials = ["Bamboo Lyocell", "Linen", "Bamboo Cotton"];
const types = ["Fitted", "Duvet", "Flat", "PC", "BC"];
const sizes = ["SK", "K", "Q", "S"];
const filterSelect = document.getElementById('filter');
const tableContainer = document.getElementById('table-container');
const materialSelect = document.getElementById('material-filter');


// Define the ideal stock levels for showroom (per item)
const idealStock = {
  "Fitted_SK": 5,
  "Fitted_K": 5,
  "Fitted_Q": 5,
  "Fitted_S": 5,
  "Duvet_SK": 5,
  "Duvet_K": 5,
  "Duvet_Q": 5,
  "Duvet_S": 5,
  "Flat_SK": 5,
  "Flat_K": 5,
  "Flat_Q": 5,
  "Flat_S": 5,
  "PC": 5,
  "BC": 5,
};

// Store product data by material, source, color, type, and size
let stockData = {
  heveya: {}, warehouse: {}, total: {}, request: {}
};

// Parse name to material, color, type, size
function parseProductName(name) {
  name = name.toLowerCase();
  const material = materials.find(m => name.includes(m.toLowerCase()));
  const color = colors.find(c => name.includes(c.toLowerCase()));
  let type = '';
  if (name.includes("fitted")) type = "Fitted";
  else if (name.includes("duvet")) type = "Duvet";
  else if (name.includes("flat")) type = "Flat";
  else if (name.includes("pillow case") || name.includes("pc")) type = "PC";
  else if (name.includes("bolster case") || name.includes("bc")) type = "BC";

  let size = '';
  if (name.includes("super king") || name.includes("sk")) size = "SK";
  else if (name.includes("king") || name.includes("k")) size = "K";
  else if (name.includes("queen") || name.includes("q")) size = "Q";
  else if (name.includes("single") || name.includes("s")) size = "S";

  return { material, color, type, size };
}

// Helper: get nested object value
function getStockQty(source, material, color, type, size) {
  try {
    return stockData[source][material][color][type][size] || 0;
  } catch {
    return 0;
  }
}

// Helper: set nested object value
function setStockQty(source, material, color, type, size, value) {
  if (!stockData[source][material]) stockData[source][material] = {};
  if (!stockData[source][material][color]) stockData[source][material][color] = {};
  if (!stockData[source][material][color][type]) stockData[source][material][color][type] = {};
  stockData[source][material][color][type][size] = value;
}

// Generate one table for a material + source
function generateTable(material, source) {
  const titleMap = {
    heveya: "Heveya Showroom",
    warehouse: "Warehouse Bali",
    total: "Total Stock Bali",
    request: "Request To Showroom"
  };
  const title = `${material} - ${titleMap[source]}`;

  const table = document.createElement('table');
  const caption = document.createElement('h2');
  caption.textContent = title;

  const thead = document.createElement('thead');
  const header1 = document.createElement('tr');
  const header2 = document.createElement('tr');
  header1.innerHTML = `
    <th rowspan="2">${material}</th>
    <th colspan="4">Fitted</th>
    <th colspan="4">Duvet</th>
    <th colspan="4">Flat</th>
    <th rowspan="2">PC</th>
    <th rowspan="2">BC</th>
  `;
  types.slice(0, 3).forEach(() => {
    header2.innerHTML += `<th>SK</th><th>K</th><th>Q</th><th>S</th>`;
  });

  thead.append(header1, header2);

  const tbody = document.createElement('tbody');

  colors.forEach(color => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="section-title">${color}</td>`;

    // Fitted/Duvet/Flat with sizes
    types.forEach(type => {
      if (["PC", "BC"].includes(type)) {
        const qty = getStockQty(source, material, color, type, '');
        tr.innerHTML += `<td>${qty}</td>`;
      } else {
        sizes.forEach(size => {
          const qty = getStockQty(source, material, color, type, size);
          tr.innerHTML += `<td>${qty}</td>`;
        });
      }
    });

    tbody.appendChild(tr);
  });

  table.appendChild(thead);
  table.appendChild(tbody);
  return [caption, table];
}

// Build all tables based on filter
function renderTables(filter) {
  tableContainer.innerHTML = '';

  let sourcesToShow = [];
  if (filter === 'all') sourcesToShow = ['heveya', 'warehouse', 'total', 'request'];
  else sourcesToShow = [filter];

  materials.forEach(material => {
    sourcesToShow.forEach(source => {
      const [caption, table] = generateTable(material, source);
      tableContainer.appendChild(caption);
      tableContainer.appendChild(table);
    });
  });
}

// Fetch and process data
async function fetchAndPrepare() {
  const res = await fetch("/sync_bedsheets");
  const { data: products } = await res.json();

  // Reset storage
  stockData = { heveya: {}, warehouse: {}, total: {}, request: {} };

  products.forEach(product => {
    const { name, quantity, location } = product;
    const { material, color, type, size } = parseProductName(name);
    if (!material || !color || !type) return;

    const qty = Number(quantity || 0);
    const source = location.includes("Warehouse") ? "warehouse" : "heveya";
    setStockQty(source, material, color, type, size, qty);
  });

  // Calculate total stock
  materials.forEach(material => {
    colors.forEach(color => {
      types.forEach(type => {
        if (["PC", "BC"].includes(type)) {
          const hQty = getStockQty("heveya", material, color, type, '');
          const wQty = getStockQty("warehouse", material, color, type, '');
          setStockQty("total", material, color, type, '', hQty + wQty);
        } else {
          sizes.forEach(size => {
            const hQty = getStockQty("heveya", material, color, type, size);
            const wQty = getStockQty("warehouse", material, color, type, size);
            setStockQty("total", material, color, type, size, hQty + wQty);
          });
        }
      });
    });
  });

  // Calculate request to showroom
  materials.forEach(material => {
    colors.forEach(color => {
      types.forEach(type => {
        if (["PC", "BC"].includes(type)) {
          const ideal = idealStock[type] || 0;
          const h = getStockQty("heveya", material, color, type, '');
          const w = getStockQty("warehouse", material, color, type, '');
          const req = Math.min(ideal - h, w);
          setStockQty("request", material, color, type, '', Math.max(0, req));
        } else {
          sizes.forEach(size => {
            const ideal = idealStock[`${type}_${size}`] || 0;
            const h = getStockQty("heveya", material, color, type, size);
            const w = getStockQty("warehouse", material, color, type, size);
            const req = Math.min(ideal - h, w);
            setStockQty("request", material, color, type, size, Math.max(0, req));
          });
        }
      });
    });
  });

  renderTables(filterSelect.value);
}

filterSelect.addEventListener("change", () => {
  renderTables(filterSelect.value);
});

fetchAndPrepare();
