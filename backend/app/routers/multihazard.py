import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from app.schemas import CoordinateQuery, MultiHazardAssessmentResponse, CAPAlert
from app.providers import OpenMeteoProvider, OpenTopographyProvider, COOLRProvider
from app.services.nowcasting_engine import nowcasting_engine, COASTAL_CITIES, HILLY_AREAS, PRIORITY_AREAS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hazards", tags=["Multi-Hazard Nowcasting"])

# External data providers
weather_provider = OpenMeteoProvider()
terrain_provider = OpenTopographyProvider()
historical_provider = COOLRProvider()

# In-memory storage for active CAP alerts to serve OASIS XML
ACTIVE_CAP_ALERTS: Dict[str, Dict[str, Any]] = {}

@router.get("/hilly-areas", response_model=List[Dict[str, Any]])
async def get_hilly_areas():
    """
    Returns prioritized high-vulnerability mountainous hotspots across
    the Western Ghats, Western Himalayas, Eastern Himalayas, and Northeast Hills.
    """
    return HILLY_AREAS

@router.get("/coastal-cities", response_model=List[Dict[str, Any]])
async def get_coastal_cities():
    """
    Returns curated coastal cities and ports across India's coastline
    (Konkan, Malabar, Canara, Coromandel, Northern Circars, and Utkal coasts).
    """
    return COASTAL_CITIES

@router.get("/priority-locations", response_model=Dict[str, Any])
async def get_priority_locations():
    """
    Returns prioritized locations categorized with Hilly Areas FIRST, followed by Coastal Hubs.
    """
    return {
        "hilly_areas": HILLY_AREAS,
        "coastal_cities": COASTAL_CITIES,
        "all_locations": PRIORITY_AREAS
    }

@router.get("/metrics")
async def get_multihazard_verification_metrics():
    """
    Returns meteorological and natural hazard forecast verification metrics:
    POD (Probability of Detection), FAR (False Alarm Rate), CSI (Critical Success Index),
    and Heidke Skill Score (HSS) with full 2x2 contingency tables.
    """
    from app.services.metrics_service import metrics_service
    return metrics_service.get_system_verification_summary()


@router.post("/assess", response_model=MultiHazardAssessmentResponse)
async def assess_multi_hazard(query: CoordinateQuery):
    """
    Multi-Task Atmospheric Nowcasting (0-6 hours) for:
    - ⛈️ Convective Thunderstorms (CAPE, IWV, Shear, CIN lid)
    - 🌧️ Localized Cloudbursts (Extreme IWV, Stationary Low Shear, CTT drop)
    - 🌊 Rapid Flash Floods (Instant QPE, Saturated Soil, Flat Basin Drainage)
    - ⛰️ Slope Landslides (Antecedent 24h/72h Rain, Soil Moisture, Steep Gradient)
    Generates explainable AI (XAI) feature attributions and OASIS CAP v1.2 alerts.
    """
    lat = query.latitude
    lon = query.longitude
    loc_label = query.location_name or f"Coastal Sector ({lat:.4f}, {lon:.4f})"

    try:
        # Fetch atmospheric telemetry, terrain DEM, and historical catalogues concurrently
        weather_task = weather_provider.get_weather(lat, lon)
        terrain_task = terrain_provider.get_terrain(lat, lon)
        history_task = historical_provider.get_historical_risk(lat, lon)

        weather, terrain, history = await asyncio.gather(
            weather_task, terrain_task, history_task, return_exceptions=False
        )

        # Compute physical precursors (IWV, CIN, convergence, shear, CTT drop, QPE)
        precursors = OpenMeteoProvider.extract_precursors(
            weather=weather,
            slope=terrain.slope,
            elevation=terrain.elevation
        )

        # Run Multi-Task Nowcasting Engine
        assessment = nowcasting_engine.assess_all_hazards(
            latitude=lat,
            longitude=lon,
            location_name=loc_label,
            weather=weather,
            terrain=terrain,
            history=history,
            precursors=precursors,
            is_demo=False
        )

        # Cache CAP alert if triggered
        if assessment.cap_alert:
            ACTIVE_CAP_ALERTS[assessment.cap_alert.identifier] = {
                "alert": assessment.cap_alert,
                "latitude": lat,
                "longitude": lon
            }

        return assessment

    except Exception as e:
        logger.error(f"Error executing multi-hazard nowcasting for ({lat}, {lon}): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Multi-hazard evaluation error: {str(e)}"
        )

@router.get("/monitor", response_model=List[Dict[str, Any]])
async def monitor_coastal_cities(
    region: Optional[str] = Query("all", description="Filter zones: 'all' (hilly first then coastal), 'hilly', or 'coastal'")
):
    """
    Simultaneously scans and computes multi-hazard risk indices across India's
    priority vulnerable zones (Hilly & Mountain Areas first, then Coastal Hubs).
    """
    if region == "hilly":
        targets = HILLY_AREAS
    elif region == "coastal":
        targets = COASTAL_CITIES
    else:
        # Default: Hilly areas first, followed by coastal cities
        targets = PRIORITY_AREAS

    results = []

    async def _evaluate_location(loc: Dict[str, Any]):
        try:
            w = await weather_provider.get_weather(loc["latitude"], loc["longitude"])
            t = await terrain_provider.get_terrain(loc["latitude"], loc["longitude"])
            h = await historical_provider.get_historical_risk(loc["latitude"], loc["longitude"])
            p = OpenMeteoProvider.extract_precursors(w, t.slope, t.elevation)
            res = nowcasting_engine.assess_all_hazards(
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                location_name=loc["name"],
                weather=w,
                terrain=t,
                history=h,
                precursors=p
            )
            if res.cap_alert:
                ACTIVE_CAP_ALERTS[res.cap_alert.identifier] = {
                    "alert": res.cap_alert,
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"]
                }
            return {
                "id": loc["id"],
                "name": loc["name"],
                "region_type": loc.get("region_type", "hilly" if "mountain_range" in loc else "coastal"),
                "mountain_range": loc.get("mountain_range"),
                "coast": loc.get("coast"),
                "zone_badge": loc.get("mountain_range") or loc.get("coast") or "Vulnerable Zone",
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "vulnerabilities": loc.get("vulnerabilities", []),
                "overall_alert_level": res.overall_alert_level,
                "overall_alert_color": res.overall_alert_color,
                "highest_risk_hazard": res.highest_risk_hazard,
                "precursors": res.precursors.dict(),
                "hazards": {k: v.dict() for k, v in res.hazards.items()},
                "cap_alert": res.cap_alert.dict() if res.cap_alert else None,
                "advisory": res.advisory
            }
        except Exception as err:
            logger.warning(f"Error scanning location {loc['name']}: {err}")
            return {
                "id": loc["id"],
                "name": loc["name"],
                "region_type": loc.get("region_type", "hilly" if "mountain_range" in loc else "coastal"),
                "mountain_range": loc.get("mountain_range"),
                "coast": loc.get("coast"),
                "zone_badge": loc.get("mountain_range") or loc.get("coast") or "Vulnerable Zone",
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "vulnerabilities": loc.get("vulnerabilities", []),
                "overall_alert_level": "Low",
                "overall_alert_color": "#10b981",
                "highest_risk_hazard": "None",
                "advisory": "Monitoring active."
            }

    tasks = [_evaluate_location(loc) for loc in targets]
    results = await asyncio.gather(*tasks)
    return results

# OASIS CAP v1.2 Feed Endpoints (Step 6 in PDF)
cap_router = APIRouter(prefix="/alerts", tags=["Common Alerting Protocol (CAP)"])

@cap_router.get("/cap/{alert_id}")
async def get_cap_alert_xml(
    alert_id: str,
    format: str = Query("xml", description="Format: 'xml' (OASIS CAP v1.2) or 'json'")
):
    """
    Serves official OASIS Common Alerting Protocol (CAP v1.2) XML feeds
    interoperable with NDMA SACHET and IMD National Alert feeds.
    """
    cached = ACTIVE_CAP_ALERTS.get(alert_id)
    if cached:
        alert: CAPAlert = cached["alert"]
        lat = cached["latitude"]
        lon = cached["longitude"]
    else:
        # Fallback dynamic CAP alert if ID requested directly
        alert = CAPAlert(
            identifier=alert_id,
            sender="GeoShield-MultiHazard-IMD-NDMA",
            sent=datetime.utcnow(),
            status="Actual",
            msg_type="Alert",
            scope="Public",
            event="Extreme Convective Weather",
            urgency="Expected",
            severity="Severe",
            certainty="Likely",
            headline=f"NDMA/IMD Multi-Hazard Alert ({alert_id})",
            description="Active atmospheric precursors detected across coastal monitoring corridor.",
            instruction="Avoid flood-prone roadways and seek safe shelter away from unstable slopes.",
            area_desc="Coastal India Emergency Grid",
            cap_xml_url=f"/api/alerts/cap/{alert_id}"
        )
        lat = 18.9220
        lon = 72.8347

    if format.lower() == "json":
        return JSONResponse(content=alert.dict())

    xml_content = nowcasting_engine.to_cap_xml(alert, latitude=lat, longitude=lon)
    return Response(content=xml_content, media_type="application/xml")
