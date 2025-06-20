function updateRemain(input) {
    const row = input.closest("tr");
    const qty = parseInt(row.querySelector(".qty").value) || 0;
    const delivered = parseInt(input.value) || 0;
    const remainInput = row.querySelector(".remain_qty");
    remainInput.value = Math.max(qty - delivered, 0);
}
