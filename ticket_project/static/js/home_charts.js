// home_charts.js - FIXED VERSION with initial server data

// ========== GLOBAL STATE ==========
const charts = {};

// ========== SETUP FILTERS ==========
function setupFilters() {
    const form = document.getElementById('filterForm');
    const resetBtn = document.getElementById('resetBtn');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        loadDashboardData();
    });
    
    resetBtn.addEventListener('click', function() {
        form.reset();
        document.getElementById('selectAllAnalysts').textContent = 'Select All';
        document.getElementById('selectAllStates').textContent = 'Select All';
        updateFilterSummary();
        // Reload initial server data
        location.reload();
    });
}

// ========== SELECT ALL BUTTONS ==========
function setupSelectAllButtons() {
    const analystSelect = document.getElementById('analysts');
    const stateSelect = document.getElementById('states');
    const selectAllAnalysts = document.getElementById('selectAllAnalysts');
    const selectAllStates = document.getElementById('selectAllStates');
    
    selectAllAnalysts.addEventListener('click', function() {
        const allSelected = Array.from(analystSelect.options).every(opt => opt.selected);
        Array.from(analystSelect.options).forEach(opt => opt.selected = !allSelected);
        this.textContent = allSelected ? 'Select All' : 'Deselect All';
    });
    
    selectAllStates.addEventListener('click', function() {
        const allSelected = Array.from(stateSelect.options).every(opt => opt.selected);
        Array.from(stateSelect.options).forEach(opt => opt.selected = !allSelected);
        this.textContent = allSelected ? 'Select All' : 'Deselect All';
    });
}

// ========== FILTER SUMMARY ==========
function updateFilterSummary() {
    const analystSelect = document.getElementById('analysts');
    const stateSelect = document.getElementById('states');
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    
    const selectedAnalysts = Array.from(analystSelect.selectedOptions);
    const selectedStates = Array.from(stateSelect.selectedOptions);
    
    let summary = [];
    if (selectedAnalysts.length > 0) summary.push(`${selectedAnalysts.length} analyst(s)`);
    if (selectedStates.length > 0) summary.push(`${selectedStates.length} state(s)`);
    if (startDate || endDate) summary.push('date range');
    
    const summaryEl = document.getElementById('filterSummary');
    if (summary.length > 0) {
        summaryEl.innerHTML = `<i class="bi bi-funnel-fill"></i> Filtering by: ${summary.join(', ')}`;
    } else {
        summaryEl.textContent = '';
    }
}

// ========== LOAD DASHBOARD DATA (API) ==========
async function loadDashboardData() {
    const form = document.getElementById('filterForm');
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    if (formData.get('start_date')) params.append('start_date', formData.get('start_date'));
    if (formData.get('end_date')) params.append('end_date', formData.get('end_date'));
    
    const analystSelect = document.getElementById('analysts');
    const selectedAnalysts = Array.from(analystSelect.selectedOptions).map(opt => opt.value);
    selectedAnalysts.forEach(analyst => params.append('analysts', analyst));
    
    const stateSelect = document.getElementById('states');
    const selectedStates = Array.from(stateSelect.selectedOptions).map(opt => opt.value);
    selectedStates.forEach(state => params.append('states', state));
    
    updateFilterSummary();
    
    try {
        const response = await fetch(`/api/home-dashboard/?${params.toString()}`);
        if (!response.ok) throw new Error('Network error');
        
        const data = await response.json();
        
        // Update KPIs
        document.getElementById('kpi-total').textContent = data.kpis.total;
        document.getElementById('kpi-avg').textContent = data.kpis.avg_time + 'h';
        document.getElementById('kpi-total-time').textContent = data.kpis.total_time + 'h';
        document.getElementById('kpi-open').textContent = data.kpis.open;
        
        // Update charts
        updateCharts(data.charts);
        
        console.log('✅ Dashboard updated with filtered data');
    } catch (error) {
        console.error('❌ Error loading dashboard:', error);
        alert('Error loading dashboard data');
    }
}

// ========== INITIALIZE CHARTS WITH SERVER DATA ==========
function initializeCharts() {
    // Get initial data from server (passed via template)
    const initial = window.initialChartData || {};
    
    // Chart 1: Doughnut
    charts.chart1 = new Chart(document.getElementById('chart1'), {
        type: 'doughnut',
        data: {
            labels: initial.chart1?.labels || [],
            datasets: [{
                data: initial.chart1?.data || [],
                backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40', '#c9cbcf', '#2ecc71']
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }
    });
    
    // Chart 2: Bar
    charts.chart2 = new Chart(document.getElementById('chart2'), {
        type: 'bar',
        data: {
            labels: initial.chart2?.labels || [],
            datasets: [{
                label: 'Tickets',
                data: initial.chart2?.data || [],
                backgroundColor: 'rgba(54, 162, 235, 0.8)'
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
    
    // Chart 3: Bar
    charts.chart3 = new Chart(document.getElementById('chart3'), {
        type: 'bar',
        data: {
            labels: initial.chart3?.labels || [],
            datasets: [{
                label: 'Hours',
                data: initial.chart3?.data || [],
                backgroundColor: 'rgba(255, 99, 132, 0.8)'
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
    
    // Chart 4: Bar
    charts.chart4 = new Chart(document.getElementById('chart4'), {
        type: 'bar',
        data: {
            labels: initial.chart4?.labels || [],
            datasets: [{
                label: 'Tickets',
                data: initial.chart4?.data || [],
                backgroundColor: 'rgba(153, 102, 255, 0.8)'
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
    
    // Chart 5: Horizontal Bar
    charts.chart5 = new Chart(document.getElementById('chart5'), {
        type: 'bar',
        data: {
            labels: initial.chart5?.labels || [],
            datasets: [{
                label: 'Tickets',
                data: initial.chart5?.data || [],
                backgroundColor: 'rgba(75, 192, 192, 0.8)'
            }]
        },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true } } }
    });
    
    // Chart 6: Bar
    charts.chart6 = new Chart(document.getElementById('chart6'), {
        type: 'bar',
        data: {
            labels: initial.chart6?.labels || [],
            datasets: [{
                label: 'Hours',
                data: initial.chart6?.data || [],
                backgroundColor: 'rgba(255, 206, 86, 0.8)'
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
    
    console.log('📊 Charts initialized with server data');
}

// ========== UPDATE CHARTS ==========
function updateCharts(chartsData) {
    charts.chart1.data.labels = chartsData.chart1.labels;
    charts.chart1.data.datasets[0].data = chartsData.chart1.data;
    charts.chart1.update();
    
    charts.chart2.data.labels = chartsData.chart2.labels;
    charts.chart2.data.datasets[0].data = chartsData.chart2.data;
    charts.chart2.update();
    
    charts.chart3.data.labels = chartsData.chart3.labels;
    charts.chart3.data.datasets[0].data = chartsData.chart3.data;
    charts.chart3.update();
    
    charts.chart4.data.labels = chartsData.chart4.labels;
    charts.chart4.data.datasets[0].data = chartsData.chart4.data;
    charts.chart4.update();
    
    charts.chart5.data.labels = chartsData.chart5.labels;
    charts.chart5.data.datasets[0].data = chartsData.chart5.data;
    charts.chart5.update();
    
    charts.chart6.data.labels = chartsData.chart6.labels;
    charts.chart6.data.datasets[0].data = chartsData.chart6.data;
    charts.chart6.update();
}

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Dashboard Charts initialized');
    
    // Initialize charts with server-side data
    initializeCharts();
    
    // Setup filter functionality
    setupFilters();
    setupSelectAllButtons();
    
    console.log('✅ All systems ready - using initial server data');
});