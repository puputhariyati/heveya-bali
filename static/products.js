function toggleCategory(id) {
  const el = document.getElementById(id);
  el.style.display = el.style.display === 'block' ? 'none' : 'block';
}

const pillowRow = document.querySelector(`tr[data-item-name="${itemName}"]`);
const showroomCell = pillowRow?.querySelector(".showroom-qty");