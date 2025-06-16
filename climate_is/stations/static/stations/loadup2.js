document.addEventListener('DOMContentLoaded', () => {
    const loadBtn = document.getElementById('load-btn');
    const downloadBtn = document.getElementById('download-btn');
    const tableBody = document.getElementById('data-table').querySelector('tbody');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Load button click handler
    loadBtn.addEventListener('click', async () => {
        const stationSelect = document.getElementById('station-select');
        const timeStepSelect = document.getElementById('time-step');
        const stationId = stationSelect.value || "day"; // по умолчанию Пермь
        const timeStep = timeStepSelect.value;
        const startDateInput = document.getElementById('start-date').value;
        const endDateInput = document.getElementById('end-date').value;

        // валидация "от" < "до"
        if (startDateInput && endDateInput && new Date(startDateInput) > new Date(endDateInput)) {
            alert('Дата начала не может быть позже даты окончания.');
            return;
        }
        
        loadingSpinner.style.display = 'block';
        tableBody.innerHTML = ''; // Clear table

        try {
            const response = await fetch(`/api/aggregate/?station_id=${stationId}&period=${timeStep}&start_date=${startDateInput}&end_date=${endDateInput}`);
            if (!response.ok) throw new Error('Failed to fetch data');
            const data = await response.json();

            if (data.length === 0) {
                alert('Нет данных для выбранной комбинации');
                return;
            }

            // Update table
            data.forEach(item => {
                const row = document.createElement('tr');
                if (timeStep === 'month') { // Месячный период
                    dateDisplay = item.date.split('-').slice(0, 2).join('-'); // Оставляем только год-месяц
                } else if (timeStep === 'week') {
                    dateDisplay = item.date_range; // Для недели используем диапазон
                } else {
                    dateDisplay = item.date; // Для дня полная дата
                }
                //const dateKey = timeStep === 'week' ? 'date_range' : 'date';
                row.innerHTML = `
                    <td>${dateDisplay}</td>
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
        const timeStepText = timeStep === 'week' ? 'Неделя' : timeStep === 'day' ? 'День' : 'Месяц';
        const filename = `Weather_${stationName}_${timeStepText}.${format}`;

        // Get table data
        //const headers = Array.from(document.querySelectorAll('#data-table th')).map(th => th.textContent);
        const headers = ['Date', 'TEMP', 'HUM', 'PREC', 'WIND_SPEED', 'UTCI', 'WBGT', 'CWSI']
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
                ...rows.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(','))
            ].join('\n');
            const bom = '\uFEFF'; // UTF-8 BOM
            const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
        } else if (format === 'xlsx') {
            // Generate XLSX using SheetJS
            var wb = XLSX.utils.table_to_book(document.getElementById("data-table"));
            XLSX.writeFile(wb, filename);
        }
    });
});