
        const validCells = voronoi.features.filter(cell => 
            cell && turf.booleanValid(cell)
        );
        const cleanBoundary = turf.buffer(permBoundary, 4);
        
        console.log("permBoundary:", JSON.stringify(permBoundary));
        
        const clipped = turf.featureCollection(
            validCells.map(cell => {
                try {
                    const result = turf.intersect(cell, cleanBoundary);
                    return result && !turf.booleanEmpty(result) ? result : null;
                } catch (e) {
                    console.warn(`Skipping cell ${cell.properties.site}:`, e.message);
                    return null;
                }
            }).filter(Boolean)
        );





document.addEventListener('DOMContentLoaded', () =>{
    // создаем карту
    var map = L.map('map', {attributionControl:false}).setView([59, 55.7], 5.9);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
    }).addTo(map);
    
    // генерируем полигоны Вороного
    const options = { bbox: [51.7, 56, 59.7, 61.8] };
    const points = turf.randomPoint(20, options);
    const voronoiPolygons = turf.voronoi(points, options);

    // берем полигон п. края  
    var borderURL = hereURL + 'perm_polygon.json';
    fetch(borderURL)
        .then(response => response.json())
        .then(coordinate_pairs => {
            // проверяем на замкнутость
            if (!turf.booleanEqual(
                turf.point(coordinate_pairs[0]), 
                turf.point(coordinate_pairs[coordinate_pairs.length-1])
            )) {
                coordinate_pairs.push(coordinate_pairs[0]);
            }
            // преобразуем полигон 
            const permBoundary = turf.polygon([coordinate_pairs]);
            
            // валидация полигона
            if (!turf.booleanValid(permBoundary)) {
                throw new Error("Invalid boundary geometry");
            }
            // обрезаем под полигон
            const clippedPolygons = {
                type: 'FeatureCollection',
                features: voronoiPolygons.features.map(voronoiCell => {
                    if (!turf.booleanValid(voronoiCell)) return null;
                    
                    try {
                        const result = turf.intersect(voronoiCell, permBoundary);
                        return result && turf.booleanValid(result) ? result : null;
                    } catch (e) {
                        console.warn("Clipping skipped for cell:", e);
                        return null;
                    }
                }).filter(Boolean)
            };
            // добавляем на карту
            L.geoJSON(clippedPolygons, {
                style: {
                    fillColor: 'blue',
                    weight: 1,
                    fillOpacity: 0.5
                }
            }).addTo(map);

            L.polyline(coordinate_pairs, {color: 'red', weight: 2}).addTo(map);
        })
        .catch(error => console.error("Error:", error));
});
