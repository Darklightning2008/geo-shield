/**
 * GeoShield Leaflet Map Controller
 * 100% Free OpenStreetMap & ESRI Topo tiles (Zero API Keys Required).
 */

class MapManager {
  constructor(containerId = "riskMap") {
    this.containerId = containerId;
    this.map = null;
    this.activeMarker = null;
    this.reportMarkersLayer = null;
    this.onLocationSelectedCallback = null;
  }

  init(initialLat = 11.5534, initialLon = 76.1320, zoom = 10) {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    // 1. Standard OpenStreetMap — 100% Free, NO API Key Required
    const osmLayer = L.tileLayer(
      "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
      }
    );

    // 2. ESRI World Topographic Map — Free, Clean Terrain & Mountain Relief, NO API Key Required
    const esriTopoLayer = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
      {
        attribution: 'Tiles &copy; Esri &mdash; Sources: GEBCO, USGS, NOAA',
        maxZoom: 19
      }
    );

    this.map = L.map(this.containerId, {
      center: [initialLat, initialLon],
      zoom: zoom,
      layers: [osmLayer]
    });

    const baseMaps = {
      "OpenStreetMap (Default)": osmLayer,
      "Topographic Terrain": esriTopoLayer
    };
    L.control.layers(baseMaps, null, { position: "topright" }).addTo(this.map);

    this.reportMarkersLayer = L.layerGroup().addTo(this.map);

    // Click handler to trigger risk assessment
    this.map.on("click", (e) => {
      const { lat, lng } = e.latlng;
      this.setActiveMarker(lat, lng, "Selected Location");
      if (this.onLocationSelectedCallback) {
        this.onLocationSelectedCallback(lat, lng);
      }
    });

    // Hover coordinate tracker
    this.map.on("mousemove", (e) => {
      const coordEl = document.getElementById("hoverCoord");
      if (coordEl) {
        coordEl.innerText = `Lat: ${e.latlng.lat.toFixed(4)}, Lon: ${e.latlng.lng.toFixed(4)}`;
      }
    });

    // Ensure map tiles recalculate bounds properly
    setTimeout(() => {
      if (this.map) this.map.invalidateSize();
    }, 200);

    window.addEventListener("resize", () => {
      if (this.map) this.map.invalidateSize();
    });

    this.setActiveMarker(initialLat, initialLon, "Wayanad (Meppadi), Kerala", "Moderate");
  }

  onLocationSelected(callback) {
    this.onLocationSelectedCallback = callback;
  }

  setActiveMarker(lat, lon, label = "Assessed Location", riskLevel = "Moderate") {
    if (this.activeMarker && this.map) {
      this.map.removeLayer(this.activeMarker);
    }

    const colorMap = {
      Low: "#10b981",
      Moderate: "#f59e0b",
      High: "#f97316",
      Critical: "#ef4444"
    };
    const color = colorMap[riskLevel] || "#f59e0b";

    const customIcon = L.divIcon({
      className: "custom-pulse-marker",
      html: `
        <div style="position: relative; width: 18px; height: 18px;">
          <div class="pulse-ring" style="border: 2px solid ${color};"></div>
          <div style="width: 18px; height: 18px; background-color: ${color}; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);"></div>
        </div>
      `,
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    });

    this.activeMarker = L.marker([lat, lon], { icon: customIcon }).addTo(this.map);
    this.activeMarker.bindPopup(`
      <div style="font-family: inherit; font-size: 12px; padding: 4px; line-height: 1.4;">
        <strong style="color: #0f172a; font-size: 13px;">${label}</strong><br>
        <span style="color: #64748b;">Coordinates:</span> ${lat.toFixed(4)}, ${lon.toFixed(4)}<br>
        <span style="color: #64748b;">Risk Level:</span> <strong style="color: ${color};">${riskLevel}</strong>
      </div>
    `).openPopup();
  }

  panTo(lat, lon, zoom = 11) {
    if (this.map) {
      this.map.flyTo([lat, lon], zoom, { duration: 0.8 });
    }
  }

  renderCitizenReports(reports, visible = true) {
    if (!this.reportMarkersLayer) return;
    this.reportMarkersLayer.clearLayers();
    if (!visible) return;

    reports.forEach((rep) => {
      const sevColor = {
        low: "#10b981",
        medium: "#f59e0b",
        high: "#f97316",
        critical: "#ef4444"
      }[rep.severity.toLowerCase()] || "#f97316";

      const iconHtml = `
        <div style="background-color: ${sevColor}; color: white; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; border: 2px solid #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
          <i class="fa-solid fa-bullhorn" style="font-size: 10px;"></i>
        </div>
      `;

      const markerIcon = L.divIcon({
        className: "citizen-pin",
        html: iconHtml,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const pin = L.marker([rep.latitude, rep.longitude], { icon: markerIcon });
      pin.bindPopup(`
        <div style="font-family: inherit; font-size: 12px; padding: 4px; max-width: 220px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <strong style="color: ${sevColor}; text-transform: uppercase; font-size: 11px;">
              ${rep.event_type.replace(/_/g, ' ')}
            </strong>
            <span style="background: #f1f5f9; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; text-transform: uppercase;">
              ${rep.severity}
            </span>
          </div>
          <p style="font-weight: 600; color: #0f172a; margin: 0 0 4px 0;">${rep.location_name}</p>
          <p style="color: #475569; font-size: 11px; margin: 0 0 6px 0; line-height: 1.3;">${rep.description || 'No description provided.'}</p>
          <div style="font-size: 10px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 4px; display: flex; justify-content: space-between;">
            <span>By: ${rep.reporter_name}</span>
          </div>
        </div>
      `);
      this.reportMarkersLayer.addLayer(pin);
    });
  }
}

window.MapManager = MapManager;
