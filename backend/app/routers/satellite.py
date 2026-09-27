from typing import Optional, Dict, Any
from fastapi import APIRouter, Query
from app.providers import GIBSProvider

router = APIRouter(prefix="/satellite", tags=["Satellite Telemetry & Imagery"])

gibs_provider = GIBSProvider()

@router.get("/layers")
async def get_satellite_layers(
    date: Optional[str] = Query(None, description="ISO date format YYYY-MM-DD (defaults to yesterday)")
) -> Dict[str, Any]:
    """
    Returns NASA Global Imagery Browse Services (GIBS) WMTS tile endpoints
    and metadata for live interactive Leaflet map overlays.
    """
    return gibs_provider.get_satellite_layers(target_date=date)
