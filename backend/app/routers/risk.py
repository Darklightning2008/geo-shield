import asyncio
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import CoordinateQuery, RiskAssessmentResponse
from app.providers import OpenMeteoProvider, OpenTopographyProvider, COOLRProvider
from app.services.risk_engine import risk_engine
from app.database import get_db
from app.models import RiskAssessmentLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])

# Instantiate active provider singletons
weather_provider = OpenMeteoProvider()
terrain_provider = OpenTopographyProvider()
historical_provider = COOLRProvider()

PRESET_LOCATIONS: List[Dict[str, Any]] = [
    {
        "id": "wayanad",
        "name": "Wayanad (Meppadi), Kerala",
        "latitude": 11.5534,
        "longitude": 76.1320,
        "region": "Western Ghats",
        "historical_hazard": "High"
    },
    {
        "id": "guwahati",
        "name": "Guwahati Hills, Assam",
        "latitude": 26.1445,
        "longitude": 91.7362,
        "region": "Northeast Region (NER)",
        "historical_hazard": "High"
    },
    {
        "id": "shimla",
        "name": "Shimla (Summer Hill), Himachal Pradesh",
        "latitude": 31.1048,
        "longitude": 77.1734,
        "region": "Western Himalayas",
        "historical_hazard": "High"
    },
    {
        "id": "darjeeling",
        "name": "Darjeeling, West Bengal",
        "latitude": 27.0410,
        "longitude": 88.2663,
        "region": "Eastern Himalayas",
        "historical_hazard": "High"
    },
    {
        "id": "munnar",
        "name": "Munnar, Kerala",
        "latitude": 10.0889,
        "longitude": 77.0595,
        "region": "Western Ghats",
        "historical_hazard": "Moderate"
    },
    {
        "id": "cherrapunji",
        "name": "Cherrapunji (Sohra), Meghalaya",
        "latitude": 25.2986,
        "longitude": 91.5822,
        "region": "Northeast Region (NER)",
        "historical_hazard": "High"
    },
    {
        "id": "joshimath",
        "name": "Joshimath, Uttarakhand",
        "latitude": 30.5564,
        "longitude": 79.5630,
        "region": "Central Himalayas",
        "historical_hazard": "High"
    },
    {
        "id": "delhi_plains",
        "name": "New Delhi (Lowland Baseline)",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "region": "Indo-Gangetic Plain",
        "historical_hazard": "Negligible"
    }
]

@router.get("/presets", response_model=List[Dict[str, Any]])
async def get_presets():
    """Returns curated hotspot coordinates and control points for instant analysis."""
    return PRESET_LOCATIONS

@router.post("/assess", response_model=RiskAssessmentResponse)
async def assess_risk_endpoint(
    query: CoordinateQuery,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates real-time landslide risk for any valid geographic coordinate (-90..90, -180..180).
    Concurrently aggregates live weather (Open-Meteo), terrain DEM (OpenTopography), and historical catalog (COOLR).
    """
    lat = query.latitude
    lon = query.longitude
    loc_label = query.location_name or f"Coordinates ({lat:.4f}, {lon:.4f})"

    try:
        # Query external data providers concurrently for optimal response latency
        weather_task = weather_provider.get_weather(lat, lon)
        terrain_task = terrain_provider.get_terrain(lat, lon)
        history_task = historical_provider.get_historical_risk(lat, lon)

        weather, terrain, history = await asyncio.gather(
            weather_task, terrain_task, history_task, return_exceptions=False
        )

        assessment = risk_engine.assess_risk(
            latitude=lat,
            longitude=lon,
            location_name=loc_label,
            weather=weather,
            terrain=terrain,
            history=history,
            is_demo=False
        )

        # Log assessment asynchronously
        try:
            log_entry = RiskAssessmentLog(
                latitude=lat,
                longitude=lon,
                location_name=loc_label,
                ml_probability=assessment.ml_probability,
                baseline_risk=assessment.baseline_risk_score,
                risk_level=assessment.risk_level,
                rainfall_24h=weather.rainfall_24h,
                rainfall_72h=weather.rainfall_72h,
                soil_moisture=weather.soil_moisture,
                slope=terrain.slope,
                elevation=terrain.elevation,
                historical_count=history.historical_landslide_count,
                is_demo=False
            )
            db.add(log_entry)
            await db.commit()
        except Exception as log_err:
            logger.warning(f"Failed to record assessment log: {log_err}")

        return assessment

    except Exception as e:
        logger.error(f"Error executing risk assessment pipeline for ({lat}, {lon}): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Risk evaluation pipeline error: {str(e)}"
        )
