document.addEventListener('DOMContentLoaded', async () => {
    try {
        // инициализируем карту
        const map = L.map('map', {attributionControl:false, zoomControl: false}).setView([59, 55.7], 5.9);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        // берем полигон п. края  
        var borderURL = hereURL + 'perm_polygon.json';
        const boundaryCoords = await fetch(borderURL).then(r => r.json());
        
        // меняем местами широту и долготу для turf.js
        const boundaryCoordsCorrected = boundaryCoords.map(coord => [coord[1], coord[0]]);
        // замыкаем полигон
        const first = boundaryCoordsCorrected[0];
        const last = boundaryCoordsCorrected[boundaryCoordsCorrected.length - 1];
        if (first[0] !== last[0] || first[1] !== last[1]) {
            boundaryCoordsCorrected.push([first[0], first[1]]);
        }
        // преобразуем в turf polygon
        const permBoundary = turf.polygon([boundaryCoordsCorrected]);

        
        // валидация геометрии
        if (!turf.booleanValid(permBoundary)) {
            throw new Error("Invalid boundary geometry");
        }

        // генерируем полигоны Вороного в bbox полигона
        const points = turf.randomPoint(20, { bbox: turf.bbox(permBoundary) });
        const voronoi = turf.voronoi(points, { bbox: turf.bbox(permBoundary) });
        
        // добавляем на карту
        L.geoJSON(voronoi, {
            style: { fillColor: '#3388ff', weight: 1, fillOpacity: 0.5 }
        }).addTo(map);

        L.polyline(boundaryCoords, {color: 'red', weight: 2}).addTo(map);

    } catch (error) {
        console.error("Map initialization failed:", error);
        alert("Error loading map. See console for details.");
    }
});
