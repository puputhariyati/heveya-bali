function toggleInternal() {
  const toggleButton = document.getElementById('toggle-view-btn');

  document.querySelectorAll('.internal-only').forEach(el => {
    el.style.display = (el.style.display === 'table-cell' || el.style.display === 'table-row') ? 'none' : (el.tagName === 'TR' ? 'table-row' : 'table-cell');
  });

  // Check if any internal-only elements are visible after toggling
  const isInternalViewActive = document.querySelector('.internal-only').style.display === 'table-cell' || document.querySelector('.internal-only').style.display === 'table-row';

  // Update button text based on the current view
  if (isInternalViewActive) {
    toggleButton.textContent = 'Client View';
  } else {
    toggleButton.textContent = 'Internal View';
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const today = new Date();
  // Format: YYYY-MM-DD for input[type="date"]
  const toDateInputValue = date =>
    date.toISOString().split("T")[0];

  document.getElementById("quote-date").value = toDateInputValue(today);

  const expiry = new Date(today);
  expiry.setMonth(today.getMonth() + 1);
  while (expiry.getMonth() !== (today.getMonth() + 1) % 12) {
    expiry.setDate(expiry.getDate() - 1);
  }
  document.getElementById("quote-expiry").value = toDateInputValue(expiry);
  document.getElementById("toggle-view-btn").textContent = "Internal View";
});


let rowCount = 1;

function addRow() {
  const tbody = document.getElementById("quote-items");
  const row = document.createElement("tr");

  row.innerHTML = `
    <td>${rowCount++}</td>
    <td><img src="https://via.placeholder.com/60" class="product-image" width="60"></td>
    <td>
      <input type="text" class="description" placeholder="Type product..." oninput="showSuggestions(this)">
      <div class="suggestions"></div>
    </td>
    <td><input type="number" class="qty" value="1" min="1" onchange="recalculate(this)"></td>
    <td class="unit">-</td>
    <td class="unit-price">-</td>
    <td><input type="number" class="discount" value="0" min="0" max="100" onchange="recalculate(this)"></td>
    <td class="amount">-</td>
    <td><input type="text" class="notes" placeholder="Optional"></td>
    <td><button onclick="this.closest('tr').remove()">🗑️</button></td>
  `;

  tbody.appendChild(row);
}

function showSuggestions(input) {
  const wrapper = input.parentElement;
  const suggestionsBox = wrapper.querySelector('.suggestions');
  const query = input.value.toLowerCase();
  suggestionsBox.innerHTML = '';

  const keywords = query.split(/\s+/);

  const matched = productDB.filter(p => {
    if (!p.name) return false;  // 🔐 Safe guard
    const name = p.name.toLowerCase();
    return keywords.every(kw => name.includes(kw));
  });

  matched.forEach(product => {
    const div = document.createElement('div');
    div.textContent = product.name;
    div.classList.add('suggestion-item');
    div.onclick = () => selectProduct(input, product);
    suggestionsBox.appendChild(div);
  });

  suggestionsBox.style.display = matched.length ? 'block' : 'none';
}

function selectProduct(input, product) {
  const row = input.closest('tr');
  const image = row.querySelector('.product-image');
  const unit = row.querySelector('.unit');
  const unitPrice = row.querySelector('.unit-price');
  const cost = row.querySelector('.unit-cost');

  input.value = product.name;
  image.src = `/static/images/${product.image_url}`;
  unit.textContent = product.Unit;

  const price = parseInt(product["Normal Price IDR"].replace(/,/g, '')) || 0;
  const costValue = parseInt(product["unit cost"].replace(/,/g, '')) || 0;

  unitPrice.textContent = price.toLocaleString("id-ID");
  unitPrice.dataset.price = price;
  cost.textContent = costValue.toLocaleString("id-ID");
  cost.dataset.cost = costValue;

  // ✅ Clear the suggestion box completely
  const suggestionsBox = input.nextElementSibling;
  suggestionsBox.innerHTML = '';
  suggestionsBox.style.display = 'none';
  suggestionsBox.style.border = 'none';
  suggestionsBox.style.boxShadow = 'none';

  recalculate(row.querySelector('.qty'));
}

// Hide suggestions on click outside
document.addEventListener('click', function (event) {
  document.querySelectorAll('.suggestions').forEach(suggestionsBox => {
    const wrapper = suggestionsBox.closest('.input-wrapper');
    if (!wrapper) return;

    const input = wrapper.querySelector('textarea'); // or 'input, textarea' if both types

    if (
      !suggestionsBox.contains(event.target) &&
      !input.contains(event.target)
    ) {
      suggestionsBox.style.display = 'none';
    }
  });
});


function recalculate(input) {
  const row = input.closest('tr');
  const qty = parseFloat(row.querySelector('.qty').value) || 0;
  const discount = parseFloat(row.querySelector('.discount').value) || 0;
  const unitPriceEl = row.querySelector('.unit-price');
  const discountedPriceEl = row.querySelector('.discounted-price');
  const amountEl = row.querySelector('.amount');
  const price = parseFloat(unitPriceEl.dataset.price || 0);

  // Calculate discounted price
  const discPrice = price * (1 - discount / 100);
  if (discountedPriceEl) {
    discountedPriceEl.textContent = formatCurrency(discPrice);
  }
  // Calculate total amount
  const amount = discPrice * qty;
  amountEl.textContent = formatCurrency(amount);
  // If you have internal-only calculations, call updateAmount or similar
  if (row.querySelector('.full-amount')) {
    updateAmount(input); // already does margin and cost
  }
  updateTotals(); // update footer totals if needed
}

function updateAmount(input) {
  const row = input.closest("tr");
  const qty = Number(row.querySelector(".qty").value || 0);
  const discount = Number(row.querySelector(".discount").value || 0);
  const unitPrice = Number(row.querySelector(".unit-price").dataset.price || 0);
  const unitCost = Number(row.querySelector(".unit-cost").dataset.cost || 0);

  const discounted = unitPrice - (unitPrice * discount / 100);
  const amount = Math.round(discounted * qty);

  row.querySelector(".amount").textContent = amount.toLocaleString("id-ID");
  row.querySelector(".full-amount").textContent = (unitPrice * qty).toLocaleString("id-ID");

  const sellingNoPPN = Math.round(amount / 1.11);
  const totalCost = unitCost * qty;
  const absMargin = sellingNoPPN - totalCost;
  const marginPercent = sellingNoPPN ? (absMargin / sellingNoPPN) * 100 : 0;

  row.querySelector(".sell-no-ppn").textContent = sellingNoPPN.toLocaleString("id-ID");
  row.querySelector(".total-cost").textContent = totalCost.toLocaleString("id-ID");
  row.querySelector(".abs-margin").textContent = absMargin.toLocaleString("id-ID");
}

// Update totals for the internal-only table
function updateTotals() {
  let totalAmount = 0;
  let totalFullAmount = 0;
  let totalSellingPriceNoPPN = 0;
  let totalCost = 0;
  let totalAbsMargin = 0;

  document.querySelectorAll("#quote-items tr").forEach(row => {
    const amount = parseCurrency(row.querySelector(".amount")?.textContent);
    const fullAmount = parseCurrency(row.querySelector(".full-amount")?.textContent);
    const sellNoPPN = parseCurrency(row.querySelector(".sell-no-ppn")?.textContent);
    const cost = parseCurrency(row.querySelector(".total-cost")?.textContent);
    const margin = parseCurrency(row.querySelector(".abs-margin")?.textContent);

    totalAmount += amount;
    totalFullAmount += fullAmount;
    totalSellingPriceNoPPN += sellNoPPN;
    totalCost += cost;
    totalAbsMargin += margin;
  });

  // Update client view
  document.getElementById("grand-total").textContent = formatCurrency(totalAmount);
  document.getElementById("total-discount").textContent = formatCurrency(totalFullAmount - totalAmount);

  // Update internal-only view
  document.querySelector(".full-amount-total").textContent = formatCurrency(totalFullAmount);
  document.querySelector(".sell-no-ppn-total").textContent = formatCurrency(totalSellingPriceNoPPN);
  document.querySelector(".total-cost-total").textContent = formatCurrency(totalCost);
  document.querySelector(".abs-margin-total").textContent = formatCurrency(totalAbsMargin);

  // Margin %
  const marginPercent = totalSellingPriceNoPPN > 0 ? (totalAbsMargin / totalSellingPriceNoPPN) * 100 : 0;
  document.querySelector(".margin-percent-total").textContent = marginPercent.toFixed(1) + "%";

  // Deposit
  const depositPercent = parseFloat(document.getElementById("deposit-percentage").value || 0);
  const depositAmount = totalAmount * (depositPercent / 100);
  document.getElementById("deposit-amount").textContent = formatCurrency(depositAmount);
}


// Helper function to parse currency strings
function parseCurrency(currencyStr) {
  if (!currencyStr) return 0;
  return parseFloat(currencyStr.replace(/\./g, '').replace(/,/g, '.').replace(/[^\d.-]/g, '')) || 0;
}

function formatCurrency(num) {
  return new Intl.NumberFormat('id-ID').format(num);
}

function downloadPDF() {
  // Optionally hide empty rows before printing
  document.querySelectorAll('#quote-items tr').forEach(row => {
    const desc = row.querySelector('.description');
    if (desc && !desc.value.trim()) {
      row.style.display = 'none';
    }
  });

  // Trigger browser's native print preview
  window.print();
}


