import math
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from app.schemas import (
    AtmosphericPrecursors,
    HazardRiskOutput,
    XAIFactor,
    CAPAlert,
    MultiHazardAssessmentResponse,
    WeatherData,
    TerrainData,
    HistoricalData
)
from app.services.risk_engine import risk_engine

# Primary high-vulnerability hilly and mountainous areas across India (Western Ghats, Himalayas, Northeast)
HILLY_AREAS: List[Dict[str, Any]] = [
    {
        "id": "wayanad",
        "name": "Wayanad (Meppadi), Kerala",
        "region_type": "hilly",
        "mountain_range": "Western Ghats",
        "elevation_m": 1150,
        "latitude": 11.5534,
        "longitude": 76.1320,
        "vulnerabilities": ["Landslide", "Flash Flood", "Thunderstorm"],
        "description": "High-gradient Western Ghats escarpment prone to catastrophic debris flows and saturated slope slips."
    },
    {
        "id": "shimla",
        "name": "Shimla (Summer Hill), Himachal Pradesh",
        "region_type": "hilly",
        "mountain_range": "Western Himalayas",
        "elevation_m": 2200,
        "latitude": 31.1048,
        "longitude": 77.1734,
        "vulnerabilities": ["Cloudburst", "Flash Flood", "Landslide"],
        "description": "Steep Himalayan slopes with high anthropogenic cutting, unstable regolith, and severe convective cloudburst washouts."
    },
    {
        "id": "joshimath",
        "name": "Joshimath (Chamoli), Uttarakhand",
        "region_type": "hilly",
        "mountain_range": "Central Himalayas",
        "elevation_m": 1890,
        "latitude": 30.5564,
        "longitude": 79.5630,
        "vulnerabilities": ["Landslide", "Flash Flood", "Cloudburst"],
        "description": "Fragile moraine and tectonic fault zone vulnerable to glacial outburst floods, cloudbursts, and slope subsidence."
    },
    {
        "id": "munnar",
        "name": "Munnar (Idukki), Kerala",
        "region_type": "hilly",
        "mountain_range": "Western Ghats",
        "elevation_m": 1532,
        "latitude": 10.0889,
        "longitude": 77.0595,
        "vulnerabilities": ["Landslide", "Flash Flood", "Thunderstorm"],
        "description": "Anamudi orographic crest receiving intense monsoon precipitation leading to rapid subsoil saturation."
    },
    {
        "id": "dharamshala",
        "name": "Dharamshala (Kangra), Himachal Pradesh",
        "region_type": "hilly",
        "mountain_range": "Western Himalayas (Dhauladhar)",
        "elevation_m": 1457,
        "latitude": 32.2190,
        "longitude": 76.3234,
        "vulnerabilities": ["Cloudburst", "Flash Flood", "Thunderstorm"],
        "description": "Rapid orographic ascent of monsoon clouds along steep Dhauladhar wall inducing sudden localized cloudbursts."
    },
    {
        "id": "darjeeling",
        "name": "Darjeeling, West Bengal",
        "region_type": "hilly",
        "mountain_range": "Eastern Himalayas",
        "elevation_m": 2042,
        "latitude": 27.0410,
        "longitude": 88.2663,
        "vulnerabilities": ["Landslide", "Flash Flood", "Cloudburst"],
        "description": "Steep gneiss bedrock with residual soil mantle subjected to chronic slope movements and torrential runoff."
    },
    {
        "id": "cherrapunji",
        "name": "Cherrapunji (Sohra), Meghalaya",
        "region_type": "hilly",
        "mountain_range": "Northeast Hills (Khasi Plateau)",
        "elevation_m": 1430,
        "latitude": 25.2986,
        "longitude": 91.5822,
        "vulnerabilities": ["Cloudburst", "Flash Flood", "Landslide"],
        "description": "World-record orographic funneling between Bay of Bengal winds and Khasi gorge escarpments."
    },
    {
        "id": "kodagu",
        "name": "Kodagu (Madikeri), Karnataka",
        "region_type": "hilly",
        "mountain_range": "Western Ghats",
        "elevation_m": 1150,
        "latitude": 12.4244,
        "longitude": 75.7382,
        "vulnerabilities": ["Landslide", "Flash Flood", "Thunderstorm"],
        "description": "Primary ground-truth training benchmark; deeply weathered lateritic slopes experiencing slope liquefaction."
    },
    {
        "id": "nilgiris",
        "name": "Nilgiris (Ooty), Tamil Nadu",
        "region_type": "hilly",
        "mountain_range": "Western Ghats",
        "elevation_m": 2240,
        "latitude": 11.4102,
        "longitude": 76.6950,
        "vulnerabilities": ["Landslide", "Thunderstorm", "Flash Flood"],
        "description": "High-altitude Ghats ridge with steep road cuts and valleys prone to rapid translational landslides."
    },
    {
        "id": "guwahati_hills",
        "name": "Guwahati Hills, Assam",
        "region_type": "hilly",
        "mountain_range": "Northeast Region (NER)",
        "elevation_m": 250,
        "latitude": 26.1445,
        "longitude": 91.7362,
        "vulnerabilities": ["Flash Flood", "Landslide", "Thunderstorm"],
        "description": "Eroded granitic inselbergs prone to rapid slips during intense Brahmaputra basin convective storms."
    }
]

# Secondary high-vulnerability coastal cities and ports across India
COASTAL_CITIES: List[Dict[str, Any]] = [
    {
        "id": "mumbai",
        "name": "Mumbai, Maharashtra",
        "region_type": "coastal",
        "coast": "Konkan Coast",
        "latitude": 18.9220,
        "longitude": 72.8347,
        "vulnerabilities": ["Cloudburst", "Flash Flood", "Coastal Hill Slips"],
        "description": "High urban imperviousness, Mithi River drainage, Arabian Sea storm surges."
    },
    {
        "id": "kozhikode",
        "name": "Kozhikode, Kerala",
        "coast": "Malabar Coast",
        "latitude": 11.2588,
        "longitude": 75.7804,
        "vulnerabilities": ["Thunderstorm", "Flash Flood", "Landslide"],
        "description": "Direct Arabian Sea monsoon gateway adjacent to Western Ghats escarpments."
    },
    {
        "id": "mangaluru",
        "name": "Mangaluru, Karnataka",
        "coast": "Canara Coast",
        "latitude": 12.9141,
        "longitude": 74.8560,
        "vulnerabilities": ["Thunderstorm", "Flash Flood", "Landslide"],
        "description": "Steep coastal hills meeting Gurupura & Netravati estuarine floodplains."
    },
    {
        "id": "kochi",
        "name": "Kochi, Kerala",
        "coast": "Central Malabar Coast",
        "latitude": 9.9312,
        "longitude": 76.2673,
        "vulnerabilities": ["Flash Flood", "Thunderstorm", "Cloudburst"],
        "description": "Low-lying coastal backwaters with high tidal waterlogging risk."
    },
    {
        "id": "chennai",
        "name": "Chennai, Tamil Nadu",
        "coast": "Coromandel Coast",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "vulnerabilities": ["Flash Flood", "Thunderstorm", "Cloudburst"],
        "description": "Bay of Bengal convective systems, Adyar/Cooum river urban basin ponding."
    },
    {
        "id": "visakhapatnam",
        "name": "Visakhapatnam, Andhra Pradesh",
        "coast": "Northern Circars Coast",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "vulnerabilities": ["Thunderstorm", "Flash Flood", "Coastal Landslide"],
        "description": "Eastern Ghats promontories meeting deep-water coastal bay."
    },
    {
        "id": "puri",
        "name": "Puri, Odisha",
        "coast": "Utkal Coast",
        "latitude": 19.8135,
        "longitude": 85.8312,
        "vulnerabilities": ["Thunderstorm", "Cloudburst", "Flash Flood"],
        "description": "Bay of Bengal tropical low-pressure storm tracks and flat deltaic drainage."
    },
    {
        "id": "goa",
        "name": "Panaji, Goa",
        "coast": "Central Konkan Coast",
        "latitude": 15.4909,
        "longitude": 73.8278,
        "vulnerabilities": ["Flash Flood", "Landslide", "Thunderstorm"],
        "description": "Mandovi estuary, laterite plateau coastal cuts, and Western Ghats spurs."
    }
]

# Combined Priority Areas: Hilly & Mountain Areas first, then Coastal Hubs
PRIORITY_AREAS: List[Dict[str, Any]] = HILLY_AREAS + COASTAL_CITIES

def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, x))))

class MultiTaskNowcastingEngine:
    """
    Multi-Task Extreme Weather Nowcasting Engine (0-6 hour forecast).
    Implements 4 specialized output heads:
    1. Thunderstorm Head (CAPE + IWV + Shear + Lift)
    2. Cloudburst Head (IWV + Stationary Low Shear + Rapid CTT Drop)
    3. Flash Flood Head (QPE Rain Rate + Saturated Soil + DEM downhill runoff)
    4. Landslide Head (24h/72h Antecedent Rain + Soil Liquefaction + Steep Slope Gradient)
    """

    def get_terrain_context(
        self,
        latitude: float,
        longitude: float,
        elevation: float = 0.0,
        slope: float = 0.0
    ) -> Dict[str, Any]:
        """
        Classifies geographic terrain context: Hilly/Mountainous vs Coastal vs Plains.
        Hilly areas are prioritized first as requested by the problem statement.
        """
        # 1. Check curated Hilly & Mountain Hotspots first
        for hill in HILLY_AREAS:
            dlat = abs(latitude - hill["latitude"])
            dlon = abs(longitude - hill["longitude"])
            if dlat < 0.6 and dlon < 0.6:
                return {
                    "is_hilly": True,
                    "is_coastal": False,
                    "terrain_type": "Hilly / Mountainous Terrain",
                    "mountain_range": hill["mountain_range"],
                    "badge_label": f"🏔️ {hill['mountain_range']}",
                    "description": hill["description"]
                }

        # 2. Check curated Coastal Cities
        for city in COASTAL_CITIES:
            dlat = abs(latitude - city["latitude"])
            dlon = abs(longitude - city["longitude"])
            if dlat < 0.6 and dlon < 0.6:
                return {
                    "is_hilly": False,
                    "is_coastal": True,
                    "terrain_type": "Coastal Plain / Maritime Gateway",
                    "mountain_range": None,
                    "badge_label": f"🌊 {city['coast']}",
                    "description": city["description"]
                }

        # 3. Check physical topographical thresholds for mountain terrain (elevation >= 600m or slope >= 18°)
        if elevation >= 600.0 or slope >= 18.0:
            if latitude > 28.0:
                range_name = "Western Himalayas"
            elif longitude < 77.5 and latitude < 16.0:
                range_name = "Western Ghats"
            elif longitude > 88.0:
                range_name = "Eastern Himalayas & Northeast"
            else:
                range_name = "Central Highlands / Peninsular Hills"

            return {
                "is_hilly": True,
                "is_coastal": False,
                "terrain_type": "Hilly / Mountainous Terrain",
                "mountain_range": range_name,
                "badge_label": f"🏔️ {range_name}",
                "description": f"Elevated terrain ({elevation:.0f}m, {slope:.1f}° slope) prone to orographic cloudbursts and slope instability."
            }

        # 4. General coastal maritime belt bounds
        if (8.0 <= latitude <= 23.0) and (68.0 <= longitude <= 73.5 or 79.5 <= longitude <= 87.0):
            return {
                "is_hilly": False,
                "is_coastal": True,
                "terrain_type": "Coastal Plain / Maritime Gateway",
                "mountain_range": None,
                "badge_label": "🌊 Coastal Sector",
                "description": "Maritime coastal zone susceptible to convective storm surges and drainage ponding."
            }

        # 5. Lowland baseline plains
        return {
            "is_hilly": False,
            "is_coastal": False,
            "terrain_type": "Interior Plains",
            "mountain_range": None,
            "badge_label": "🌾 Lowland Plains",
            "description": "Low-relief terrain with standard baseline drainage capacity."
        }

    def is_coastal(self, latitude: float, longitude: float) -> Tuple[bool, Optional[str]]:
        for city in COASTAL_CITIES:
            dlat = abs(latitude - city["latitude"])
            dlon = abs(longitude - city["longitude"])
            if dlat < 0.6 and dlon < 0.6:
                return True, city["coast"]
        # General peninsular Indian coastal bounds
        if (8.0 <= latitude <= 23.0) and (68.0 <= longitude <= 73.5 or 79.5 <= longitude <= 87.0):
            return True, "Indian Coastal Belt"
        return False, None

    @staticmethod
    def generate_6h_timeline(base_prob: float, trend_type: str = "convective") -> List[Dict[str, Any]]:
        """
        Generates realistic 0-6h forward nowcast risk progression:
        - convective (thunderstorm): peaks around T+2h to T+3h as vertical updrafts organize, then decays.
        - stationary (cloudburst): high persistence for T+1h to T+2h, then rapidly exhausts column water.
        - hydrological (flash flood): lags precipitation by 1-2h as surface runoff concentrates in flat basins.
        - geophysical (landslide): steadily climbs with antecedent saturation and cumulative pore water pressure.
        """
        timeline = []
        multipliers = {
            "convective": [1.0, 1.15, 1.25, 1.10, 0.85, 0.60],
            "stationary": [1.0, 1.10, 1.05, 0.80, 0.55, 0.40],
            "hydrological": [0.85, 1.0, 1.20, 1.25, 1.10, 0.90],
            "geophysical": [0.90, 0.95, 1.0, 1.05, 1.08, 1.10]
        }.get(trend_type, [1.0] * 6)

        for i, mult in enumerate(multipliers, 1):
            p = min(0.99, max(0.01, round(base_prob * mult, 3)))
            if p >= 0.70:
                lvl, clr = "Severe", "#ef4444"
            elif p >= 0.45:
                lvl, clr = "High", "#f97316"
            elif p >= 0.20:
                lvl, clr = "Moderate", "#f59e0b"
            else:
                lvl, clr = "Low", "#10b981"
            timeline.append({
                "hour": f"+{i}h",
                "probability": p,
                "probability_pct": int(p * 100),
                "risk_level": lvl,
                "color": clr
            })
        return timeline

    def generate_all_hazard_alerts(
        self,
        location_name: str,
        hazards: Dict[str, HazardRiskOutput]
    ) -> Dict[str, CAPAlert]:
        """
        Item G: Extends alert logic to fire independently per-hazard.
        A location can be High for flash flood while Low for landslide simultaneously.
        """
        alerts = {}
        for h_key, h_output in hazards.items():
            if h_output.probability >= 0.45:
                is_severe = h_output.probability >= 0.70
                severity = "Severe" if is_severe else "Moderate"
                urgency = "Immediate" if is_severe else "Expected"
                alert_id = f"IN-CAP-{datetime.utcnow().strftime('%Y%m%d%H%M')}-{h_key[:3].upper()}-{uuid.uuid4().hex[:4].upper()}"
                headline = f"NDMA/IMD {severity.upper()} WARNING: {h_output.hazard_title} in {location_name}"
                description = (
                    f"Nowcasting models detect {h_output.hazard_title} signature "
                    f"({int(h_output.probability * 100)}% probability). {h_output.primary_warning_sign}."
                )
                instruction = (
                    f"1. Follow local emergency SDRF protocols for {h_output.hazard_title.lower()}.\n"
                    f"2. Avoid inundated corridors and monitor disaster management broadcasts."
                )
                alerts[h_key] = CAPAlert(
                    identifier=alert_id,
                    sender=f"GeoShield-{h_key.capitalize()}-IMD-NDMA",
                    sent=datetime.utcnow(),
                    status="Actual",
                    msg_type="Alert",
                    scope="Public",
                    event=h_output.hazard_title,
                    urgency=urgency,
                    severity=severity,
                    certainty="Likely" if is_severe else "Possible",
                    headline=headline,
                    description=description,
                    instruction=instruction,
                    area_desc=location_name,
                    cap_xml_url=f"/api/alerts/cap/{alert_id}"
                )
        return alerts

    @staticmethod
    def build_data_provenance(
        weather: WeatherData,
        terrain: TerrainData,
        history: HistoricalData
    ) -> Dict[str, Dict[str, Any]]:
        """
        Item I: Transparent audit of all active and interface-ready data providers.
        Explicitly notes that INSAT and IMDAA are interface-ready but NOT connected.
        """
        return {
            "weather": {
                "name": "Atmospheric Telemetry & Precursors",
                "provider": weather.provider,
                "is_live": not weather.is_fallback,
                "status": "LIVE TELEMETRY" if not weather.is_fallback else "REGIONAL BASELINE",
                "source": "Open-Meteo API (ECMWF & GFS operational atmospheric models)",
                "features": ["rainfall_24h", "rainfall_72h", "soil_moisture", "cape", "dew_point", "wind_gusts"]
            },
            "terrain": {
                "name": "Digital Elevation Model & Slope",
                "provider": terrain.provider,
                "is_live": not terrain.is_fallback,
                "status": "LIVE DEM" if not terrain.is_fallback else "REGIONAL TOPOGRAPHIC HEURISTIC",
                "source": "OpenTopography (SRTM GL1 30m Global DEM)",
                "features": ["slope_angle", "elevation_asl"]
            },
            "historical": {
                "name": "Historical Landslide Catalog",
                "provider": getattr(history, "provider", getattr(history, "catalog_source", "NASA COOLR & GSI Catalog")),
                "is_live": not getattr(history, "is_fallback", False),
                "status": "ACTIVE CATALOG",
                "source": "NASA Cooperative Open Online Landslide Repository (COOLR) + GSI 2018 records",
                "features": ["historical_event_density_40km"]
            },
            "satellite_visual": {
                "name": "Satellite Visual Imagery",
                "provider": "NASA GIBS / Worldview",
                "is_live": True,
                "status": "ACTIVE TILES",
                "source": "MODIS Terra/Aqua Corrected Reflectance True Color + VIIRS SNPP",
                "features": ["optical_truecolor", "imerg_visual_precipitation"]
            },
            "insat_satellite": {
                "name": "INSAT-3D/3DR Geostationary Radiance",
                "provider": "ISRO MOSDAC / IMD Satellite Division",
                "is_live": False,
                "status": "NOT CONNECTED (Architecture Interface Ready)",
                "note": "Interface-ready for INSAT-3D/3DR TIR-1 & WV radiance feeds. Credentials not issued within hackathon timeframe.",
                "features": ["tir1_ctt_cooling", "water_vapour_channel"]
            },
            "imdaa_reanalysis": {
                "name": "IMDAA Regional Atmospheric Reanalysis",
                "provider": "NCMRWF / IMD High-Resolution Reanalysis",
                "is_live": False,
                "status": "NOT CONNECTED (Architecture Interface Ready)",
                "note": "Interface-ready via IMDAAProvider class. High-resolution 12km reanalysis credentials reserved for production swap-in.",
                "features": ["mesoscale_convergence", "dynamic_instability"]
            }
        }

    def evaluate_thunderstorm_head(self, p: AtmosphericPrecursors) -> HazardRiskOutput:
        # Thunderstorm requires: CAPE (>1000 J/kg), CIN weakening (> -50 J/kg), high IWV, active shear
        cape_norm = min(1.0, p.cape / 2200.0)
        iwv_norm = min(1.0, max(0.0, (p.iwv - 20.0) / 45.0))
        cin_factor = 1.0 - min(1.0, abs(p.cin) / 90.0)
        shear_norm = min(1.0, p.wind_shear / 14.0)

        # Logit calculation
        logit = (2.2 * cape_norm + 1.6 * iwv_norm + 1.2 * cin_factor + 0.8 * shear_norm) - 2.6
        prob = round(float(sigmoid(logit)), 4)

        if prob >= 0.75:
            level, color = "Severe", "#ef4444"
            driver = f"Explosive CAPE ({p.cape} J/kg) with rapid cloud cooling ({p.ctt_drop_rate}°C/hr)"
        elif prob >= 0.50:
            level, color = "High", "#f97316"
            driver = f"High atmospheric instability ({p.cape} J/kg) with broken convective lid"
        elif prob >= 0.25:
            level, color = "Moderate", "#f59e0b"
            driver = f"Moderate convective energy accumulating (IWV: {p.iwv} mm)"
        else:
            level, color = "Low", "#10b981"
            driver = "Stable atmosphere; negligible convective charge"

        xai = [
            XAIFactor(factor_name="CAPE Buoyant Energy", contribution_pct=40.0, description=f"Baseline feature weight: {p.cape} J/kg available for vertical updrafts"),
            XAIFactor(factor_name="Column Moisture (IWV)", contribution_pct=30.0, description=f"Baseline feature weight: {p.iwv} mm atmospheric water vapor column"),
            XAIFactor(factor_name="CIN Lid Breakthrough", contribution_pct=18.0, description=f"Baseline feature weight: Inhibition weakened to {p.cin} J/kg"),
            XAIFactor(factor_name="Vertical Wind Shear", contribution_pct=12.0, description=f"Baseline feature weight: {p.wind_shear} m/s velocity differential")
        ]

        return HazardRiskOutput(
            hazard_type="thunderstorm",
            hazard_title="Convective Thunderstorm",
            probability=prob,
            risk_level=level,
            alert_color=color,
            primary_warning_sign=driver,
            model_provenance="Prototype baseline",
            xai_breakdown=xai,
            timeline_6h=self.generate_6h_timeline(prob, "convective")
        )

    def evaluate_cloudburst_head(self, p: AtmosphericPrecursors) -> HazardRiskOutput:
        # Cloudburst requires: Extreme moisture (IWV > 55mm), LOW shear (< 7 m/s) keeping the storm stationary,
        # and rapid CTT drop rate (> 15°C/hr) indicating explosive vertical cumulonimbus.
        iwv_norm = min(1.0, max(0.0, (p.iwv - 30.0) / 40.0))
        # Inverted shear: LOW shear keeps intense rainfall trapped in one spot!
        stationary_factor = max(0.0, 1.0 - (p.wind_shear / 10.0))
        ctt_norm = min(1.0, p.ctt_drop_rate / 22.0)
        cape_norm = min(1.0, p.cape / 2500.0)

        logit = (2.8 * iwv_norm + 2.2 * stationary_factor + 2.0 * ctt_norm + 1.0 * cape_norm) - 4.5
        prob = round(float(sigmoid(logit)), 4)

        if prob >= 0.70:
            level, color = "Severe", "#ef4444"
            driver = f"Stationary super-cell locked by low shear with extreme IWV ({p.iwv} mm)"
        elif prob >= 0.45:
            level, color = "High", "#f97316"
            driver = f"Intense moisture column ({p.iwv} mm) & rapid CTT cooling ({p.ctt_drop_rate}°C/hr)"
        elif prob >= 0.20:
            level, color = "Moderate", "#f59e0b"
            driver = f"Elevated cloud top cooling with localized moisture accumulation"
        else:
            level, color = "Low", "#10b981"
            driver = "No localized torrential cloudburst signature detected"

        xai = [
            XAIFactor(factor_name="Extreme Moisture (IWV)", contribution_pct=38.0, description=f"Baseline feature weight: {p.iwv} mm atmospheric water column"),
            XAIFactor(factor_name="Stationary Low Shear", contribution_pct=32.0, description=f"Baseline feature weight: Low shear ({p.wind_shear} m/s) anchors storm burst"),
            XAIFactor(factor_name="Rapid CTT Drop Rate", contribution_pct=20.0, description=f"Baseline feature weight: Cloud cooling at {p.ctt_drop_rate}°C/hr"),
            XAIFactor(factor_name="CAPE Instability", contribution_pct=10.0, description=f"Baseline feature weight: {p.cape} J/kg vertical transport")
        ]

        return HazardRiskOutput(
            hazard_type="cloudburst",
            hazard_title="Localized Cloudburst",
            probability=prob,
            risk_level=level,
            alert_color=color,
            primary_warning_sign=driver,
            model_provenance="Prototype baseline",
            xai_breakdown=xai,
            timeline_6h=self.generate_6h_timeline(prob, "stationary")
        )

    def evaluate_flash_flood_head(self, p: AtmosphericPrecursors, is_coastal: bool, is_hilly: bool = False) -> HazardRiskOutput:
        # Flash flood requires: Heavy instantaneous QPE rain rate, high soil saturation,
        # plus DEM topography (low slope pooling in lowlands, or steep mountain channelization in hilly valleys).
        qpe_norm = min(1.0, p.qpe_rate / 25.0)
        soil_norm = min(1.0, max(0.0, (p.soil_saturation - 40.0) / 55.0))

        # DEM topographic factors (Step 3 in PDF):
        # In hilly terrain, steep slopes rapidly shed water into narrow canyon stream beds
        if is_hilly:
            drainage_factor = min(1.0, p.slope_angle / 30.0) * 1.5
            basin_desc = f"{p.slope_angle}° steep mountain catchment runoff"
        else:
            # In flat plains/coast, water cannot drain and ponds
            drainage_factor = max(0.0, 1.0 - (p.slope_angle / 25.0)) * 1.8
            basin_desc = f"{p.slope_angle}° low-gradient drainage retention"

        coastal_factor = 0.3 if is_coastal else 0.0

        logit = (2.4 * qpe_norm + 2.2 * soil_norm + drainage_factor + coastal_factor) - 2.8
        prob = round(float(sigmoid(logit)), 4)

        if prob >= 0.70:
            level, color = "Severe", "#ef4444"
            driver = f"Severe flash flood surge: High QPE ({p.qpe_rate} mm/hr) across {basin_desc} with {p.soil_saturation}% soil saturation"
        elif prob >= 0.45:
            level, color = "High", "#f97316"
            driver = f"Rapid runoff funneling ({basin_desc}, {p.soil_saturation}% soil)"
        elif prob >= 0.20:
            level, color = "Moderate", "#f59e0b"
            driver = "Drainage capacity near equilibrium; watch mountain torrents and low culverts"
        else:
            level, color = "Low", "#10b981"
            driver = "Drainage channels clear; runoff flowing normally"

        xai = [
            XAIFactor(factor_name="Instant Rain Rate (QPE)", contribution_pct=42.0, description=f"Baseline feature weight: {p.qpe_rate} mm/hr stormwater rate"),
            XAIFactor(factor_name="Soil Moisture Saturation", contribution_pct=30.0, description=f"Baseline feature weight: {p.soil_saturation}% ground saturation"),
            XAIFactor(factor_name="Topographic DEM Runoff", contribution_pct=18.0, description=f"DEM factor: {basin_desc}"),
            XAIFactor(factor_name="Regional Hydro-Factor", contribution_pct=10.0, description="Baseline feature weight: Basin hydrology factor")
        ]

        return HazardRiskOutput(
            hazard_type="flash_flood",
            hazard_title="Rapid Flash Flood",
            probability=prob,
            risk_level=level,
            alert_color=color,
            primary_warning_sign=driver,
            model_provenance="Prototype baseline",
            xai_breakdown=xai,
            timeline_6h=self.generate_6h_timeline(prob, "hydrological")
        )

    def evaluate_landslide_head(
        self,
        weather: WeatherData,
        terrain: TerrainData,
        history: HistoricalData
    ) -> HazardRiskOutput:
        # Landslide requires: High antecedent rainfall, high soil saturation, STEEP slope (> 20°), history
        ml_prob = risk_engine.predict_ml_probability(
            rainfall_24h=weather.rainfall_24h,
            rainfall_72h=weather.rainfall_72h,
            soil_moisture=weather.soil_moisture,
            slope=terrain.slope,
            elevation=terrain.elevation,
            historical_count=history.historical_landslide_count
        )
        prob = round(float(ml_prob), 4)

        if prob >= 0.70:
            level, color = "Severe", "#ef4444"
            driver = f"Critical slope shear failure imminent on {terrain.slope}° incline with {weather.soil_moisture}% saturation"
        elif prob >= 0.45:
            level, color = "High", "#f97316"
            driver = f"High slope vulnerability ({terrain.slope}°) following {weather.rainfall_24h} mm rainfall"
        elif prob >= 0.20:
            level, color = "Moderate", "#f59e0b"
            driver = f"Moderate slope instability in regional historical hazard zone"
        else:
            level, color = "Low", "#10b981"
            driver = "Terrain mechanically stable; pore water pressure safe"

        xai = [
            XAIFactor(factor_name="Soil Liquefaction Index", contribution_pct=40.0, description=f"Trained model weight: {weather.soil_moisture}% subsoil moisture"),
            XAIFactor(factor_name="24h Rainfall Intensity", contribution_pct=30.0, description=f"Trained model weight: {weather.rainfall_24h} mm direct infiltration"),
            XAIFactor(factor_name="Terrain Slope Gradient", contribution_pct=20.0, description=f"Trained model weight: {terrain.slope}° driving hillside angle"),
            XAIFactor(factor_name="Historical Landslide Record", contribution_pct=10.0, description=f"Trained model weight: {history.historical_landslide_count} prior events")
        ]

        return HazardRiskOutput(
            hazard_type="landslide",
            hazard_title="Slope Landslide & Debris Flow",
            probability=prob,
            risk_level=level,
            alert_color=color,
            primary_warning_sign=driver,
            model_provenance="Trained ML Model (LightGBM on Real 2018 Western Ghats GPS Data)",
            xai_breakdown=xai,
            timeline_6h=self.generate_6h_timeline(prob, "geophysical")
        )


    def generate_cap_alert(
        self,
        location_name: str,
        highest_hazard: HazardRiskOutput,
        all_hazards: Dict[str, HazardRiskOutput]
    ) -> Optional[CAPAlert]:
        """Generates standard Common Alerting Protocol (CAP v1.2) alert if risk exceeds threshold."""
        if highest_hazard.probability < 0.45:
            return None

        is_severe = highest_hazard.probability >= 0.70
        severity = "Severe" if is_severe else "Moderate"
        urgency = "Immediate" if is_severe else "Expected"

        hazard_names = [h.hazard_title for h in all_hazards.values() if h.probability >= 0.45]
        headline = f"NDMA/IMD {severity.upper()} MULTI-HAZARD WARNING: {', '.join(hazard_names)} expected in {location_name}"
        
        description = (
            f"Nowcasting models detect atmospheric precursors for {highest_hazard.hazard_title} "
            f"(Probability: {int(highest_hazard.probability * 100)}%). {highest_hazard.primary_warning_sign}. "
            f"Co-occurring hazards: {', '.join(hazard_names)}."
        )

        instruction = (
            "1. Stay indoors and avoid waterlogged streets and mountain cuts.\n"
            "2. Unplug electrical appliances during lightning squalls.\n"
            "3. If living in low-lying or hillside talus zones, prepare to move to designated relief shelters.\n"
            "4. Monitor local SDRF / District Disaster Management Authority broadcasts."
        )

        alert_id = f"IN-CAP-{datetime.utcnow().strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:6].upper()}"

        return CAPAlert(
            identifier=alert_id,
            sender="GeoShield-MultiHazard-IMD-NDMA",
            sent=datetime.utcnow(),
            status="Actual",
            msg_type="Alert",
            scope="Public",
            event=highest_hazard.hazard_title,
            urgency=urgency,
            severity=severity,
            certainty="Likely" if is_severe else "Possible",
            headline=headline,
            description=description,
            instruction=instruction,
            area_desc=location_name,
            cap_xml_url=f"/api/alerts/cap/{alert_id}"
        )

    def assess_all_hazards(
        self,
        latitude: float,
        longitude: float,
        location_name: str,
        weather: WeatherData,
        terrain: TerrainData,
        history: HistoricalData,
        precursors: AtmosphericPrecursors,
        is_demo: bool = False
    ) -> MultiHazardAssessmentResponse:
        t_ctx = self.get_terrain_context(latitude, longitude, terrain.elevation, terrain.slope)
        is_coast = t_ctx["is_coastal"]
        coast_name = t_ctx["badge_label"].replace("🌊 ", "") if is_coast else None
        is_hilly = t_ctx["is_hilly"]
        mountain_range = t_ctx["mountain_range"]
        terrain_type = t_ctx["terrain_type"]
        terrain_badge = t_ctx["badge_label"]

        # 4 Multi-Task Heads (Step 3 in PDF)
        h_thunder = self.evaluate_thunderstorm_head(precursors)
        h_burst = self.evaluate_cloudburst_head(precursors)
        h_flood = self.evaluate_flash_flood_head(precursors, is_coastal=is_coast, is_hilly=is_hilly)
        h_slide = self.evaluate_landslide_head(weather, terrain, history)

        hazards = {
            "thunderstorm": h_thunder,
            "cloudburst": h_burst,
            "flash_flood": h_flood,
            "landslide": h_slide
        }

        # Identify highest risk
        sorted_hazards = sorted(hazards.values(), key=lambda h: h.probability, reverse=True)
        top_hazard = sorted_hazards[0]

        # Synthesize overall advisory
        if top_hazard.probability >= 0.70:
            overall_level = "Severe"
            overall_color = "#ef4444"
            advisory = (
                f"HIGH ALERT: Immediate threat of {top_hazard.hazard_title} in {location_name}. "
                f"Convective instability and rapid accumulation detected."
            )
            actions = [
                "Evacuate vulnerable lowland basins and steep hillside slopes immediately.",
                "Avoid highway underpasses, mountain ghat roads, and coastal shoreline corridors.",
                "Disconnect electrical mains in flood-prone basements.",
                "Tune in to local emergency SDRF / NDRF radio frequencies."
            ]
        elif top_hazard.probability >= 0.45:
            overall_level = "High"
            overall_color = "#f97316"
            advisory = (
                f"WARNING: Elevated multi-hazard risk. High probability of {top_hazard.hazard_title} "
                f"within the next 2-6 hours."
            )
            actions = [
                "Restrict unnecessary outdoor travel along mountain routes and coastal highways.",
                "Inspect retaining walls and storm drainage grates for early blockages.",
                "Charge emergency battery packs and assemble first aid supplies."
            ]
        elif top_hazard.probability >= 0.20:
            overall_level = "Moderate"
            overall_color = "#f59e0b"
            advisory = f"ADVISORY: Moderate atmospheric instability present. Maintain situational awareness."
            actions = [
                "Check regional radar and weather updates.",
                "Ensure local mountain and roadside drainage culverts are free of debris."
            ]
        else:
            overall_level = "Low"
            overall_color = "#10b981"
            advisory = "NORMAL: Environmental and atmospheric parameters within manageable baseline thresholds."
            actions = [
                "Standard seasonal vigilance.",
                "Maintain functional hillside and urban drainage systems."
            ]

        # CAP Alert (Step 6 in PDF)
        cap = self.generate_cap_alert(location_name, top_hazard, hazards)
        hazard_alerts = self.generate_all_hazard_alerts(location_name, hazards)
        data_provenance = self.build_data_provenance(weather, terrain, history)

        return MultiHazardAssessmentResponse(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            is_coastal=is_coast,
            coast_region=coast_name,
            is_hilly=is_hilly,
            mountain_range=mountain_range,
            terrain_type=terrain_type,
            terrain_badge=terrain_badge,
            precursors=precursors,
            hazards=hazards,
            highest_risk_hazard=top_hazard.hazard_title,
            overall_alert_level=overall_level,
            overall_alert_color=overall_color,
            cap_alert=cap,
            hazard_alerts=hazard_alerts,
            data_provenance=data_provenance,
            advisory=advisory,
            action_items=actions,
            is_demo=is_demo
        )

    def to_cap_xml(self, alert: CAPAlert, latitude: float = 0.0, longitude: float = 0.0) -> str:
        """Serializes CAPAlert instance into OASIS CAP v1.2 standard XML specification (NDMA SACHET / IMD compliant)."""
        sent_iso = alert.sent.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>{alert.identifier}</identifier>
  <sender>{alert.sender}</sender>
  <sent>{sent_iso}</sent>
  <status>{alert.status}</status>
  <msgType>{alert.msg_type}</msgType>
  <scope>{alert.scope}</scope>
  <info>
    <category>Met</category>
    <event>{alert.event}</event>
    <urgency>{alert.urgency}</urgency>
    <severity>{alert.severity}</severity>
    <certainty>{alert.certainty}</certainty>
    <eventCode>
      <valueName>NDMA_CAP_V1.2_CODE</valueName>
      <value>EXTREME_MET_NOWCAST</value>
    </eventCode>
    <headline>{alert.headline}</headline>
    <description>{alert.description}</description>
    <instruction>{alert.instruction}</instruction>
    <area>
      <areaDesc>{alert.area_desc}</areaDesc>
      <circle>{latitude:.4f},{longitude:.4f},20.0</circle>
    </area>
    <parameter>
      <valueName>Platform</valueName>
      <value>GeoShield Early Warning System</value>
    </parameter>
  </info>
</alert>"""

nowcasting_engine = MultiTaskNowcastingEngine()

