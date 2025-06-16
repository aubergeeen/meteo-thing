function getAdaptiveColor(value, minVal, maxVal) {
    const colors = ['#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026'];
    const range = maxVal - minVal;
    if (range === 0) return colors[0];
    
    const step = range / (colors.length - 1);
    const index = Math.min(Math.floor((value - minVal) / step), colors.length - 1);
    return colors[index]; 
}

function getColorBreaks(minVal, maxVal, steps = 8) {
    const range = maxVal - minVal;
    const step = range / (steps - 1);
    return Array.from({ length: steps }, (_, i) => minVal + i * step);
}

function style(feature, minVal, maxVal) {
    return {
        fillColor: feature.properties.val ? getAdaptiveColor(feature.properties.val, minVal, maxVal) : '#d3d3d3',
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
    };
}

let geojsonLayer = null;
let currentLegend = null;
let currentParameters = null;

async function updateMap(params, map, clippedFeatureCollection) {
    try {
        const queryString = new URLSearchParams(params).toString();
        const apiUrl = `/api/weather/cartography/?${queryString}`;
        const measurements = await fetch(apiUrl).then(r => {
            if (!r.ok) throw new Error(`Failed to fetch measurements: ${r.statusText}`);
            return r.json();
        });

        if (measurements.length === 0) {
            alert('Нет данных для выбранной комбинации');
            return;
        }

        // Store current parameters for download
        currentParameters = params;

        // Map measurements to station IDs
        const measurementMap = {};
        measurements.forEach(m => {
            measurementMap[m.station] = m.value;
        });

        // Assign values to Voronoi polygons using station_id
        clippedFeatureCollection.features.forEach(feature => {
            const stationId = feature.properties.station_id;
            feature.properties.val = measurementMap[stationId] || null;
        });

        // Calculate min and max values
        const values = measurements.map(m => m.value).filter(v => v !== null && v !== undefined);
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);

        // Remove existing layer
        if (geojsonLayer) {
            map.removeLayer(geojsonLayer);
        }

        // Add new GeoJSON layer
        geojsonLayer = L.geoJSON(clippedFeatureCollection, {
            style: feature => style(feature, minVal, maxVal)
        }).addTo(map);

        // Update legend
        updateLegend(map, minVal, maxVal, params.parameter);

    } catch (error) {
        console.error('Error updating map:', error);
        alert('Ошибка при загрузке данных. Подробности в консоли.');
    }
}

function updateLegend(map, minVal, maxVal, parameter) {
    if (currentLegend) {
        map.removeControl(currentLegend);
        currentLegend = null;
    }

    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function () {
        const div = L.DomUtil.create('div', 'info legend');
        const grades = getColorBreaks(minVal, maxVal);
        const unit = parameter === 'humidity' ? '%' : ['precip', 'hdd', 'cdd'].includes(parameter) ? '' : '°C';

        for (let i = 0; i < grades.length; i++) {
            div.innerHTML +=
                `<div><i style="background:${getAdaptiveColor(grades[i], minVal, maxVal)}"></i> ` +
                grades[i].toFixed(1) + (grades[i + 1] !== undefined ? '–' + grades[i + 1].toFixed(1) : '+') + ` ${unit}</div>`;
        }
        return div;
    };
    legend.addTo(map);
    currentLegend = legend;
}

function updateAggregateOptions(tab) {
    const parameterSelect = document.getElementById(`parameter-select-${tab}`);
    const aggregateSelect = document.getElementById(`aggregate-select-${tab}`);
    const parameter = parameterSelect.value;

    // Enable all options by default
    Array.from(aggregateSelect.options).forEach(option => {
        option.disabled = false;
    });

    if (tab === 'statistics') {
        aggregateSelect.querySelector('option[value="sum"]').disabled = true;
        if (parameter === 'PRECIP') {
            aggregateSelect.querySelector('option[value="sum"]').disabled = false;
        }
    } else if (tab === 'indexes') {
        if (['utci', 'wbgt', 'cwsi', 'heat_index'].includes(parameter)) {
            aggregateSelect.querySelector('option[value="sum"]').disabled = true;
        } else if (['hdd', 'cdd'].includes(parameter)) {
            Array.from(aggregateSelect.options).forEach(option => {
                option.disabled = option.value !== 'sum';
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const map = L.map('map', { attributionControl: false, zoomControl: false }).setView([59, 55.7], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        const borderURL = hereURL + 'perm_polygon.json';
        const boundaryCoords = await fetch(borderURL).then(r => r.json());
        const boundaryCoordsCorrected = boundaryCoords.map(coord => [coord[1], coord[0]]);
        const first = boundaryCoordsCorrected[0];
        const last = boundaryCoordsCorrected[boundaryCoordsCorrected.length - 1];
        
        if (first[0] !== last[0] || first[1] !== last[1]) {
            boundaryCoordsCorrected.push([first[0], first[1]]);
        }
        const permBoundary = turf.polygon([boundaryCoordsCorrected]);
        if (!turf.booleanValid(permBoundary)) {
            throw new Error('Invalid boundary geometry');
        }

        const apiUrl = '/api/locate/?fields=station_id,latitude,longitude';
        const stations = await fetch(apiUrl).then(r => {
            if (!r.ok) throw new Error('Failed to fetch station data');
            return r.json();
        });

        const stationPoints = stations.map(station => ({
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [station.longitude, station.latitude]
            },
            properties: {
                station_id: station.station_id
            }
        }));
        const pointsFeatureCollection = turf.featureCollection(stationPoints);
        if (stationPoints.length === 0) {
            throw new Error('No station points available');
        }

        const voronoi = turf.voronoi(pointsFeatureCollection, { bbox: turf.bbox(permBoundary) });
        const clippedPolygons = voronoi.features.map((feature, index) => {
            try {
                const intersection = turf.intersect(turf.featureCollection([feature, permBoundary]));
                if (intersection) {
                    intersection.properties = {
                        station_id: stationPoints[index].properties.station_id,
                        val: null
                    };
                    return intersection;
                }
                return null;
            } catch (e) {
                console.warn('Intersection failed for feature', feature, e);
                return null;
            }
        }).filter(Boolean);
        const clippedFeatureCollection = turf.featureCollection(clippedPolygons);

        const customIcon = L.icon({
            iconUrl: hereURL + 'marker.ico',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        });

        stations.forEach(station => {
            L.marker([station.latitude, station.longitude], { icon: customIcon }).addTo(map);
        });

        geojsonLayer = L.geoJSON(clippedFeatureCollection, {
            style: feature => ({
                fillColor: '#d3d3d3',
                weight: 2,
                opacity: 1,
                color: 'white',
                dashArray: '3',
                fillOpacity: 0.7
            })
        }).addTo(map);

        window.leafletMap = map;

        // Initialize aggregate options
        updateAggregateOptions('statistics');
        updateAggregateOptions('indexes');

        // Parameter change listeners
        document.getElementById('parameter-select-statistics').addEventListener('change', () => updateAggregateOptions('statistics'));
        document.getElementById('parameter-select-indexes').addEventListener('change', () => updateAggregateOptions('indexes'));

        // Form submission listeners
        document.getElementById('statistics-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const params = {
                parameter: document.getElementById('parameter-select-statistics').value,
                aggregate: document.getElementById('aggregate-select-statistics').value,
                month: document.getElementById('month-select-statistics').value,
                year: document.getElementById('year-select-statistics').value,
                zero_missing: document.getElementById('zero-missing-statistics').checked
            };
            await updateMap(params, map, clippedFeatureCollection);
        });

        document.getElementById('indexes-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const params = {
                parameter: document.getElementById('parameter-select-indexes').value,
                aggregate: document.getElementById('aggregate-select-indexes').value,
                month: document.getElementById('month-select-indexes').value,
                year: document.getElementById('year-select-indexes').value,
                zero_missing: document.getElementById('zero-missing-indexes').checked
            };
            await updateMap(params, map, clippedFeatureCollection);
        });

        // Download PNG button
        const downloadBtn = document.getElementById('download-btn');
        downloadBtn.addEventListener('click', async () => {
            if (!currentParameters) {
                alert('Сначала выберите данные для отображения на карте');
                return;
            }

            try {
                // Ensure map is fully rendered
                map.invalidateSize();
                //await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for layers to render

                // Capture map container
                // const mapElement = document.getElementById('map');
                // const dataUrl = await domtoimage.toPng(mapElement, {
                //     quality: 0.8, // Reduce quality for faster rendering
                //     bgcolor: '#ffffff' // White background
                // });

                // Get map div dimensions
                const mapElement = document.getElementById('map');
                const rect = mapElement.getBoundingClientRect();
                const width = Math.round(rect.width);
                const height = Math.round(rect.height);

                // Capture map container with exact dimensions
                const dataUrl = await domtoimage.toPng(mapElement, {
                    quality: 0.8, // Balanced quality
                    bgcolor: '#ffffff', // White background
                    width: width, // Match div width
                    height: height // Match div height
                });

                // Create download link
                const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
                const parameterName = currentParameters.parameter || 'Unknown';
                const periodName = monthNames[parseInt(currentParameters.month) - 1] || 'Unknown';
                const year = currentParameters.year || new Date().getFullYear();
                const filename = `Map_${parameterName}_${periodName}_${year}.png`;

                const link = document.createElement('a');
                link.href = dataUrl;
                link.download = filename;
                link.click();
            } catch (err) {
                console.error('Error generating map image:', err);
                alert('Ошибка при создании изображения карты');
            }
        });

        document.dispatchEvent(new Event('mapInitialized'));
    } catch (error) {
        console.error('Map initialization failed:', error);
        alert('Ошибка инициализации карты. Подробности в консоли.');
    }
});