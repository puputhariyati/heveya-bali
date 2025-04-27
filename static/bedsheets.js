const colors = ["White", "Sand", "Grey", "Dark Grey", "Sage", "Moss Green", "Blush Mauve", "Burnt Orange", "Lilac"];
const tbody = document.getElementById('table-body');

// STEP 1: Build the empty table
colors.forEach(color => {
  const tr = document.createElement('tr');
  const tdColor = document.createElement('td');
  tdColor.className = 'section-title';
  tdColor.textContent = color;
  tr.appendChild(tdColor);

  for (let i = 0; i < 14; i++) {
    const td = document.createElement('td');
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = '-';
    input.dataset.color = color;
    input.dataset.index = i; // 0-13
    td.appendChild(input);
    tr.appendChild(td);
  }

  tbody.appendChild(tr);
});

// STEP 2: Mapping helper
function findInput(color, type, size) {
  const row = Array.from(tbody.querySelectorAll('tr')).find(tr => tr.querySelector('td').textContent.trim() === color);
  if (!row) return null;

  const inputs = row.querySelectorAll('input');
  let inputIndex = -1;

  if (type === 'Fitted') {
    if (size === 'SK') inputIndex = 0;
    if (size === 'K') inputIndex = 1;
    if (size === 'Q') inputIndex = 2;
    if (size === 'S') inputIndex = 3;
  } else if (type === 'Duvet') {
    if (size === 'SK') inputIndex = 4;
    if (size === 'K') inputIndex = 5;
    if (size === 'Q') inputIndex = 6;
    if (size === 'S') inputIndex = 7;
  } else if (type === 'Flat') {
    if (size === 'SK') inputIndex = 8;
    if (size === 'K') inputIndex = 9;
    if (size === 'Q') inputIndex = 10;
    if (size === 'S') inputIndex = 11;
  } else if (type === 'PC') {
    inputIndex = 12;
  } else if (type === 'BC') {
    inputIndex = 13;
  }

  return inputs[inputIndex] || null;
}

// STEP 3: Fetch real products from API
async function fetchProducts() {
  try {
    const response = await fetch("/sync_bedsheets", {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    const products = data.data || [];

    console.log("✅ Products fetched:", products); // <--- ADD THIS to debug!

    products.forEach(product => {
      const name = product.name.toLowerCase();
      const qty = product.quantity ?? 0; // Always at least 0

      let color = colors.find(c => name.includes(c.toLowerCase()));
      if (!color) return;

      let type = '';
      if (name.includes('fitted')) type = 'Fitted';
      else if (name.includes('duvet')) type = 'Duvet';
      else if (name.includes('flat')) type = 'Flat';
      else if (name.includes('pillow case') || name.includes('pc')) type = 'PC';
      else if (name.includes('bolster case') || name.includes('bc')) type = 'BC';
      else return;

      let size = '';
      if (name.includes('super king') || name.includes('sk')) size = 'SK';
      else if (name.includes('king') || name.includes('k')) size = 'K';
      else if (name.includes('queen') || name.includes('q')) size = 'Q';
      else if (name.includes('single') || name.includes('s')) size = 'S';

      const input = findInput(color, type, size);
      if (input) {
        input.value = qty;
      }
    });

    // Fill empty inputs with 0
    tbody.querySelectorAll('input').forEach(input => {
      if (input.value === '') {
        input.value = '-';
      }
    });

  } catch (error) {
    console.error('Fetch error:', error);
  }
}

// STEP 4: Run it after page load
fetchProducts();
