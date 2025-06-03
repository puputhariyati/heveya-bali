function downloadPDF() {
  const invoice = document.getElementById("invoice");
  html2pdf().from(invoice).set({
    margin: 10,
    filename: 'sales-quote.pdf',
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  }).save();
}

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

window.onload = function () {
  const today = new Date();
  const oneMonthLater = new Date();
  oneMonthLater.setMonth(today.getMonth() + 1);

  const toDateInputValue = date =>
    date.toISOString().split("T")[0]; // yyyy-mm-dd

  document.getElementById("quote-date").value = toDateInputValue(today);
  document.getElementById("quote-expiry").value = toDateInputValue(oneMonthLater);

  // Initialize the button text to "Internal View" since internal-only elements are hidden by default
  document.getElementById("toggle-view-btn").textContent = "Internal View";
};

// Mock database of products
const products = [
  {
    name: "Heveya Natural Organic Latex Mattress III - King -180x200x31cm - Medium",
    keywords: ["mattress iii king medium", "latex king medium"],
    unit: "pcs",
    unitPrice: 20000000
  },
  {
    name: "Heveya Bamboo Sheets - Queen",
    keywords: ["bamboo sheets queen", "sheets queen bamboo"],
    unit: "set",
    unitPrice: 1500000
  }
  // Add more items as needed
];

function addRow() {
  const tbody = document.getElementById("quote-body");
  const row = document.createElement("tr");

  row.innerHTML = `
    <td>
      <input type="text" class="desc-input" oninput="autoFillDetails(this)" style="width: 100%;" />
    </td>
    <td><input type="number" min="1" value="1" class="qty-input" oninput="updateAmount(this)" /></td>
    <td><span class="unit-text"></span></td>
    <td><input type="number" min="0" max="100" value="0" class="disc-input" oninput="updateAmount(this)" /></td>
    <td><span class="amount-text">0</span></td>
    <td><input type="text" class="note-input" /></td>
  `;

  tbody.appendChild(row);
}

function autoFillDetails(input) {
  const row = input.closest("tr");
  const unitCell = row.querySelector(".unit-text");
  const amountCell = row.querySelector(".amount-text");

  const desc = input.value.toLowerCase().trim();
  const product = products.find(p =>
    p.keywords.some(k => desc.includes(k))
  );

  if (product) {
    input.value = product.name;
    row.dataset.unitPrice = product.unitPrice;
    unitCell.textContent = product.unit;
  } else {
    row.dataset.unitPrice = 0;
    unitCell.textContent = '';
  }

  updateAmount(input);
}

function updateAmount(input) {
  const row = input.closest("tr");
  const qty = Number(row.querySelector(".qty-input").value || 0);
  const discount = Number(row.querySelector(".disc-input").value || 0);
  const unitPrice = Number(row.dataset.unitPrice || 0);
  const unitCost = Number(row.dataset.unitCost || 0);

  // Calculate amount (IDR)
  const discountedPrice = unitPrice - (unitPrice * discount / 100);
  const amount = Math.round(discountedPrice * qty);
  row.querySelector(".amount-text").textContent = amount.toLocaleString("id-ID");

  // Calculate internal-only values
  if (row.querySelector(".full-amount")) {
    // Full amount: unit price * qty
    const fullAmount = unitPrice * qty;
    row.querySelector(".full-amount").textContent = fullAmount.toLocaleString("id-ID");

    // Selling price - PPN: amount (IDR) / 1.11
    const sellingPriceNoPPN = Math.round(amount / 1.11);
    row.querySelector(".sell-no-ppn").textContent = sellingPriceNoPPN.toLocaleString("id-ID");

    // Total cost: unit cost * qty
    const totalCost = unitCost * qty;
    row.querySelector(".total-cost").textContent = totalCost.toLocaleString("id-ID");

    // Abs. margin: (selling price - ppn) - total cost
    const absMargin = sellingPriceNoPPN - totalCost;
    row.querySelector(".abs-margin").textContent = absMargin.toLocaleString("id-ID");

    // Margin percentage: (abs. margin / (selling price - ppn)) * 100
    let marginPercent = 0;
    if (sellingPriceNoPPN > 0) {
      marginPercent = (absMargin / sellingPriceNoPPN) * 100;
    }
    row.querySelector(".margin-percent").textContent = marginPercent.toFixed(1) + "%";

    // Update totals
    updateTotals();
  }
}

// Update totals for the internal-only table
function updateTotals() {
  let totalFullAmount = 0;
  let totalSellingPriceNoPPN = 0;
  let totalCost = 0;
  let totalAbsMargin = 0;

  document.querySelectorAll("#quote-items tr").forEach(row => {
    if (row.querySelector(".full-amount")) {
      totalFullAmount += parseCurrency(row.querySelector(".full-amount").textContent);
      totalSellingPriceNoPPN += parseCurrency(row.querySelector(".sell-no-ppn").textContent);
      totalCost += parseCurrency(row.querySelector(".total-cost").textContent);
      totalAbsMargin += parseCurrency(row.querySelector(".abs-margin").textContent);
    }
  });

  // Update total cells
  if (document.querySelector(".full-amount-total")) {
    document.querySelector(".full-amount-total").textContent = totalFullAmount.toLocaleString("id-ID");
    document.querySelector(".sell-no-ppn-total").textContent = totalSellingPriceNoPPN.toLocaleString("id-ID");
    document.querySelector(".total-cost-total").textContent = totalCost.toLocaleString("id-ID");
    document.querySelector(".abs-margin-total").textContent = totalAbsMargin.toLocaleString("id-ID");

    // Calculate total margin percentage
    let totalMarginPercent = 0;
    if (totalSellingPriceNoPPN > 0) {
      totalMarginPercent = (totalAbsMargin / totalSellingPriceNoPPN) * 100;
    }
    document.querySelector(".margin-percent-total").textContent = totalMarginPercent.toFixed(1) + "%";
  }
}

// Helper function to parse currency strings
function parseCurrency(currencyStr) {
  if (!currencyStr) return 0;
  return parseFloat(currencyStr.replace(/\./g, '').replace(/,/g, '.').replace(/[^\d.-]/g, '')) || 0;
}
