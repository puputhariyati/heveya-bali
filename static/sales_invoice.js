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
  document.querySelectorAll('.internal-only').forEach(el => {
    el.style.display = (el.style.display === 'table-cell' || el.style.display === 'table-row') ? 'none' : (el.tagName === 'TR' ? 'table-row' : 'table-cell');
  });
}

window.onload = function () {
  const today = new Date();
  const oneMonthLater = new Date();
  oneMonthLater.setMonth(today.getMonth() + 1);

  const toDateInputValue = date =>
    date.toISOString().split("T")[0]; // yyyy-mm-dd

  document.getElementById("quote-date").value = toDateInputValue(today);
  document.getElementById("quote-expiry").value = toDateInputValue(oneMonthLater);
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
  const discountedPrice = unitPrice - (unitPrice * discount / 100);
  const amount = Math.round(discountedPrice * qty);
  row.querySelector(".amount-text").textContent = amount.toLocaleString("id-ID");
}

