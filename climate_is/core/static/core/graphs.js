document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.style.display = 'none');

            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).style.display = 'block';
        });
    });

    // Form submission handler
    const forms = [
        { id: 'statistics-form', tab: 'statistics' },
        { id: 'seasonal-form', tab: 'seasonal' },
        { id: 'indexes-form', tab: 'indexes' }
    ];

    forms.forEach(({ id, tab }) => {
        const form = document.getElementById(id);
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            let params = {
                tab,
                year_start: form.querySelector(`#year-start-${tab}`).value,
                year_end: form.querySelector(`#year-end-${tab}`).value
            };

            if (tab === 'statistics') {
                params.parameter = form.querySelector('#parameter-select-statistics').value;
            } else if (tab === 'indexes') {
                params.parameter = form.querySelector('#index-select-indexes').value;
                params.threshold = form.querySelector('#threshold-indexes').value;
            } else {
                // Seasonal tab (no API support yet)
                alert('Данные для сезонного анализа недоступны');
                return;
            }

            try {
                const query = new URLSearchParams(params).toString();
                const response = await fetch(`/api/graph-data/?${query}`);
                if (!response.ok) throw new Error('Failed to fetch data');
                const data = await response.json();

                if (data.months.length === 0) {
                    alert('Нет данных для выбранной комбинации');
                    return;
                }

                // Prepare Plotly data
                const plotData = [
                    {
                        x: data.months,
                        y: tab === 'indexes' ? data.cdd : data.temperatures,
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: tab === 'indexes' ? 'CDD' : 'Фактическая температура',
                        marker: { color: '#3b82f6', size: 8 },
                        line: { color: '#3b82f6', width: 2 }
                    },
                    {
                        x: data.months,
                        y: data.climate_norm,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Климатическая норма',
                        marker: { color: '#ef4444', size: 8 },
                        line: { color: '#ef4444', width: 2, dash: 'dash' },
                        visible: tab === 'statistics' && document.getElementById('show-norm').checked
                    }
                ];

                // Update layout
                const layout = {
                    title: {
                        text: tab === 'indexes'
                            ? `Градусо-дни охлаждения (порог ${params.threshold}°C), ${params.year_start}–${params.year_end}`
                            : `Среднемесячная температура (°C), ${params.year_start}–${params.year_end}`,
                        font: { size: 18 }
                    },
                    xaxis: {
                        title: 'Месяц',
                        tickangle: 45,
                        automargin: true
                    },
                    yaxis: {
                        title: tab === 'indexes' ? 'CDD (°C)' : 'Температура (°C)'
                    },
                    margin: { t: 50, b: 100, l: 50, r: 50 },
                    showlegend: true,
                    legend: {
                        x: 1,
                        y: 1,
                        xanchor: 'right',
                        yanchor: 'top'
                    }
                };

                // Render graph
                Plotly.newPlot('plotly-graph', plotData, layout);

            } catch (error) {
                console.error('Error fetching data:', error);
                alert('Ошибка загрузки данных. Подробности в консоли.');
            }
        });
    });

    // Toggle climate norm visibility (Statistics tab only)
    document.getElementById('show-norm').addEventListener('change', function() {
        const isChecked = this.checked;
        Plotly.restyle('plotly-graph', { visible: isChecked ? true : false }, [1]);
    });

    // Download PNG
    document.getElementById('download-png').addEventListener('click', function() {
        const title = document.querySelector('.plotly-graph-div .gtitle')?.textContent || 'graph';
        Plotly.downloadImage('plotly-graph', { format: 'png', filename: title.replace(/[^a-zA-Z0-9]/g, '_') });
    });
});