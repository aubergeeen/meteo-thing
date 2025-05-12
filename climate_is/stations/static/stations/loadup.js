document.addEventListener('DOMContentLoaded', function() {
    const loadBtn = document.getElementById('load-btn');
    if (loadBtn) {
        loadBtn.addEventListener('click', loadStationStats);
    }
});

async function loadStationStats() {
    const stationSelect = document.getElementById('station-select');
    const timeStep = document.getElementById('time-step');
    const tableBody = document.querySelector('#data-table tbody');

    if (!stationSelect || !stationSelect.value) {
        alert('Please select a station');
        return;
    }
    try {
        // TODO? - REDO WITH DOM INST OF INNER HTML MAYBE???? 
        const response = await fetch(`/api/aggregate/?station=${stationSelect.value}&&step=${timeStep.value}`)
        const data = await response.json();
        if (data.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4">No data available for selected station.</td></tr>';
            return;
        }
        tableBody.innerHTML = '';
        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.date || '—'}</td>
                <td>${(item.avg_t != null) ? item.avg_t.toFixed(1) : '—'}</td>
                <td>${(item.avg_h != null) ? item.avg_h.toFixed(1) : '—'}</td>

            `;
            tableBody.appendChild(row);
        });
        console.log(data)
    } catch (error) {
        console.error('Error fetching data:', error);
        alert('Error loading data. Please try again.');
    }
}