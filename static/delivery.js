function applyBulkDate() {
    const bulkDate = document.getElementById("bulk-delivery-date").value;
    if (!bulkDate) {
        alert("Please choose a date first.");
        return;
    }

    document.querySelectorAll("tr").forEach(row => {
        const checkbox = row.querySelector(".row-check");
        const dateInput = row.querySelector("input[name='delivery_date']");
        if (checkbox && checkbox.checked && dateInput) {
            dateInput.value = bulkDate;
        }
    });
}

function toggleAll(source) {
    const checkboxes = document.querySelectorAll(".row-check");
    checkboxes.forEach(cb => cb.checked = source.checked);
}

function updateRemain(input) {
    const row = input.closest("tr");
    const qty = parseInt(row.querySelector(".qty").value) || 0;
    const delivered = parseInt(input.value) || 0;
    const remainInput = row.querySelector(".remain_qty");
    remainInput.value = Math.max(qty - delivered, 0);
}

function showCalendarView() {
  document.getElementById('delivery-table').style.display = 'none';
  document.getElementById('delivery-calendar').style.display = 'block';
}
function showTableView() {
  document.getElementById('delivery-calendar').style.display = 'none';
  document.getElementById('delivery-table').style.display = 'block';
}
// Render Calendar
window.addEventListener('DOMContentLoaded', () => {
  const calendarEl = document.getElementById('delivery-calendar');
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    events: [
      { title: 'SO-1001: Mattress', date: '2025-06-21' },
      { title: 'SO-1002: Pillow', date: '2025-06-18' }
    ]
  });
  calendar.render();
});