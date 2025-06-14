document.addEventListener('DOMContentLoaded', () => {
    const loadBtn = document.getElementById('load-btn');
    const downloadBtn = document.getElementById('download-btn');
    const tableBody = document.getElementById('data-table').querySelector('tbody');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Load button click handler
    loadBtn.addEventListener('click', async () => {
        const stationSelect = document.getElementById('station-select');
        const timeStepSelect = document.getElementById('time-step');
        const stationId = stationSelect.value || "1"; // Default to Пермь - Гайва
        const timeStep = timeStepSelect.value;

        // Show loading spinner
        loadingSpinner.style.display = 'block';
        tableBody.innerHTML = ''; // Clear table

        try {
            const response = await fetch(`/api/weather/?station_id=${stationId}&time_step=${timeStep}`);
            if (!response.ok) throw new Error('Failed to fetch data');
            const data = await response.json();

            if (data.length === 0) {
                alert('Нет данных для выбранной комбинации');
                return;
            }

            // Update table
            data.forEach(item => {
                const row = document.createElement('tr');
                const dateKey = timeStep === '1w' ? 'date_range' : 'date';
                row.innerHTML = `
                    <td>${item[dateKey]}</td>
                    <td>${item.temperature.toFixed(1)}</td>
                    <td>${item.humidity.toFixed(1)}</td>
                    <td>${item.precipitation.toFixed(1)}</td>
                    <td>${item.wind_speed.toFixed(1)}</td>
                    <td>${item.utci.toFixed(1)}</td>
                    <td>${item.wbgt.toFixed(1)}</td>
                    <td>${item.cwsi.toFixed(2)}</td>
                    <td>${item.heat_index.toFixed(1)}</td>
                `;
                tableBody.appendChild(row);
            });
        } catch (error) {
            console.error('Error loading data:', error);
            alert('Ошибка загрузки данных. Подробности в консоли.');
        } finally {
            loadingSpinner.style.display = 'none';
        }
    });

    // Download button click handler
    downloadBtn.addEventListener('click', () => {
        const formatSelect = document.getElementById('format-select');
        const format = formatSelect.value;
        const stationSelect = document.getElementById('station-select');
        const stationName = stationSelect.options[stationSelect.selectedIndex].text;
        const timeStep = document.getElementById('time-step').value;
        const timeStepText = timeStep === '1w' ? 'Неделя' : timeStep === '1d' ? 'День' : 'Месяц';
        const filename = `Weather_${stationName}_${timeStepText}.${format}`;

        // Get table data
        const headers = Array.from(document.querySelectorAll('#data-table th')).map(th => th.textContent);
        const rows = Array.from(tableBody.querySelectorAll('tr')).map(row =>
            Array.from(row.querySelectorAll('td')).map(td => td.textContent)
        );

        if (rows.length === 0) {
            alert('Нет данных для скачивания');
            return;
        }

        if (format === 'csv') {
            // Generate CSV
            const csvContent = [
                headers.join(','),
                ...rows.map(row => row.join(','))
            ].join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
        } else if (format === 'xlsx') {
            // Generate XLSX using SheetJS
            const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'WeatherData');
            XLSX.write(wb, filename, { bookType: 'xlsx', type: 'blob' });
        }
    });
});