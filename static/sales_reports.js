let chart;
let processedData = []; // ✅ Correct, it's an array of raw products

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

            const categoryTotals = {};
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
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const category = chart.data.labels[index];
                            console.log("Clicked:", category);
                            showCategoryDetails(category);
                        }
                    }
                }
            });

            document.getElementById("downloadExcel").href = `/api/sales_by_products_excel?start_date=${start}&end_date=${end}`;
        })
        .catch(error => {
            console.error("Error fetching report:", error);
            alert("Failed to fetch data. Check console for details.");
        });
}

function getCategory(name) {
    name = name.toLowerCase();
    if (name.includes("mattress") && !name.includes("protector")) return "mattress";
    if (name.includes("bamboo")) return "others"; // ⛔ Exclude bamboo items from pillow category
    const isValidPillow = [
        "latex pillow", "latex medium pillow",
        "latex bolster",
        "toddler pillow",
        "toddler flat pillow",
        "toddler contour pillow",
        "travel pillow - half heveya 2",
        "latex spa pillow",
        "latex travel mini bolster",
        "heveya pregnancy pillow"
    ].some(keyword => name.includes(keyword));
    if (isValidPillow) return "pillow";
    if (name.includes("sheet")) return "sheet";
    if (name.includes("duvet")) return "organic duvet";
    if (name.includes("towel")) return "towel";
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
        type: "pie",
        data: {
            labels: labels,
            datasets: [{
                data: qty,
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true,
            onClick: function (event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const category = labels[index];

                    console.log("Clicked category:", category);
                    showCategoryDetails(category);
                }
            }
        }
    });
}

function getMattressSubCategory(name) {
    name = name.toLowerCase();
    if (name.includes("latex mattress")) return "Latex Mattress";
    if (name.includes("cot mattress")) return "Cot Mattress";
    if (name.includes("hospitality mattress")) return "Hospitality Mattress";
    return null; // ignore all other mattress types
}

function showCategoryDetails(category) {
    if (!Array.isArray(processedData)) {
        console.error("processedData is not ready or not an array", processedData);
        return;
    }

    const lowerCategory = category.toLowerCase();

    let labels = [];
    let data = [];
    let items = [];

    if (lowerCategory === "mattress") {
        // Show breakdown for only specific mattress types
        const mattressItems = processedData.filter(p => getMattressSubCategory(p.product.product_name) !== null);


        const subCategoryTotals = {};
        const subCategoryItems = {};

        mattressItems.forEach(p => {
            const sub = getMattressSubCategory(p.product.product_name);
            if (sub) {
                const qty = parseFloat(p.product.quantity) || 0;
                subCategoryTotals[sub] = (subCategoryTotals[sub] || 0) + qty;

                if (!subCategoryItems[sub]) subCategoryItems[sub] = [];
                subCategoryItems[sub].push(p);
            }
        });

        labels = Object.keys(subCategoryTotals);
        data = Object.values(subCategoryTotals);
        items = subCategoryItems;
    } else {
        // Default behavior
        const categoryItems = processedData.filter(p => getCategory(p.product.product_name) === lowerCategory);
        labels = categoryItems.map(p => p.product.product_name);
        data = categoryItems.map(p => parseFloat(p.product.quantity) || 0);
        items = categoryItems;
    }

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
            onClick: function (event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const productName = labels[index];
                    const quantity = data[index];
                    alert(`${productName}\nQuantity Sold: ${quantity}`);
                }
            }
        }
    });

    // Render product list in info panel
    const total = data.reduce((sum, q) => sum + q, 0);
    const infoDiv = document.getElementById('categoryInfo');
    let html = `<h3>Total ${category}: ${total}</h3><ul>`;

    if (lowerCategory === "mattress") {
        // Show grouped sub-category items
        for (const sub of labels) {
            html += `<li><strong>${sub}</strong><ul>`;
            items[sub].forEach(p => {
                html += `<li>${p.product.product_name}: ${p.product.quantity}</li>`;
            });
            html += `</ul></li>`;
        }
    } else {
        // Default list
        items.forEach(p => {
            html += `<li>${p.product.product_name}: ${p.product.quantity}</li>`;
        });
    }

    html += "</ul>";
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
    const lastYear = new Date();
    lastYear.setFullYear(today.getFullYear() - 1);

    const format = (date) => date.toISOString().split('T')[0];
    document.getElementById('start_date').value = format(lastYear);
    document.getElementById('end_date').value = format(today);

    // Bind event listener
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
            const items = grouped[selectedCategory] || [];
            const total = items.reduce((sum, item) => sum + item.qty, 0);
            let listHTML = `<h3>Total ${selectedCategory}: ${total}</h3>`;

            if (selectedCategory === 'mattress') {
                // Show only subcategory summary for mattress
                const subTotals = {
                    'Latex Mattress': 0,
                    'Cot Mattress': 0,
                    'Hospitality Mattress': 0
                };

                items.forEach(item => {
                    const sub = getMattressSubCategory(item.name);
                    if (sub) subTotals[sub] += item.qty;
                });

                listHTML += `<ul>`;
                for (const [sub, qty] of Object.entries(subTotals)) {
                    listHTML += `<li>${sub}: ${qty}</li>`;
                }
                listHTML += `</ul>`;
            } else {
                // Default: show full list
                listHTML += `<ul>`;
                items.forEach(item => {
                    listHTML += `<li>${item.name} : ${item.qty}</li>`;
                });
                listHTML += `</ul>`;
            }

            infoDiv.innerHTML = listHTML;
        } else {
            infoDiv.innerHTML = '';
        }
    });

    // ✅ Fetch data immediately instead of clicking a button
    fetchReport();
};






