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
            if (paneId === 'seasonal') {
                updateSeasonalFieldVisibility();
            }
        }
    };

    // Функция управления видимостью полей в форме seasonal
    const updateSeasonalFieldVisibility = () => {
        const cycleSelect = document.getElementById('cycle-select-seasonal');
        const daySelect = document.getElementById('day-select-seasonal');
        const monthSelect = document.getElementById('month-select-seasonal');

        if (!cycleSelect || !daySelect || !monthSelect) {
            console.error('One or more elements not found: cycle-select-seasonal, day-select-seasonal, month-select-seasonal');
            return;
        }

        if (cycleSelect.value === 'daily') {
            daySelect.style.display = 'block';
            monthSelect.style.display = 'block';
        } else if (cycleSelect.value === 'monthly') {
            daySelect.style.display = 'none';
            monthSelect.style.display = 'block';
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

    // Обработчик для изменения цикла в форме seasonal
    const cycleSelect = document.getElementById('cycle-select-seasonal');
    if (cycleSelect) {
        cycleSelect.addEventListener('change', updateSeasonalFieldVisibility);
    }

    // Функция валидации диапазона годов
    const validateYearRange = (formData) => {
        const yearStart = parseInt(formData.get('year_start'), 10);
        const yearEnd = parseInt(formData.get('year_end'), 10);

        if (yearStart && yearEnd && yearStart > yearEnd) {
            alert('Ошибка: "Год от" не может быть больше "Года до".');
            return false;
        }
        return true;
    };

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

        if (!validateYearRange(formData)) {
            return;
        }

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

        if (!validateYearRange(formData)) {
            return;
        }

        // Валидация target_day для daily цикла
        if (formData.get('cycle') === 'daily') {
            const month = parseInt(formData.get('target_month'), 10);
            const day = parseInt(formData.get('target_day'), 10);
            const yearStart = parseInt(formData.get('year_start'), 10);
            if (!month || !day || !yearStart) {
                alert('Ошибка: Месяц, день и год начала должны быть заполнены.');
                return;
            }
            // Проверяем високосный год для февраля
            const isLeapYear = (year) => (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
            const maxDays = month === 2 && isLeapYear(yearStart) ? 29 : new Date(2025, month, 0).getDate();
            if (day < 1 || day > maxDays) {
                alert(`Ошибка: День должен быть от 1 до ${maxDays} для выбранного месяца.`);
                return;
            }
        }

        const params = new URLSearchParams();
        formData.forEach((value, key) => {
            if (form[key].type !== 'checkbox' || form[key].checked) {
                params.append(key, value);
            }
        });

        try {
            const response = await fetch(`/api/weather/seasonal/?${params}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.non_field_errors || `Ошибка API: ${response.status}`);
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
            alert(`Ошибка: ${error.message}`);
        }
    });

    // Обработчик формы индексов
    document.getElementById('indexes-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        if (!validateYearRange(formData)) {
            return;
        }

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

    // Динамическая валидация диапазона годов
    const yearStartSelects = document.querySelectorAll('[id^=year-start]');
    const yearEndSelects = document.querySelectorAll('[id^=year-end]');

    yearStartSelects.forEach((startSelect, index) => {
        const endSelect = yearEndSelects[index];
        const validateOnChange = () => {
            const yearStart = parseInt(startSelect.value, 10);
            const yearEnd = parseInt(endSelect.value, 10);
            const submitButton = startSelect.closest('form').querySelector('.form-button');
            const existingErrors = endSelect.parentNode.querySelectorAll('.error-message');

            existingErrors.forEach(error => error.remove());

            if (yearStart && yearEnd && yearStart > yearEnd) {
                submitButton.disabled = true;
                startSelect.style.borderColor = 'red';
                endSelect.style.borderColor = 'red';
                
                const error = document.createElement('div');
                error.className = 'error-message';
                error.style.color = 'red';
                error.style.fontSize = '12px';
                error.textContent = 'Ошибка: "Год начала" не может быть больше "Года конца".';
                endSelect.parentNode.insertBefore(error, endSelect.nextSibling);
            } else {
                submitButton.disabled = false;
                startSelect.style.borderColor = '';
                endSelect.style.borderColor = '';
            }
        };

        startSelect.addEventListener('change', validateOnChange);
        endSelect.addEventListener('change', validateOnChange);
    });
});