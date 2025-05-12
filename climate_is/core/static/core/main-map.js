document.addEventListener('DOMContentLoaded', () => {
    console.log(hereURL)
    var map = L.map('insert-map-here').setView([58.0092, 56.2270], 5);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);
    const apiUrl = '/api/locate/?fields=station_id,longitude,latitude';
    
    const customIcon = L.icon({
        iconUrl: hereURL + 'map-marker.ico', // путь к изображению иконки
        iconSize: [32, 32], // размер иконки
        iconAnchor: [16, 32], // точка привязки (по центру снизу)
        popupAnchor: [0, -32] // точка для popup относительно иконки
    });
    
    var borderURL = hereURL + 'perm_polygon.json';
    fetch(borderURL)
    .then(response => response.json())
    .then(data => {
        borderCoordinates = data;
        const polyline = L.polyline(borderCoordinates, {color: 'red'}).addTo(map);
    });
    //var polyline = L.polyline(border, {color: 'red'});

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Координаты станций:', data);
            data.forEach(station => {
                    const lat = station.latitude;
                    const lon = station.longitude;
                    const stationId = station.station_id;

                    L.marker([lat, lon], { icon: customIcon })
                        .addTo(map)
                        .bindPopup(`Station ID: ${stationId}`);
                    //polyline.addTo(map);
            });
        })
        .catch(error => {
        console.error('Ошибка при получении данных:', error);
        });
});