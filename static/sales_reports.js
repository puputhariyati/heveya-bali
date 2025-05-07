let chart;
let processedData = []; // ✅ Correct, it's an array of raw products
let categoryTotals = {};

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

            processedData = products; // save globally

            const colorMap = {};
            products.forEach(p => {
                const name = p.product.product_name;
                const qty = parseFloat(p.product.quantity) || 0;
                const category = getCategory(name);

                categoryTotals[category] = (categoryTotals[category] || 0) + qty;

                if (!colorMap[category]) {
                    colorMap[category] = `hsl(${Math.random() * 360}, 70%, 70%)`;
                }
            });

            const labels = Object.keys(categoryTotals);
            const qty = Object.values(categoryTotals);
            const colors = labels.map(l => colorMap[l]);

            if (chart) chart.destroy();

            const ctx = document.getElementById('salesChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: qty,
                        backgroundColor: colors
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        datalabels: {
                            color: '#fff',
                            font: {
                                weight: 'bold'
                            },
                            formatter: (value, context) => {
                                const total = context.chart.data.datasets[0].data.reduce((sum, val) => sum + val, 0);
                                const percent = (value / total * 100).toFixed(1);
                                return `${percent}%`;
                            }
                        },
                        legend: {
                            position: 'bottom'
                        }
                    },
                    onClick: function (event, elements) {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const category = labels[index];
                            console.log("Clicked category:", category);
                            showCategoryDetails(category);
                        }
                    }
                },
                plugins: [ChartDataLabels]
            });

            // Show total breakdown with percentages for the main chart
            const totalQty = qty.reduce((sum, val) => sum + val, 0);
            let html = `<h3>Total by Category</h3><ul>`;
            labels.forEach((category, index) => {
                const q = qty[index];
                const percent = ((q / totalQty) * 100).toFixed(1);
                html += `<div style="display: grid; grid-template-columns: 2fr 1fr 0.7fr; gap: 12px; padding: 4px 0;">
                    <div>${category}</div><div>${q}</div><div>${percent}%</div>
                 </div>`;
            });
            html += `</ul>`;
            document.getElementById('categoryInfo').innerHTML = html;

            document.getElementById("downloadExcel").href = `/api/sales_by_products_excel?start_date=${start}&end_date=${end}`;
        })
        .catch(error => {
            console.error("Error fetching report:", error);
            alert("Failed to fetch data. Check console for details.");
        });
}

function getCategory(name) {
    name = name.toLowerCase();

    const isValidMattress = [
        "mattress",
        "hospitality mattress",
        "cot mattress",
        "topper"
    ].some(keyword => name.includes(keyword));
    if (isValidMattress) {
        if (name.includes("protector")) return "others";
        return "mattress";
    }

    const isValidPillow = [
        "latex pillow", "latex medium pillow",
        "latex bolster", "toddler pillow",
        "toddler flat pillow", "toddler contour pillow",
        "travel pillow - half heveya 2", "latex spa pillow",
        "latex travel mini bolster", "heveya pregnancy pillow"
    ].some(keyword => name.includes(keyword));
    if (isValidPillow) {
        if (name.includes("bamboo")) return "others"; // Exclude bamboo-labeled pillows as 'others'
        return "pillow";
    }

    const isValidSheets = [
        "bamboo duvet", "bamboo fitted", "bamboo flat",
        "linen duvet", "linen fitted", "linen flat",
        "bamboo cotton"
    ].some(keyword => name.includes(keyword));
    if (isValidSheets) {
        if (["bag", "box"].some(ex => name.includes(ex))) return "others"; // Exclude packaging
        return "sheets";
    }

    if (name.includes("inner duvet")) return "organic duvet";


    if (["towel", "bath mat", "bath robe", "bath sheet"].some(keyword => name.includes(keyword))) {
        return "towel";
    }

    if (name.includes("frame")) return "frame";

    return "others";
}

function groupByCategory(products) {
    const grouped = {};
    products.forEach(p => {
        if (!grouped[p.category]) {
            grouped[p.category] = [];
        }
        grouped[p.category].push(p);
    });
    return grouped;
}

function renderChart(data, filterCategory = 'all') {
    if (chart) chart.destroy();

    let labels = [];
    let qty = [];
    let colors = [];
    let categoryLookup = [];

    Object.entries(data).forEach(([category, items]) => {
        if (filterCategory === 'all' || category.toLowerCase() === filterCategory.toLowerCase()) {
            const total = items.reduce((sum, item) => sum + item.qty, 0);
            labels.push(category); // category, not item name
            qty.push(total);
            colors.push(items[0].color); // just use the first item color
            categoryLookup.push(category);
        }
    });

    const ctx = document.getElementById("salesChart").getContext("2d");
    chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: qty,
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true,
            plugins: {
                datalabels: {
                    color: '#fff',
                    font: {
                        weight: 'bold'
                    },
                    formatter: (value, context) => {
                        const total = context.chart.data.datasets[0].data.reduce((sum, val) => sum + val, 0);
                        const percent = (value / total * 100).toFixed(1);
                        return `${percent}%`;
                    }
                },
                legend: {
                    position: 'bottom'
                }
            },
            onClick: function (event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const category = labels[index];
                    console.log("Clicked category:", category);
                    showCategoryDetails(category);
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}

// After chart is rendered
const infoDiv = document.getElementById('categoryInfo');
let html = `<h3>Total by Category</h3><ul>`;
Object.entries(categoryTotals)
    .sort((a, b) => b[1] - a[1]) // optional: sort descending
    .forEach(([cat, qty]) => {
        html += `<li>${cat}: ${qty}</li>`;
    });
html += `</ul>`;
infoDiv.innerHTML = html;


function showCategoryDetails(category) {
    if (!Array.isArray(processedData)) {
        console.error("processedData is not ready or not an array", processedData);
        return;
    }

    const lowerCategory = category.trim().toLowerCase();

    // Filter items by normalized category
    const categoryItems = processedData.filter(p => {
        const itemCategory = getCategory(p.product.product_name);
        return itemCategory && itemCategory.trim().toLowerCase() === lowerCategory;
    });

    if (categoryItems.length === 0) {
        console.warn(`No items found for category "${category}"`);
        document.getElementById('categoryInfo').innerHTML = `<h3>No products found for "${category}"</h3>`;
        return;
    }

    const labels = categoryItems.map(p => p.product.product_name);
    const data = categoryItems.map(p => parseFloat(p.product.quantity) || 0);
    const total = data.reduce((sum, q) => sum + q, 0);
    const colors = labels.map(() => `hsl(${Math.random() * 360}, 70%, 70%)`);

    if (chart) chart.destroy();

    const ctx = document.getElementById("salesChart").getContext("2d");
    chart = new Chart(ctx, {
        type: "pie",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true,
            plugins: {
                datalabels: {
                    color: "#fff",
                    font: {
                        weight: "bold"
                    },
                    formatter: (value, context) => {
                        const percent = (value / total * 100).toFixed(1);
                        return `${percent}%`;
                    }
                },
                legend: {
                    position: "bottom"
                }
            },
            onClick: function (event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const productName = labels[index];
                    const quantity = data[index];
                    alert(`${productName}\nQuantity Sold: ${quantity}`);
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    // Render product list in info panel with percentages
    const infoDiv = document.getElementById('categoryInfo');
    let html = `<h3>Total ${category}: ${total}</h3><ul>`;
    labels.forEach((label, i) => {
        const percent = ((data[i] / total) * 100).toFixed(1);
        html += `<li style="display: grid; grid-template-columns: gap: 20px;">
            ${label}: ${data[i]} (${percent}%)</li>`;
    });
    html += `</ul>`;
    infoDiv.innerHTML = html;
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


window.onload = function () {
    const today = new Date();

    // Force start date to 1 January 2025
    const startOfYear = new Date(2025, 0, 1); // Month is 0-indexed: 0 = Jan

    // Format YYYY-MM-DD without timezone issues
    const format = (date) => {
        const yyyy = date.getFullYear();
        const mm = String(date.getMonth() + 1).padStart(2, '0');
        const dd = String(date.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    };

    document.getElementById('start_date').value = format(startOfYear);
    document.getElementById('end_date').value = format(today);

    // ... the rest of your code unchanged ...
    document.getElementById('categoryFilter').addEventListener('change', () => {
        const selectedCategory = document.getElementById('categoryFilter').value;

        if (!Array.isArray(processedData)) {
            console.error("processedData is not an array!", processedData);
            return;
        }

        const grouped = groupByCategory(processedData);
        renderChart(grouped, selectedCategory);

        const infoDiv = document.getElementById('categoryInfo');
        if (selectedCategory !== 'all') {
            const lowerCategory = selectedCategory.toLowerCase();
            const items = grouped[lowerCategory] || [];
            const total = items.reduce((sum, item) => sum + item.qty, 0);
            let listHTML = `<h3>Total ${selectedCategory}: ${total}</h3>`;
            const categoryItems = processedData.filter(p => {
                return getCategory(p.product.product_name)?.toLowerCase() === lowerCategory;
            });
            listHTML += `<ul>${categoryItems.map(p => `<li>${p.product.product_name} - ${p.product.quantity}</li>`).join('')}</ul>`;
            infoDiv.innerHTML = listHTML;
        } else {
            infoDiv.innerHTML = '';
        }
    });

    fetchReport();
};

