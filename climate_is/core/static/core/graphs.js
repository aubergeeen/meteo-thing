document.addEventListener('DOMContentLoaded', () => {
    // Инициализация вкладок
    const tabs = document.querySelectorAll('.tab-button');
    const panes = document.querySelectorAll('.tab-pane');

    // Функция загрузки метеостанций
    const loadStations = async () => {
        try {
            const response = await fetch('/api/locate/?fields=station_id,name');
            if (!response.ok) {
                throw new Error(`Ошибка API: ${response.status}`);
            }
            const stations = await response.json();

            const stationSelects = document.querySelectorAll('[id^=station-select]');
            stationSelects.forEach(select => {
                while (select.options.length > 1) {
                    select.remove(1);
                }
                stations.forEach(station => {
                    const option = document.createElement('option');
                    option.value = station.station_id;
                    option.textContent = station.name;
                    select.appendChild(option);
                });
            });
        } catch (error) {
            console.error('Ошибка при загрузке метеостанций:', error);
        }
    };

    // Функция инициализации формы для активной вкладки
    const initializeForm = async (paneId) => {
        await loadStations();
        const form = document.querySelector(`#${paneId} form`);
        if (form) {
            form.reset();
        }
    };

    // Обработчик переключения вкладок
    tabs.forEach(tab => {
        tab.addEventListener('click', async () => {
            tabs.forEach(t => t.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const pane = document.getElementById(tab.dataset.tab);
            pane.classList.add('active');

            await initializeForm(tab.dataset.tab);
        });
    });

    // Инициализация при загрузке страницы
    initializeForm('statistics');

    // Функция построения графика
    const plotGraph = (data, layout, type = 'scatter') => {
        const config = {
            responsive: true,
            toImageButtonOptions: {
                format: 'png',
                filename: 'plot',
                height: 500,
                width: 800,
                scale: 1
            }
        };
        Plotly.newPlot('plotly-graph', data, layout, config);
    };

    // Обработчик формы временного ряда
    document.getElementById('statistics-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const params = new URLSearchParams();
        
        formData.forEach((value, key) => {
            if (form[key].type !== 'checkbox' || form[key].checked) {
                params.append(key, value);
            }
        });

        try {
            const response = await fetch(`/api/weather/timeseries/?${params}`);
            if (!response.ok) {
                throw new Error(`Ошибка API: ${response.status}`);
            }
            const data = await response.json();

            const traces = [{
                x: data.map(d => d.date),
                y: data.map(d => d.value),
                mode: 'lines',
                name: formData.get('parameter')
            }];

            if (formData.get('show_norm') === 'on') {
                traces.push({
                    x: data.map(d => d.date),
                    y: data.map(d => d.normal_value),
                    mode: 'lines',
                    name: 'Климатическая норма',
                    line: { dash: 'dash', color: 'purple' }
                });
            }

            if (formData.get('show_stl') === 'on') {
                traces.push({
                    x: data.map(d => d.date),
                    y: data.map(d => d.seasonal),
                    mode: 'lines',
                    name: 'Сезонность'
                }, {
                    x: data.map(d => d.date),
                    y: data.map(d => d.trend),
                    mode: 'lines',
                    name: 'Тренд'
                }, {
                    x: data.map(d => d.date),
                    y: data.map(d => d.residual),
                    mode: 'lines',
                    name: 'Остатки'
                });
            }

            const layout = {
                title: `Временной ряд: ${formData.get('parameter')}`,
                xaxis: { title: 'Дата' },
                yaxis: { title: 'Значение' }
            };

            plotGraph(traces, layout);
        } catch (error) {
            console.error('Ошибка при построении графика:', error);
        }
    });

    // Обработчик формы сезонного ряда
    document.getElementById('seasonal-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const params = new URLSearchParams();
        
        formData.forEach((value, key) => {
            if (form[key].type !== 'checkbox' || form[key].checked) {
                params.append(key, value);
            }
        });

        try {
            const response = await fetch(`/api/weather/seasonal/?${params}`);
            if (!response.ok) {
                throw new Error(`Ошибка API: ${response.status}`);
            }
            const data = await response.json();

            const traces = [{
                x: data.map(d => d.date),
                y: data.map(d => d.value),
                mode: 'lines',
                name: formData.get('parameter')
            }];

            if (formData.get('show_trend') === 'on') {
                traces.push({
                    x: data.map(d => d.date),
                    y: data.map(d => d.trend),
                    mode: 'lines',
                    name: 'Тренд'
                });
            }

            if (formData.get('show_anomalies') === 'on') {
                const anomalyData = data.filter(d => d.anomaly);
                traces.push({
                    x: anomalyData.map(d => d.date),
                    y: anomalyData.map(d => d.value),
                    mode: 'markers',
                    name: 'Аномалии',
                    marker: { size: 10, color: 'red' }
                });
            }

            const layout = {
                title: `Сезонный ряд: ${formData.get('parameter')}`,
                xaxis: { title: 'Цикл' },
                yaxis: { title: 'Значение' }
            };

            plotGraph(traces, layout);
        } catch (error) {
            console.error('Ошибка при построении графика:', error);
        }
    });

    // Обработчик формы индексов
    document.getElementById('indexes-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const params = new URLSearchParams();
        
        formData.forEach((value, key) => {
            if (form[key].type !== 'checkbox' || form[key].checked) {
                params.append(key, value);
            }
        });

        try {
            const response = await fetch(`/api/weather/indexes/?${params}`);
            if (!response.ok) {
                throw new Error(`Ошибка API: ${response.status}`);
            }
            const data = await response.json();

            let traces, layout;
            if (formData.get('vis_type') === 'heatmap') {
                const dates = [...new Set(data.map(d => d.date.split('T')[0]))];
                const values = data.map(d => d.value);
                traces = [{
                    z: [values],
                    x: dates,
                    y: [formData.get('index').toUpperCase()],
                    type: 'heatmap',
                    colorscale: 'Viridis'
                }];
                layout = {
                    title: `Тепловая карта: ${formData.get('index').toUpperCase()}`,
                    xaxis: { title: 'Дата' },
                    yaxis: { title: 'Индекс' }
                };
            } else {
                traces = [{
                    x: data.map(d => d.date),
                    y: data.map(d => d.value),
                    mode: 'lines',
                    name: formData.get('index').toUpperCase(),
                    text: data.map(d => d.date_range || '')
                }];
                layout = {
                    title: `Климатический индекс: ${formData.get('index').toUpperCase()}`,
                    xaxis: { title: 'Дата' },
                    yaxis: { title: 'Значение' }
                };
            }

            plotGraph(traces, layout, formData.get('vis_type') === 'heatmap' ? 'heatmap' : 'scatter');

            const tableBody = document.getElementById('indexes-table-body');
            if (tableBody) {
                tableBody.innerHTML = '';
                data.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="border px-4 py-2">${item.date.split('T')[0]}</td>
                        <td class="border px-4 py-2">${item.value.toFixed(2)}</td>
                        <td class="border px-4 py-2">${item.date_range || '-'}</td>
                    `;
                    tableBody.appendChild(row);
                });
                document.getElementById('indexes-table').style.display = 'block';
            }
        } catch (error) {
            console.error('Ошибка при построении графика:', error);
        }
    });

    // Скачивание PNG
    document.getElementById('download-png').addEventListener('click', () => {
        Plotly.downloadImage('plotly-graph', {
            format: 'png',
            width: 800,
            height: 500,
            filename: 'plot'
        });
    });
});