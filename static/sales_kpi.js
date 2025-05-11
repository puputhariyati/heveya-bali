const yearlyCtx = document.getElementById('yearlyChart').getContext('2d');
const quarterlyCtx = document.getElementById('quarterlyChart').getContext('2d');
const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');

const yearlyChart = new Chart(yearlyCtx, {
    type: 'bar',
    data: {
        labels: ['Target', 'Actual'],
        datasets: [{
            label: 'Yearly Sales (Rp)',
            data: [28000000000, 6564744731],
            backgroundColor: ['#4caf50', '#2196f3']
        }]
    },
    options: { responsive: true, plugins: { legend: { display: false } } }
});

const quarterlyChart = new Chart(quarterlyCtx, {
    type: 'bar',
    data: {
        labels: ['Q1', 'Q2', 'Q3', 'Q4'],
        datasets: [
            {
                label: 'Target',
                data: [5880000000, 6160000000, 7280000000, 8680000000],
                backgroundColor: '#ccc'
            },
            {
                label: 'Actual',
                data: [4432484593, 2132260138, 0, 0],
                backgroundColor: '#03a9f4'
            }
        ]
    },
    options: { responsive: true }
});

const monthlyChart = new Chart(monthlyCtx, {
    type: 'bar',
    data: {
        labels: ['April', 'May', 'June'],
        datasets: [
            {
                label: 'Target',
                data: [1745333333, 2258666667, 2156000000],
                backgroundColor: '#bbb'
            },
            {
                label: 'Actual',
                data: [1825524138, 306736000, 0],
                backgroundColor: '#ff9800'
            }
        ]
    },
    options: { responsive: true }
});

document.getElementById('yearSelect').addEventListener('change', function() {
    const selectedYear = this.value;
    alert('Filter by year: ' + selectedYear);
    // TODO: Update data dynamically from server or dataset based on selectedYear
});
