document.addEventListener("DOMContentLoaded", function () {
  const transactionNo = getTransactionNoFromURL();

  fetch("/static/data/sales_orders_May2025.json")
    .then(response => response.json())
    .then(data => {
      const tbody = document.getElementById("sales-order-detail-body");

      // Find the order matching the transactionNo
      const matchedOrder = data.find(order => order.transaction_no == transactionNo);

      if (!matchedOrder) {
        tbody.innerHTML = `<tr><td colspan="13">Sales order not found: ${transactionNo}</td></tr>`;
        return;
      }

      const lines = matchedOrder.transaction_lines_attributes || [];
      lines.forEach((line, i) => {
        const item = line.product?.name || '';
        const qty = line.quantity || '';
        const unit = line.unit?.name || '-';

        const row = document.createElement("tr");
        row.innerHTML = `
          <td><input type="checkbox" class="row-check"></td>
          <td>${i + 1}</td>
          <td>${item}</td>
          <td><input type="text" class="desc" placeholder=""></td>
          <td><input type="number" class="qty" value="${qty}" readonly></td>
          <td>${unit}</td>
          <td><input type="number" class="delivered" name="delivered" min="0" value="0" oninput="updateRemain(this)"></td>
          <td><input type="number" class="remain_qty" name="remain_qty" value="${qty}" readonly></td>
          <td><input type="text" class="PO_no" placeholder=""></td>
          <td>
              <select name="warehouse_option">
                  <option value="showroom">Showroom</option>
                  <option value="warehouse">Warehouse</option>
              </select>
          </td>
          <td><input type="date" name="delivery_date"></td>
        `;
        tbody.appendChild(row);
      });
    })
    .catch(error => {
      console.error("Error loading sales order data:", error);
    });

  function getTransactionNoFromURL() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
  }
});

function updateRemain(input) {
    const row = input.closest("tr");
    const qty = parseInt(row.querySelector(".qty").value) || 0;
    const delivered = parseInt(input.value) || 0;
    const remainInput = row.querySelector(".remain_qty");
    remainInput.value = Math.max(qty - delivered, 0);
}