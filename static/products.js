function toggleCategory(id) {
  const el = document.getElementById(id);
  el.style.display = el.style.display === 'block' ? 'none' : 'block';
}
const pillowRow = document.querySelector(`tr[data-item-name="${itemName}"]`);
const showroomCell = pillowRow?.querySelector(".showroom-qty");

//stock history
async function loadStockHistory(category, size, firmness, location) {
    console.log("Loading stock history for:", category, size, firmness, location);

    const response = await fetch(`/stock_history?category=${category}&size=${size}&firmness=${firmness}&location=${location}`);
    const data = await response.json();
    console.log("Stock history data:", data);

    const detailBox = document.getElementById("popup-details");
    detailBox.innerHTML = "";

    if (data.length === 0) {
      detailBox.innerHTML = "<p>No history available.</p>";
    } else {
      data.forEach(item => {
        const entry = document.createElement("p");
        entry.textContent = `${item.qty}pc - ${item.type} - ${item.notes}`;
        detailBox.appendChild(entry);
      });
}

document.getElementById("stock-popup").style.display = "block";
}

function closePopup() {
document.getElementById("stock-popup").style.display = "none";
}

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll(".warehouse-qty.clickable").forEach(td => {
    td.addEventListener("click", () => {
      const category = td.dataset.category;
      const subcategory = td.dataset.subcategory;
      const size = td.dataset.size;
      const firmness = td.dataset.firmness;
      const location = td.dataset.location;
      loadStockHistory(category, size, firmness, location);
    });
  });
});


