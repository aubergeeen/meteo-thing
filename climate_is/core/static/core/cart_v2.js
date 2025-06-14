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
let currentParameter = null;
let currentPeriod = null;

async function updateMap(parameter, period, map, clippedFeatureCollection) {
    try {
        const apiUrl = `/api/measurements/?parameter=${parameter}&period=${period}`;
        const measurements = await fetch(apiUrl).then(r => {
            if (!r.ok) throw new Error('Failed to fetch measurements');
            return r.json();
        });

        if (measurements.length === 0) {
            alert('No data available for this combination');
            return;
        }

        // Store current parameter and period for download
        currentParameter = parameter;
        currentPeriod = period;

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
        const values = measurements.map(m => m.value).filter(v => v !== undefined);
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
        updateLegend(map, minVal, maxVal, parameter);

    } catch (error) {
        console.error('Error updating map:', error);
        alert('Error fetching data. See console for details.');
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
        const unit = parameter.includes('humidity') ? '%' : '°C';

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

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const map = L.map('map', { attributionControl: false, zoomControl: false }).setView([59, 55.7], 7);
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

        // OK button event listeners
        document.querySelectorAll('.tab-pane button').forEach(button => {
            button.addEventListener('click', async () => {
                const tab = button.closest('.tab-pane').id;
                let parameter, period;

                if (tab === 'statistics') {
                    const paramSelect = document.getElementById('parameter-select-statistics').value;
                    const aggSelect = document.getElementById('aggregate-select-statistics').value;
                    const periodSelect = document.getElementById('period-select-statistics').value;
                    parameter = paramSelect === 'temp' ? 'effective_temp' : 'min_humidity';
                    period = periodSelect;
                } else if (tab === 'indexes') {
                    parameter = 'effective_temp';
                    period = document.getElementById('period-select-indexes').value;
                }

                await updateMap(parameter, period, map, clippedFeatureCollection);
            });
        });

        // Download PNG button
        const downloadBtn = document.querySelector('#map-container button');
        downloadBtn.addEventListener('click', () => {
            if (!currentParameter || !currentPeriod) {
                alert('Сначала выберите данные для отображения на карте');
                return;
            }

            leafletImage(map, function(err, canvas) {
                if (err) {
                    console.error('Error generating map image:', err);
                    alert('Ошибка при создании изображения карты');
                    return;
                }

                const parameterName = currentParameter === 'effective_temp' ? 'EffectiveTemp' : 'MinHumidity';
                const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
                const periodName = monthNames[parseInt(currentPeriod) - 1] || 'Unknown';
                const filename = `Map_${parameterName}_${periodName}.png`;

                const link = document.createElement('a');
                link.href = canvas.toDataURL('image/png');
                link.download = filename;
                link.click();
            });
        });

        document.dispatchEvent(new Event('mapInitialized'));
    } catch (error) {
        console.error('Map initialization failed:', error);
        alert('Error loading map. See console for details.');
    }
});