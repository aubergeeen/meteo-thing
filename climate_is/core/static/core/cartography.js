function getColor(d) {
    return d > 1000 ? '#800026' :
           d > 500  ? '#BD0026' :
           d > 200  ? '#E31A1C' :
           d > 100  ? '#FC4E2A' :
           d > 50   ? '#FD8D3C' :
           d > 20   ? '#FEB24C' :
           d > 10   ? '#FED976' :
                      '#FFEDA0';
}

function style(feature) {
    return {
        fillColor: getColor(feature.properties.val),
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
    };
}

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
        const permBoundary = turf.polygon([boundaryCoordsCorrected]);      
        if (!turf.booleanValid(permBoundary)) {
            throw new Error("Invalid boundary geometry");
        }
        // генерируем полигоны Вороного в bbox полигона
        const points = turf.randomPoint(8, { bbox: turf.bbox(permBoundary) });
        const voronoi = turf.voronoi(points, { bbox: turf.bbox(permBoundary) });
        const clippedPolygons = voronoi.features.map(feature => {
            try {
                // пересечение с полигоном региона
                const intersection = turf.intersect(turf.featureCollection([feature, permBoundary]));
                if (intersection){
                    intersection.properties = {
                        val: Math.floor(Math.random() * 1000) + 1
                    };
                }
                return intersection;
            } catch (e) {
                console.warn("Intersection failed for feature", feature, e);
                return null;
            }
        }).filter(Boolean);
        // cоздаем FeatureCollection из обрезанных полигонов
        const clippedFeatureCollection = turf.featureCollection(clippedPolygons);
        // добавляем на карту
        var geojson = L.geoJSON(clippedFeatureCollection, {
            style: style
        }).addTo(map);
        //L.polyline(boundaryCoords, {color: 'red', weight: 2}).addTo(map);
        var legend = L.control({position: 'bottomright'});
        legend.onAdd = function (map) {
            var div = L.DomUtil.create('div', 'info legend'),
                grades = [0, 10, 20, 50, 100, 200, 500, 1000],
                labels = [];
            // loop through our density intervals and generate a label with a colored square for each interval
            for (var i = 0; i < grades.length; i++) {
                div.innerHTML +=
                    '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
                    grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
            }
            return div;
        };

        legend.addTo(map);
    } catch (error) {
        console.error("Map initialization failed:", error);
        alert("Error loading map. See console for details.");
    }
});
