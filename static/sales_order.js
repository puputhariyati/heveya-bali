document.addEventListener("DOMContentLoaded", function () {
fetch("/static/data/sales_orders_May2025.json")
  .then(response => response.json())
  .then(data => {
    const tbody = document.getElementById("sales-order-body");

    data.forEach(order => {
      const date = order.transaction_date || '';
      const orderNo = order.transaction_no || '';
      const customer = order.person?.display_name || '';
      const balanceDue = order.outstanding_amount_currency_format || '-';
      const total = order.original_amount_currency_format || '-';

      const row = document.createElement("tr");
      row.innerHTML = `
        <td><input type="checkbox" class="row-check"></td>
        <td>${date}</td>
        <td><a href="/sales_order/${orderNo}">${orderNo}</a></td>
        <td>${customer}</td>
        <td>${balanceDue}</td>
        <td>${total}</td>
        <td>
            <select name="status">
            <option value="prepared">Prepared</option>
            <option value="partially sent">Partially Sent</option>
            <option value="done">Done</option>
            </select>
        </td>
        <td><input type="date" name="ETD"></td>
      `;
      tbody.appendChild(row);
    });
  })
  .catch(error => {
    console.error("Error loading sales order data:", error);
  });
});

