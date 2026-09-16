document.addEventListener("DOMContentLoaded", function () {
    const mapElement = document.getElementById("map");
    if (!mapElement) return;

    // Initialize map centered at default coordinates
    const map = L.map("map").setView([17.3850, 78.4867], 11);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Fetch map marker data from API
    fetch("/api/map_data")
        .then(response => response.json())
        .then(data => {
            data.markers.forEach(marker => {
                let color = "blue";
                if (marker.type === "disaster") {
                    if (marker.priority === "CRITICAL") color = "red";
                    else if (marker.priority === "HIGH") color = "orange";
                    else if (marker.priority === "MEDIUM") color = "gold";
                    else color = "green";
                } else {
                    color = "violet";
                }

                const markerIcon = L.divIcon({
                    className: "custom-div-icon",
                    html: `<div style="background-color:${color}; width:14px; height:14px; border-radius:50%; border:2px solid white; box-shadow:0 0 6px ${color};"></div>`,
                    iconSize: [14, 14],
                    iconAnchor: [7, 7]
                });

                L.marker([marker.lat, marker.lng], { icon: markerIcon })
                    .addTo(map)
                    .bindPopup(`<strong>${marker.title}</strong><br>${marker.details}`);
            });
        })
        .catch(err => console.error("Error loading map markers:", err));
});
