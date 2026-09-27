/**
 * GeoShield Dashboard Controller
 * Multi-Hazard Nowcasting Engine (Thunderstorms, Cloudbursts, Flash Floods, Landslides)
 * Native OASIS CAP v1.2 Alert Feed for NDMA SACHET / IMD integration
 */

document.addEventListener("DOMContentLoaded", async () => {
  // Initialize Leaflet Map (Default to Wayanad Hilly Disaster Epicenter)
  const mapManager = new MapManager("riskMap");
  mapManager.init(11.5534, 76.1320, 10);

  // Active state
  let currentCapAlert = null;
  let activeAssessment = null;
  let currentUserRole = sessionStorage.getItem("geoshield_role") || "citizen";
  let activeMatrixFilter = "all";

  // DOM Elements - Navigation & Quick Filter
  const hillyAreaButtons = document.getElementById("hillyAreaButtons");
  const coastalCityButtons = document.getElementById("coastalCityButtons");
  const coordInput = document.getElementById("coordInput");
  const analyzeCoordBtn = document.getElementById("analyzeCoordBtn");
  const scanAllCitiesBtn = document.getElementById("scanAllCitiesBtn");
  const refreshMatrixBtn = document.getElementById("refreshMatrixBtn");
  const filterAllZonesBtn = document.getElementById("filterAllZonesBtn");
  const filterHillyZonesBtn = document.getElementById("filterHillyZonesBtn");
  const filterCoastalZonesBtn = document.getElementById("filterCoastalZonesBtn");
  const matrixCountBadge = document.getElementById("matrixCountBadge");

  // DOM Elements - Location & Risk Display
  const locationNameEl = document.getElementById("locationName");
  const assessmentCoordsEl = document.getElementById("assessmentCoords");
  const coastBadge = document.getElementById("coastBadge");
  const isCoastalTag = document.getElementById("isCoastalTag");
  const overallAlertBadge = document.getElementById("overallAlertBadge");

  // DOM Elements - Precursors
  const valIWV = document.getElementById("valIWV");
  const valCAPE = document.getElementById("valCAPE");
  const valCIN = document.getElementById("valCIN");
  const valShear = document.getElementById("valShear");
  const valCTT = document.getElementById("valCTT");
  const valQPESoil = document.getElementById("valQPESoil");

  // DOM Elements - 4 Hazard Prediction Heads
  const headThunderstorm = document.getElementById("headThunderstorm");
  const probThunderstorm = document.getElementById("probThunderstorm");
  const levelThunderstorm = document.getElementById("levelThunderstorm");
  const barThunderstorm = document.getElementById("barThunderstorm");
  const signThunderstorm = document.getElementById("signThunderstorm");
  const xaiThunderstorm = document.getElementById("xaiThunderstorm");
  const timelineThunderstorm = document.getElementById("timelineThunderstorm");

  const headCloudburst = document.getElementById("headCloudburst");
  const probCloudburst = document.getElementById("probCloudburst");
  const levelCloudburst = document.getElementById("levelCloudburst");
  const barCloudburst = document.getElementById("barCloudburst");
  const signCloudburst = document.getElementById("signCloudburst");
  const xaiCloudburst = document.getElementById("xaiCloudburst");
  const timelineCloudburst = document.getElementById("timelineCloudburst");

  const headFlashFlood = document.getElementById("headFlashFlood");
  const probFlashFlood = document.getElementById("probFlashFlood");
  const levelFlashFlood = document.getElementById("levelFlashFlood");
  const barFlashFlood = document.getElementById("barFlashFlood");
  const signFlashFlood = document.getElementById("signFlashFlood");
  const xaiFlashFlood = document.getElementById("xaiFlashFlood");
  const timelineFlashFlood = document.getElementById("timelineFlashFlood");

  const headLandslide = document.getElementById("headLandslide");
  const probLandslide = document.getElementById("probLandslide");
  const levelLandslide = document.getElementById("levelLandslide");
  const barLandslide = document.getElementById("barLandslide");
  const signLandslide = document.getElementById("signLandslide");
  const xaiLandslide = document.getElementById("xaiLandslide");
  const timelineLandslide = document.getElementById("timelineLandslide");

  // DOM Elements - Advisory
  const advisoryBox = document.getElementById("advisoryBox");
  const advisoryText = document.getElementById("advisoryText");
  const actionList = document.getElementById("actionList");

  // DOM Elements - CAP Alert Banner & Modal
  const capAlertBanner = document.getElementById("capAlertBanner");
  const capUrgencyBadge = document.getElementById("capUrgencyBadge");
  const capSeverityBadge = document.getElementById("capSeverityBadge");
  const capHeadline = document.getElementById("capHeadline");
  const capDescription = document.getElementById("capDescription");
  const viewCapXmlBtn = document.getElementById("viewCapXmlBtn");

  const capXmlModal = document.getElementById("capXmlModal");
  const capXmlContent = document.getElementById("capXmlContent");
  const closeCapXmlModalBtn = document.getElementById("closeCapXmlModalBtn");
  const copyCapXmlBtn = document.getElementById("copyCapXmlBtn");
  const downloadCapXmlBtn = document.getElementById("downloadCapXmlBtn");

  // DOM Elements - Matrix & Reports
  const coastalMatrixBody = document.getElementById("coastalMatrixBody");
  const reportsGrid = document.getElementById("reportsGrid");
  const reportCountBadge = document.getElementById("reportCountBadge");
  const refreshReportsBtn = document.getElementById("refreshReportsBtn");

  // DOM Elements - Forecast Verification Metrics (POD, FAR, CSI)
  const viewMetricsBtn = document.getElementById("viewMetricsBtn");
  const refreshMetricsBtn = document.getElementById("refreshMetricsBtn");
  const metricPodOverall = document.getElementById("metricPodOverall");
  const metricFarOverall = document.getElementById("metricFarOverall");
  const metricCsiOverall = document.getElementById("metricCsiOverall");
  const metricHssOverall = document.getElementById("metricHssOverall");
  const metricsBreakdownBody = document.getElementById("metricsBreakdownBody");

  // DOM Elements - Report Modal
  const reportModal = document.getElementById("reportModal");
  const openReportBtn = document.getElementById("openReportBtn");
  const closeReportModalBtn = document.getElementById("closeReportModalBtn");
  const cancelReportBtn = document.getElementById("cancelReportBtn");
  const reportForm = document.getElementById("reportForm");

  // DOM Elements - Admin Authentication & Roles
  const citizenRoleBadge = document.getElementById("citizenRoleBadge");
  const adminRoleBadge = document.getElementById("adminRoleBadge");
  const adminLoginBtn = document.getElementById("adminLoginBtn");
  const adminLogoutBtn = document.getElementById("adminLogoutBtn");
  const adminLoginModal = document.getElementById("adminLoginModal");
  const closeAdminLoginModalBtn = document.getElementById("closeAdminLoginModalBtn");
  const cancelAdminLoginBtn = document.getElementById("cancelAdminLoginBtn");
  const adminLoginForm = document.getElementById("adminLoginForm");
  const adminEmailInput = document.getElementById("adminEmailInput");
  const adminPasswordInput = document.getElementById("adminPasswordInput");
  const adminLoginError = document.getElementById("adminLoginError");
  const autofillAdminBtn = document.getElementById("autofillAdminBtn");
  const submitAdminLoginBtn = document.getElementById("submitAdminLoginBtn");
  const capBadgeLabel = document.getElementById("capBadgeLabel");

  // --- Role Management (Citizen vs Authenticated EOC Admin) ---
  function applyUserRole(role) {
    currentUserRole = role;
    sessionStorage.setItem("geoshield_role", role);

    const adminElements = document.querySelectorAll(".admin-only");
    if (role === "admin") {
      if (citizenRoleBadge) citizenRoleBadge.classList.add("hidden");
      if (adminRoleBadge) adminRoleBadge.classList.remove("hidden");
      if (adminLoginBtn) adminLoginBtn.classList.add("hidden");
      if (adminLogoutBtn) adminLogoutBtn.classList.remove("hidden");

      adminElements.forEach(el => el.classList.remove("hidden"));
    } else {
      if (citizenRoleBadge) citizenRoleBadge.classList.remove("hidden");
      if (adminRoleBadge) adminRoleBadge.classList.add("hidden");
      if (adminLoginBtn) adminLoginBtn.classList.remove("hidden");
      if (adminLogoutBtn) adminLogoutBtn.classList.add("hidden");

      adminElements.forEach(el => el.classList.add("hidden"));
    }
  }


  // --- 1. Load Priority Hotspots (Hilly & Mountain Areas First, then Coastal Hubs) ---
  async function loadPriorityLocations() {
    try {
      const data = await window.GeoShieldAPI.getPriorityLocations();
      const hilly = data.hilly_areas || [];
      const coastal = data.coastal_cities || [];

      // Render Primary Hilly & Mountain Areas
      if (hillyAreaButtons) {
        hillyAreaButtons.innerHTML = hilly.map(area => `
          <button 
            data-lat="${area.latitude}" 
            data-lon="${area.longitude}" 
            data-name="${area.name}"
            title="${area.mountain_range} • ${area.elevation_m}m elevation"
            class="zone-btn px-2.5 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 hover:text-emerald-900 text-emerald-800 font-medium transition text-xs border border-emerald-200 whitespace-nowrap shadow-2xs flex items-center gap-1">
            <span>🏔️</span>
            <span>${area.name.split(',')[0]}</span>
          </button>
        `).join("");
      }

      // Render Secondary Coastal Areas
      if (coastalCityButtons) {
        coastalCityButtons.innerHTML = coastal.map(city => `
          <button 
            data-lat="${city.latitude}" 
            data-lon="${city.longitude}" 
            data-name="${city.name}"
            title="${city.coast}"
            class="zone-btn px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 hover:text-blue-900 text-blue-800 font-medium transition text-xs border border-blue-200 whitespace-nowrap shadow-2xs flex items-center gap-1">
            <span>🌊</span>
            <span>${city.name.split(',')[0]}</span>
          </button>
        `).join("");
      }

      document.querySelectorAll(".zone-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const lat = parseFloat(btn.dataset.lat);
          const lon = parseFloat(btn.dataset.lon);
          const name = btn.dataset.name;
          mapManager.panTo(lat, lon, 10);
          mapManager.setActiveMarker(lat, lon, name);
          executeMultiHazardAssessment(lat, lon, name);
        });
      });
    } catch (err) {
      console.error("Failed to load priority locations:", err);
      if (hillyAreaButtons) hillyAreaButtons.innerHTML = `<span class="text-xs text-red-500">Failed to load mountain hotspots</span>`;
      if (coastalCityButtons) coastalCityButtons.innerHTML = `<span class="text-xs text-red-500">Failed to load coastal hubs</span>`;
    }
  }

  // --- 2. Multi-Hazard Assessment Engine ---
  async function executeMultiHazardAssessment(lat, lon, name = null) {
    try {
      assessmentCoordsEl.innerText = `Acquiring ECMWF/GFS & computing precursors for (${lat.toFixed(4)}, ${lon.toFixed(4)})...`;
      const assessment = await window.GeoShieldAPI.assessMultiHazard(lat, lon, name);
      activeAssessment = assessment;
      renderMultiHazardData(assessment);
      mapManager.setActiveMarker(lat, lon, assessment.location_name, assessment.overall_alert_level);
    } catch (err) {
      alert(`Could not complete multi-hazard assessment: ${err.message}`);
      assessmentCoordsEl.innerText = `Error: ${err.message}`;
    }
  }

  // Map click listener
  mapManager.onLocationSelected((lat, lon) => {
    executeMultiHazardAssessment(lat, lon, `Selected Coastal Zone (${lat.toFixed(3)}, ${lon.toFixed(3)})`);
  });

  // Manual Coordinate Input
  analyzeCoordBtn.addEventListener("click", () => {
    const val = coordInput.value.trim();
    if (!val) return;
    const parts = val.split(",").map(p => parseFloat(p.trim()));
    if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
      const [lat, lon] = parts;
      mapManager.panTo(lat, lon, 10);
      executeMultiHazardAssessment(lat, lon, `Custom Coordinates (${lat.toFixed(3)}, ${lon.toFixed(3)})`);
    } else {
      alert("Please enter coordinates in format: latitude, longitude (e.g. 18.9220, 72.8347)");
    }
  });

  coordInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") analyzeCoordBtn.click();
  });

  // --- 3. Render Multi-Hazard Assessment Data ---
  function renderMultiHazardData(data) {
    // Header & Location Info
    locationNameEl.innerText = data.location_name;
    assessmentCoordsEl.innerText = `${data.latitude.toFixed(4)}° N, ${data.longitude.toFixed(4)}° E`;

    if (data.is_hilly && data.mountain_range) {
      coastBadge.innerText = data.mountain_range;
      coastBadge.className = "text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200";
      isCoastalTag.innerText = "Critical Mountain Landslide Corridor";
    } else if (data.is_coastal && data.coast_region) {
      coastBadge.innerText = data.coast_region;
      coastBadge.className = "text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200";
      isCoastalTag.innerText = "Vulnerable Coastal Sector";
    } else {
      coastBadge.innerText = data.terrain_type || "Inland Sector";
      coastBadge.className = "text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200";
      isCoastalTag.innerText = "Interior Basin";
    }

    // Overall Alert Badge
    const levelColors = {
      Low: "bg-emerald-50 text-emerald-700 border-emerald-200",
      Moderate: "bg-amber-50 text-amber-700 border-amber-300",
      High: "bg-orange-50 text-orange-700 border-orange-300",
      Severe: "bg-red-50 text-red-700 border-red-300"
    };
    overallAlertBadge.className = `text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider border ${levelColors[data.overall_alert_level] || levelColors.Moderate}`;
    overallAlertBadge.innerText = `${data.overall_alert_level} ALERT`;

    // Render Atmospheric Precursors (Step 2 in PDF)
    const p = data.precursors;
    if (p) {
      valIWV.innerText = `${p.iwv} mm`;
      valCAPE.innerText = `${p.cape} J/kg`;
      valCIN.innerText = `${p.cin} J/kg`;
      valShear.innerText = `${p.wind_shear} m/s`;
      valCTT.innerText = `${p.ctt_drop_rate} °C/hr`;
      valQPESoil.innerText = `${p.qpe_rate} mm/h | ${p.soil_saturation}%`;
    }

    // Render the 4 Hazard Prediction Heads (Step 3 in PDF)
    const hazards = data.hazards || {};
    renderHead(hazards.thunderstorm, probThunderstorm, levelThunderstorm, barThunderstorm, signThunderstorm, xaiThunderstorm, timelineThunderstorm);
    renderHead(hazards.cloudburst, probCloudburst, levelCloudburst, barCloudburst, signCloudburst, xaiCloudburst, timelineCloudburst);
    renderHead(hazards.flash_flood, probFlashFlood, levelFlashFlood, barFlashFlood, signFlashFlood, xaiFlashFlood, timelineFlashFlood);
    renderHead(hazards.landslide, probLandslide, levelLandslide, barLandslide, signLandslide, xaiLandslide, timelineLandslide);

    // Render Data Provenance & Transparency (Item I)
    if (data.data_provenance) {
      const dp = data.data_provenance;
      const provWeatherStatus = document.getElementById("provWeatherStatus");
      const provTerrainStatus = document.getElementById("provTerrainStatus");
      const provWeatherProvider = document.getElementById("provWeatherProvider");
      const provTerrainProvider = document.getElementById("provTerrainProvider");

      if (provWeatherStatus && dp.weather) {
        provWeatherStatus.innerText = dp.weather.status;
        provWeatherStatus.className = dp.weather.is_live 
          ? "text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200"
          : "text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300";
      }
      if (provWeatherProvider && dp.weather) {
        provWeatherProvider.innerText = `Provider: ${dp.weather.provider}`;
      }

      if (provTerrainStatus && dp.terrain) {
        provTerrainStatus.innerText = dp.terrain.status;
        provTerrainStatus.className = dp.terrain.is_live 
          ? "text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200"
          : "text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300";
      }
      if (provTerrainProvider && dp.terrain) {
        provTerrainProvider.innerText = `Provider: ${dp.terrain.provider}`;
      }
    }

    // Advisory and Actions
    advisoryText.innerText = data.advisory;
    actionList.innerHTML = (data.action_items || []).map(item => `<li>${item}</li>`).join("");

    // CAP Alert Banner Logic (Official Advisory broadcast)
    if (data.cap_alert && (data.overall_alert_level === "Moderate" || data.overall_alert_level === "High" || data.overall_alert_level === "Severe")) {
      currentCapAlert = data.cap_alert;
      capAlertBanner.classList.remove("hidden");

      // Dynamic styling by severity
      capAlertBanner.classList.remove("bg-amber-600", "border-amber-700", "bg-orange-600", "border-orange-700", "bg-red-600", "border-red-700");

      const sev = (data.cap_alert.severity || data.overall_alert_level).toLowerCase();
      if (sev === "severe" || data.overall_alert_level === "Severe") {
        capAlertBanner.classList.add("bg-red-600", "border-red-700");
        if (capBadgeLabel) capBadgeLabel.innerText = "CRITICAL EMERGENCY BROADCAST";
      } else if (sev === "high" || data.overall_alert_level === "High") {
        capAlertBanner.classList.add("bg-orange-600", "border-orange-700");
        if (capBadgeLabel) capBadgeLabel.innerText = "HIGH SEVERITY ADVISORY";
      } else {
        capAlertBanner.classList.add("bg-amber-600", "border-amber-700");
        if (capBadgeLabel) capBadgeLabel.innerText = "OFFICIAL WEATHER ADVISORY";
      }

      capUrgencyBadge.innerText = data.cap_alert.urgency || "EXPECTED";
      capSeverityBadge.innerText = data.cap_alert.severity || data.overall_alert_level;
      capHeadline.innerText = data.cap_alert.headline;
      capDescription.innerText = data.cap_alert.description;
    } else {
      capAlertBanner.classList.add("hidden");
      currentCapAlert = null;
    }

    // Refresh role-based element visibility
    applyUserRole(currentUserRole);
  }

  function renderHead(hazard, probEl, levelEl, barEl, signEl, xaiEl, timelineEl) {
    if (!hazard) return;
    const pct = Math.round(hazard.probability * 100);
    probEl.innerText = `${pct}%`;
    levelEl.innerText = hazard.risk_level.toUpperCase();

    // WCAG contrast compliant tokens
    const colorTokens = {
      Low: { text: "text-emerald-700", bar: "bg-emerald-500" },
      Moderate: { text: "text-amber-800", bar: "bg-amber-500" },
      High: { text: "text-orange-700", bar: "bg-orange-500" },
      Severe: { text: "text-red-700", bar: "bg-red-500" }
    };
    const c = colorTokens[hazard.risk_level] || colorTokens.Moderate;
    levelEl.className = `block text-[10px] font-bold ${c.text}`;
    barEl.className = `h-2 rounded-full transition-all duration-500 ${c.bar}`;
    barEl.style.width = `${Math.min(100, Math.max(3, pct))}%`;

    signEl.innerText = hazard.primary_warning_sign;

    // Render 6-Hour Risk Timeline (Item F)
    if (timelineEl && hazard.timeline_6h && hazard.timeline_6h.length > 0) {
      timelineEl.innerHTML = hazard.timeline_6h.map(t => {
        const hPct = Math.round(t.probability * 100);
        const bgColors = {
          Low: "bg-emerald-50 text-emerald-800 border-emerald-200",
          Moderate: "bg-amber-100 text-amber-900 border-amber-300",
          High: "bg-orange-100 text-orange-950 border-orange-300",
          Severe: "bg-red-100 text-red-950 border-red-300"
        };
        const badgeClass = bgColors[t.risk_level] || bgColors.Moderate;
        return `
          <div class="flex flex-col items-center py-1 px-0.5 rounded border text-center font-mono ${badgeClass}" title="${t.hour}: ${hPct}% (${t.risk_level})">
            <span class="text-[9px] font-bold">${t.hour}</span>
            <span class="text-[10px] font-bold">${hPct}%</span>
          </div>
        `;
      }).join("");
    }

    // Render XAI breakdown tags
    if (hazard.xai_breakdown && hazard.xai_breakdown.length > 0) {
      xaiEl.innerHTML = hazard.xai_breakdown.map(f => `
        <span title="${f.description}" class="cursor-help text-[10px] bg-slate-50 border border-slate-200 px-2 py-0.5 rounded text-slate-700 font-mono font-medium">
          ${f.factor_name.split(' ')[0]}: ${Math.round(f.contribution_pct)}%
        </span>
      `).join("");
    }
  }

  // --- 4. OASIS CAP v1.2 XML Viewer Modal ---
  viewCapXmlBtn.addEventListener("click", async () => {
    if (!currentCapAlert) return;
    capXmlModal.classList.remove("hidden");
    capXmlContent.innerText = "Generating OASIS CAP v1.2 XML feed...";

    try {
      const xml = await window.GeoShieldAPI.getCapAlertXml(currentCapAlert.identifier);
      capXmlContent.innerText = xml;
    } catch (e) {
      capXmlContent.innerText = `<!-- Error fetching CAP feed: ${e.message} -->`;
    }
  });

  closeCapXmlModalBtn.addEventListener("click", () => capXmlModal.classList.add("hidden"));
  capXmlModal.addEventListener("click", (e) => {
    if (e.target === capXmlModal) capXmlModal.classList.add("hidden");
  });

  copyCapXmlBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(capXmlContent.innerText);
    const originalText = copyCapXmlBtn.innerHTML;
    copyCapXmlBtn.innerHTML = `<i class="fa-solid fa-check text-emerald-600"></i><span>Copied!</span>`;
    setTimeout(() => { copyCapXmlBtn.innerHTML = originalText; }, 2000);
  });

  downloadCapXmlBtn.addEventListener("click", () => {
    const text = capXmlContent.innerText;
    const blob = new Blob([text], { type: "application/xml" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${currentCapAlert ? currentCapAlert.identifier : 'cap_alert'}.xml`;
    a.click();
  });

  // --- 5. Priority Situational Monitoring Matrix (Hilly Areas First, then Coastal Hubs) ---
  async function loadCoastalMonitorMatrix(filter = activeMatrixFilter) {
    activeMatrixFilter = filter;
    coastalMatrixBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center py-6 text-slate-400">
          <i class="fa-solid fa-spinner fa-spin mr-2"></i>Scanning atmospheric stability across ${filter} priority stations...
        </td>
      </tr>
    `;

    try {
      const matrix = await window.GeoShieldAPI.monitorCoastalCities(filter);
      if (matrixCountBadge) {
        const label = filter === 'hilly' ? '10 Hilly Hotspots' : filter === 'coastal' ? '8 Coastal Hubs' : '18 Priority Zones (Hilly First)';
        matrixCountBadge.innerText = label;
      }

      const badgeStyles = {
        Low: "bg-emerald-50 text-emerald-700 border border-emerald-200",
        Moderate: "bg-amber-50 text-amber-700 border border-amber-200",
        High: "bg-orange-50 text-orange-700 border border-orange-200",
        Severe: "bg-red-50 text-red-700 border border-red-200"
      };

      coastalMatrixBody.innerHTML = matrix.map(m => {
        const h = m.hazards || {};
        const pThunder = h.thunderstorm ? Math.round(h.thunderstorm.probability * 100) : 0;
        const pCloud = h.cloudburst ? Math.round(h.cloudburst.probability * 100) : 0;
        const pFlood = h.flash_flood ? Math.round(h.flash_flood.probability * 100) : 0;
        const pLand = h.landslide ? Math.round(h.landslide.probability * 100) : 0;

        const isHilly = m.region_type === "hilly";
        const icon = isHilly ? "🏔️" : "🌊";
        const subtitle = m.mountain_range || m.coast || (isHilly ? "Mountain Sector" : "Coastal Sector");
        const rowClass = isHilly ? "hover:bg-emerald-50/40" : "hover:bg-blue-50/40";

        return `
          <tr class="${rowClass} transition">
            <td class="py-3 px-3">
              <div class="flex items-center space-x-1.5">
                <span class="text-xs">${icon}</span>
                <span class="font-bold text-slate-900 block">${m.name.split(',')[0]}</span>
              </div>
              <span class="text-[10px] text-slate-500 font-sans pl-4">${subtitle}</span>
            </td>
            <td class="py-3 px-3 font-semibold text-slate-800">
              ${m.highest_risk_hazard}
            </td>
            <td class="py-3 px-3 font-mono">
              <span class="${pThunder >= 50 ? 'text-orange-600 font-bold' : 'text-slate-600'}">${pThunder}%</span>
            </td>
            <td class="py-3 px-3 font-mono">
              <span class="${pCloud >= 50 ? 'text-orange-600 font-bold' : 'text-slate-600'}">${pCloud}%</span>
            </td>
            <td class="py-3 px-3 font-mono">
              <span class="${pFlood >= 50 ? 'text-orange-600 font-bold' : 'text-slate-600'}">${pFlood}%</span>
            </td>
            <td class="py-3 px-3 font-mono">
              <span class="${pLand >= 50 ? 'text-orange-600 font-bold' : 'text-slate-600'}">${pLand}%</span>
            </td>
            <td class="py-3 px-3">
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${badgeStyles[m.overall_alert_level] || badgeStyles.Moderate}">
                ${m.overall_alert_level}
              </span>
            </td>
            <td class="py-3 px-3 text-right">
              <button 
                data-lat="${m.latitude}" 
                data-lon="${m.longitude}" 
                data-name="${m.name}"
                class="inspect-city-btn px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 font-semibold rounded text-[11px] border border-slate-200 transition shadow-2xs">
                Inspect
              </button>
            </td>
          </tr>
        `;
      }).join("");

      document.querySelectorAll(".inspect-city-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const lat = parseFloat(btn.dataset.lat);
          const lon = parseFloat(btn.dataset.lon);
          const name = btn.dataset.name;
          mapManager.panTo(lat, lon, 10);
          mapManager.setActiveMarker(lat, lon, name);
          executeMultiHazardAssessment(lat, lon, name);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        });
      });

    } catch (e) {
      console.error("Matrix monitor error:", e);
      coastalMatrixBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-4 text-red-500">
            Failed to refresh priority matrix: ${e.message}
          </td>
        </tr>
      `;
    }
  }

  // Filter button handlers
  const updateFilterStyles = (activeBtn) => {
    [filterAllZonesBtn, filterHillyZonesBtn, filterCoastalZonesBtn].forEach(btn => {
      if (!btn) return;
      btn.className = (btn === activeBtn) 
        ? "px-2.5 py-1 rounded-md bg-white text-slate-900 shadow-2xs font-semibold"
        : "px-2.5 py-1 rounded-md text-slate-600 hover:text-slate-900";
    });
  };

  if (filterAllZonesBtn) {
    filterAllZonesBtn.addEventListener("click", () => {
      updateFilterStyles(filterAllZonesBtn);
      loadCoastalMonitorMatrix("all");
    });
  }
  if (filterHillyZonesBtn) {
    filterHillyZonesBtn.addEventListener("click", () => {
      updateFilterStyles(filterHillyZonesBtn);
      loadCoastalMonitorMatrix("hilly");
    });
  }
  if (filterCoastalZonesBtn) {
    filterCoastalZonesBtn.addEventListener("click", () => {
      updateFilterStyles(filterCoastalZonesBtn);
      loadCoastalMonitorMatrix("coastal");
    });
  }

  if (refreshMatrixBtn) refreshMatrixBtn.addEventListener("click", () => loadCoastalMonitorMatrix(activeMatrixFilter));
  if (scanAllCitiesBtn) scanAllCitiesBtn.addEventListener("click", () => loadCoastalMonitorMatrix("all"));

  // --- 5.1 Forecast Verification Metrics (POD / FAR / CSI) ---
  async function loadVerificationMetrics() {
    try {
      const data = await window.GeoShieldAPI.getVerificationMetrics();
      if (!data) return;

      if (metricPodOverall) metricPodOverall.innerText = `${data.overall.pod_pct}%`;
      if (metricFarOverall) metricFarOverall.innerText = `${data.overall.far_pct}%`;
      if (metricCsiOverall) metricCsiOverall.innerText = `${data.overall.csi_pct}%`;
      if (metricHssOverall) metricHssOverall.innerText = data.overall.hss.toFixed(3);

      if (metricsBreakdownBody) {
        const items = [
          ...Object.values(data.hazard_breakdown),
          data.overall
        ];

        metricsBreakdownBody.innerHTML = items.map(m => {
          const isOverall = m.hazard_type === "all";
          const c = m.contingency_table;
          return `
            <tr class="${isOverall ? 'bg-slate-50 font-bold border-t-2 border-slate-300' : 'hover:bg-slate-50'} transition">
              <td class="py-2.5 px-3">
                <span class="text-slate-900 font-semibold block">${m.hazard_title}</span>
                <span class="text-[10px] text-slate-400 font-sans">${m.hazard_type.toUpperCase()}</span>
              </td>
              <td class="py-2.5 px-3 text-[11px] font-sans text-slate-600 max-w-xs">
                ${m.benchmark_standard}
              </td>
              <td class="py-2.5 px-3 text-slate-700">${c.hits}</td>
              <td class="py-2.5 px-3 text-slate-700">${c.false_alarms}</td>
              <td class="py-2.5 px-3 text-slate-700">${c.misses}</td>
              <td class="py-2.5 px-3 text-slate-700">${c.correct_negatives}</td>
              <td class="py-2.5 px-3 text-emerald-600 font-bold">${m.pod_pct}%</td>
              <td class="py-2.5 px-3 text-blue-600 font-bold">${m.far_pct}%</td>
              <td class="py-2.5 px-3 text-purple-600 font-bold">${m.csi_pct}%</td>
              <td class="py-2.5 px-3 text-slate-900 font-bold">${m.hss.toFixed(3)}</td>
            </tr>
          `;
        }).join("");
      }
    } catch (e) {
      console.error("Verification metrics load error:", e);
      if (metricsBreakdownBody) {
        metricsBreakdownBody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-red-500">Failed to load verification metrics: ${e.message}</td></tr>`;
      }
    }
  }

  if (viewMetricsBtn) {
    viewMetricsBtn.addEventListener("click", () => {
      const el = document.getElementById("verificationMetricsSection");
      if (el) el.scrollIntoView({ behavior: "smooth" });
    });
  }
  if (refreshMetricsBtn) {
    refreshMetricsBtn.addEventListener("click", loadVerificationMetrics);
  }


  // --- 6. Citizen Hazard Reports ---
  async function loadReports() {
    try {
      const reports = await window.GeoShieldAPI.getReports();
      reportCountBadge.innerText = `${reports.length} reports`;
      mapManager.renderCitizenReports(reports);

      const typeLabels = {
        severe_storm: "Severe Storm / Squall",
        cloudburst: "Cloudburst",
        flash_flood: "Flash Flood",
        slope_cracks: "Tension Cracks",
        water_seepage: "Seepage",
        rockfall: "Rockfall",
        minor_slide: "Minor Slide",
        blocked_drainage: "Blocked Culvert"
      };

      const sevBadges = {
        low: "bg-emerald-50 text-emerald-700 border-emerald-200",
        medium: "bg-amber-50 text-amber-700 border-amber-200",
        high: "bg-orange-50 text-orange-700 border-orange-200",
        critical: "bg-red-50 text-red-700 border-red-200"
      };

      reportsGrid.innerHTML = reports.map(r => `
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                ${typeLabels[r.event_type] || r.event_type}
              </span>
              <span class="text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${sevBadges[r.severity.toLowerCase()] || sevBadges.medium}">
                ${r.severity}
              </span>
            </div>
            <h5 class="text-xs font-bold text-slate-800 line-clamp-1">${r.location_name}</h5>
            <p class="text-[11px] text-slate-600 mt-1 line-clamp-2 leading-relaxed">${r.description || 'Observed by ground reconnaissance team.'}</p>
          </div>
          <div class="mt-2.5 pt-2 border-t border-slate-200 flex items-center justify-between text-[10px] text-slate-400">
            <span>By: ${r.reporter_name || 'Ground Unit'}</span>
            <span class="font-mono">${new Date(r.timestamp).toLocaleDateString()}</span>
          </div>
        </div>
      `).join("");

    } catch (err) {
      console.error("Reports loading error:", err);
    }
  }

  refreshReportsBtn.addEventListener("click", loadReports);

  // Submit Report Modal
  openReportBtn.addEventListener("click", () => {
    reportModal.classList.remove("hidden");
    if (activeAssessment) {
      document.getElementById("repLat").value = activeAssessment.latitude.toFixed(4);
      document.getElementById("repLon").value = activeAssessment.longitude.toFixed(4);
      document.getElementById("repLocation").value = activeAssessment.location_name;
    }
  });

  const closeReportModal = () => reportModal.classList.add("hidden");
  closeReportModalBtn.addEventListener("click", closeReportModal);
  cancelReportBtn.addEventListener("click", closeReportModal);
  reportModal.addEventListener("click", (e) => {
    if (e.target === reportModal) closeReportModal();
  });

  reportForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const repData = {
      latitude: parseFloat(document.getElementById("repLat").value),
      longitude: parseFloat(document.getElementById("repLon").value),
      location_name: document.getElementById("repLocation").value,
      event_type: document.getElementById("repEventType").value,
      severity: document.getElementById("repSeverity").value,
      description: document.getElementById("repDesc").value,
      reporter_name: document.getElementById("repName").value || "Citizen Observer"
    };

    try {
      await window.GeoShieldAPI.submitReport(repData);
      closeReportModal();
      reportForm.reset();
      await loadReports();
      alert("Observation report logged successfully into early warning stream!");
    } catch (err) {
      alert(`Submission failed: ${err.message}`);
    }
  });

  // --- Admin Authentication Controls ---
  if (adminLoginBtn) {
    adminLoginBtn.addEventListener("click", () => {
      if (adminLoginModal) adminLoginModal.classList.remove("hidden");
      if (adminLoginError) adminLoginError.classList.add("hidden");
    });
  }

  const closeAdminModal = () => {
    if (adminLoginModal) adminLoginModal.classList.add("hidden");
  };

  if (closeAdminLoginModalBtn) closeAdminLoginModalBtn.addEventListener("click", closeAdminModal);
  if (cancelAdminLoginBtn) cancelAdminLoginBtn.addEventListener("click", closeAdminModal);
  if (adminLoginModal) {
    adminLoginModal.addEventListener("click", (e) => {
      if (e.target === adminLoginModal) closeAdminModal();
    });
  }

  if (autofillAdminBtn) {
    autofillAdminBtn.addEventListener("click", () => {
      if (adminEmailInput) adminEmailInput.value = "admin@geoshield.gov.in";
      if (adminPasswordInput) adminPasswordInput.value = "Admin@NDMA2026";
      if (adminLoginError) adminLoginError.classList.add("hidden");
    });
  }

  if (adminLoginForm) {
    adminLoginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (adminLoginError) adminLoginError.classList.add("hidden");
      if (submitAdminLoginBtn) {
        submitAdminLoginBtn.disabled = true;
        submitAdminLoginBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Authenticating...`;
      }

      try {
        const email = adminEmailInput.value.trim();
        const password = adminPasswordInput.value;
        const res = await window.GeoShieldAPI.loginAdmin(email, password);

        sessionStorage.setItem("geoshield_token", res.token);
        sessionStorage.setItem("geoshield_admin_profile", JSON.stringify(res.profile));
        applyUserRole("admin");
        closeAdminModal();
        adminLoginForm.reset();
        
        // Reload verification metrics now that admin is authenticated
        loadVerificationMetrics();
      } catch (err) {
        if (adminLoginError) {
          adminLoginError.innerText = err.message || "Invalid administrative credentials.";
          adminLoginError.classList.remove("hidden");
        }
      } finally {
        if (submitAdminLoginBtn) {
          submitAdminLoginBtn.disabled = false;
          submitAdminLoginBtn.innerHTML = `<i class="fa-solid fa-lock-open text-xs"></i><span>Authenticate</span>`;
        }
      }
    });
  }

  if (adminLogoutBtn) {
    adminLogoutBtn.addEventListener("click", () => {
      sessionStorage.removeItem("geoshield_token");
      sessionStorage.removeItem("geoshield_admin_profile");
      applyUserRole("citizen");
    });
  }

  // --- Initial Boot Sequence ---
  applyUserRole(currentUserRole);
  await loadPriorityLocations();
  await loadReports();
  loadVerificationMetrics();
  // Initialize with Wayanad (primary hilly landslide and flash-flood epicenter)
  await executeMultiHazardAssessment(11.5534, 76.1320, "Wayanad (Meppadi), Kerala");
  // Pre-load priority monitoring matrix in background (Hilly First)
  setTimeout(() => loadCoastalMonitorMatrix("all"), 1000);
});

