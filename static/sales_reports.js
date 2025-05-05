let chart;
let processedData = {}; // make global


function getCategory(productName) {
    const name = productName.toLowerCase();
    if (name.includes("mattress")) return "Mattress";
    if (name.includes("pillow")) return "Pillow";
    if (name.includes("sheet")) return "Sheet";
    if (name.includes("duvet")) return "Organic Duvet";
    if (name.includes("towel")) return "Towel";
    if (name.includes("frame")) return "Frame";
    return "Others";
}

function groupByCategory(products) {
    const categoryGroups = {};

    products.forEach((p, i) => {
        const name = p.product.product_name;
        const qty = parseFloat(p.product.quantity);
        const color = `hsl(${Math.random() * 360}, 70%, 70%)`;
        const category = getCategory(name);

        if (!categoryGroups[category]) categoryGroups[category] = [];

        categoryGroups[category].push({
            name,
            qty,
            color
        });
    });

    return categoryGroups;
}

function renderLegend(data) {
    const container = document.getElementById("legendContainer");
    container.innerHTML = "";

    Object.entries(data).forEach(([category, items]) => {
        const group = document.createElement("div");
        group.innerHTML = `<strong>${category}</strong>`;

        items.forEach(item => {
            const div = document.createElement("div");
            div.innerHTML = `<span style="display:inline-block;width:12px;height:12px;background:${item.color};margin-right:5px;"></span>${item.name} (${item.qty})`;
            group.appendChild(div);
        });

        container.appendChild(group);
    });
}

function renderChart(data, filterCategory = 'all') {
    if (chart) chart.destroy();

    let labels = [];
    let qty = [];
    let colors = [];

    Object.entries(data).forEach(([category, items]) => {
        if (filterCategory === 'all' || category.toLowerCase() === filterCategory.toLowerCase()) {
            items.forEach(item => {
                labels.push(item.name);
                qty.push(item.qty);
                colors.push(item.color);
            });
        }
    });

    const ctx = document.getElementById("salesChart").getContext("2d");
    chart = new Chart(ctx, {
        type: "pie",
        data: {
            labels: labels,
            datasets: [{
                data: qty,
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true
        }
    });
}

function fetchReport() {
    const start = document.getElementById('start_date').value;
    const end = document.getElementById('end_date').value;

    fetch(`/api/sales_by_products?start_date=${start}&end_date=${end}`)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            const products = data.sales_by_products.reports.products;

            if (!products || products.length === 0) {
                alert("No data found for the selected date range.");
                return;
            }

            // Step 1: Categorize and sum
            const categoryTotals = {};
            products.forEach(p => {
                const name = p.product.product_name;
                const qty = parseFloat(p.product.quantity) || 0;
                const category = getCategory(name);
                categoryTotals[category] = (categoryTotals[category] || 0) + qty;
            });

            const labels = Object.keys(categoryTotals);
            const qty = Object.values(categoryTotals);

            if (chart) chart.destroy();

            const ctx = document.getElementById('salesChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: qty,
                        backgroundColor: labels.map(() => `hsl(${Math.random() * 360}, 70%, 70%)`)
                    }]
                },
                options: {
                    responsive: true
                }
            });

            // Set Excel download link
            document.getElementById("downloadExcel").href = `/api/sales_by_products_excel?start_date=${start}&end_date=${end}`;

            // Save the raw data for filtering later
            window.processedData = products;
        })
        .catch(error => {
            console.error("Error fetching report:", error);
            alert("Failed to fetch data. Check console for details.");
        });
}


window.onload = function () {
    const today = new Date();
    const lastYear = new Date();
    lastYear.setFullYear(today.getFullYear() - 1);

    const format = (date) => date.toISOString().split('T')[0];

    document.getElementById('start_date').value = format(lastYear);
    document.getElementById('end_date').value = format(today);

    // Bind event listener for filter
    document.getElementById('categoryFilter').addEventListener('change', () => {
        const selectedCategory = document.getElementById('categoryFilter').value;
        renderChart(processedData, selectedCategory);
    });

    // Auto fetch
    document.getElementById('generate_report').click();
};

