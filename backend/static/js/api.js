/**
 * GeoShield API Client
 * Centralized API communication module with error handling and fallback detection.
 */

// Dynamically sets API_BASE: in standalone/Render mode uses current origin, in Vite uses VITE_API_URL
const API_BASE = window.API_BASE || window.location.origin;

class GeoShieldAPI {
  static async getPresets() {
    const res = await fetch(`${API_BASE}/api/risk/presets`);
    if (!res.ok) throw new Error("Failed to fetch location presets");
    return await res.json();
  }

  static async getPriorityLocations() {
    const res = await fetch(`${API_BASE}/api/hazards/priority-locations`);
    if (!res.ok) throw new Error("Failed to fetch priority locations");
    return await res.json();
  }

  static async getHillyAreas() {
    const res = await fetch(`${API_BASE}/api/hazards/hilly-areas`);
    if (!res.ok) throw new Error("Failed to fetch hilly areas");
    return await res.json();
  }

  static async getCoastalCities() {
    const res = await fetch(`${API_BASE}/api/hazards/coastal-cities`);
    if (!res.ok) throw new Error("Failed to fetch coastal cities");
    return await res.json();
  }

  static async assessMultiHazard(latitude, longitude, locationName = null) {
    const res = await fetch(`${API_BASE}/api/hazards/assess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        location_name: locationName
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Network error" }));
      throw new Error(err.detail || "Multi-hazard assessment request failed");
    }
    return await res.json();
  }

  static async monitorCoastalCities(region = "all") {
    const res = await fetch(`${API_BASE}/api/hazards/monitor?region=${region}`);
    if (!res.ok) throw new Error("Failed to monitor priority zones");
    return await res.json();
  }

  static async getCapAlertXml(alertId) {
    const res = await fetch(`${API_BASE}/api/alerts/cap/${alertId}?format=xml`);
    if (!res.ok) throw new Error("Failed to retrieve CAP XML feed");
    return await res.text();
  }

  static async getVerificationMetrics() {
    const res = await fetch(`${API_BASE}/api/hazards/metrics`);
    if (!res.ok) throw new Error("Failed to retrieve verification metrics");
    return await res.json();
  }

  static async loginAdmin(email, password) {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Authentication failed" }));
      throw new Error(err.detail || "Authentication failed");
    }
    return await res.json();
  }


  static async assessRisk(latitude, longitude, locationName = null) {
    const res = await fetch(`${API_BASE}/api/risk/assess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        location_name: locationName
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Network error" }));
      throw new Error(err.detail || "Risk assessment request failed");
    }
    return await res.json();
  }

  static async getDemoSteps() {
    const res = await fetch(`${API_BASE}/api/demo/steps`);
    if (!res.ok) throw new Error("Failed to load demo scenario steps");
    return await res.json();
  }

  static async getDemoStep(stepNumber) {
    const res = await fetch(`${API_BASE}/api/demo/step/${stepNumber}`);
    if (!res.ok) throw new Error(`Failed to load demo step ${stepNumber}`);
    return await res.json();
  }

  static async getSatelliteLayers(date = null) {
    const url = date 
      ? `${API_BASE}/api/satellite/layers?date=${date}`
      : `${API_BASE}/api/satellite/layers`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to retrieve satellite layer configurations");
    return await res.json();
  }

  static async getReports(severity = null) {
    const url = severity 
      ? `${API_BASE}/api/reports?severity=${severity}`
      : `${API_BASE}/api/reports`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to retrieve citizen reports");
    return await res.json();
  }

  static async submitReport(reportData) {
    const res = await fetch(`${API_BASE}/api/reports`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reportData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Submission failed" }));
      throw new Error(err.detail || "Failed to submit hazard report");
    }
    return await res.json();
  }

  static async getModelInfo() {
    const res = await fetch(`${API_BASE}/api/model/info`);
    if (!res.ok) throw new Error("Failed to retrieve model governance information");
    return await res.json();
  }

  static async retrainModel(params) {
    const res = await fetch(`${API_BASE}/api/model/retrain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Retraining failed" }));
      throw new Error(err.detail || "Model retraining failed");
    }
    return await res.json();
  }
}

window.GeoShieldAPI = GeoShieldAPI;
