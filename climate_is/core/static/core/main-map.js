document.addEventListener('DOMContentLoaded', () => {
    console.log(hereURL);
    var map = L.map('insert-map-here').setView([59.0092, 56.2270], 6);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors',
        zoomSnap: 2
    }).addTo(map);

    const customIcon = L.icon({
        iconUrl: hereURL + 'marker.ico',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
    });

    var borderURL = hereURL + 'perm_polygon.json';
    fetch(borderURL)
        .then(response => response.json())
        .then(data => {
            borderCoordinates = data;
            const polyline = L.polyline(borderCoordinates, {color: 'red'}).addTo(map);
        })
        .catch(error => console.error('Error fetching border data:', error));

    const apiUrl = '/api/locate/?fields=station_id,name,description,latitude,longitude,elevation,soil_type';
    
    // Mapping for soil_type codes to human-readable labels
    const soilTypeLabels = {
        'PT': 'Торфяные',
        'PD': 'Подзолистые',
        'GF': 'Серые лесные',
        'CL': 'Глинистые/суглинки',
        'SL': 'Песчаные/супеси',
        'UR': 'Урбанизированные',
        'MT': 'Горные',
        'FP': 'Пойменные'
    };

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Координаты и данные станций:', data);
            data.forEach(station => {
                const lat = station.latitude;
                const lon = station.longitude;
                const stationId = station.station_id;
                const name = station.name;
                const description = station.description || 'Нет описания';
                const elevation = station.elevation;
                const soilType = soilTypeLabels[station.soil_type] || station.soil_type;

                // Create popup content with styled card
                const popupContent = `
                    <div class="station-card">
                        <h3>${name}</h3>
                        <p><strong>Описание:</strong> ${description}</p>
                        <p><strong>Широта:</strong> ${lat}</p>
                        <p><strong>Долгота:</strong> ${lon}</p>
                        <p><strong>Высота над уровнем моря:</strong> ${elevation} м</p>
                        <p><strong>Тип почвы:</strong> ${soilType}</p>
                    </div>
                `;

                L.marker([lat, lon], { icon: customIcon })
                    .addTo(map)
                    .bindPopup(popupContent, { className: 'station-popup' });
            });
        })
        .catch(error => {
            console.error('Ошибка при получении данных станций:', error);
        });
});