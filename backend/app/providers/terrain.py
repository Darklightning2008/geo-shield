import math
import logging
import httpx
from typing import Dict, Tuple, Optional
from app.providers.base import TerrainProvider
from app.schemas import TerrainData
from app.config import settings

logger = logging.getLogger(__name__)

class OpenTopographyProvider(TerrainProvider):
    """
    Terrain provider querying Digital Elevation Models (DEM) from OpenTopography / Open-Elevation.
    Computes terrain elevation (meters MSL) and local terrain slope gradient (degrees).
    Caches results in-memory to prevent repeated redundant elevation queries.
    """
    
    def __init__(self):
        self.api_key = settings.OPENTOPOGRAPHY_API_KEY
        self._cache: Dict[str, Tuple[float, float]] = {}

    def _cache_key(self, lat: float, lon: float) -> str:
        # Cache resolution ~1km (~0.01 deg)
        return f"{round(lat, 2)}_{round(lon, 2)}"

    async def get_terrain(self, latitude: float, longitude: float) -> TerrainData:
        key = self._cache_key(latitude, longitude)
        if key in self._cache:
            elev, slope = self._cache[key]
            return TerrainData(
                elevation=elev,
                slope=slope,
                provider="OpenTopography DEM Cache",
                is_fallback=False,
                status_note="Retrieved from cached digital elevation model."
            )

        # Attempt querying Open-Elevation or OpenTopography endpoints
        delta = 0.002  # ~220 meters
        coords = [
            {"latitude": latitude, "longitude": longitude},
            {"latitude": latitude + delta, "longitude": longitude},  # North
            {"latitude": latitude - delta, "longitude": longitude},  # South
            {"latitude": latitude, "longitude": longitude + delta},  # East
            {"latitude": latitude, "longitude": longitude - delta},  # West
        ]

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                resp = await client.post(
                    "https://api.open-elevation.com/api/v1/lookup",
                    json={"locations": coords}
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if len(results) == 5:
                        z_center = float(results[0]["elevation"])
                        z_north = float(results[1]["elevation"])
                        z_south = float(results[2]["elevation"])
                        z_east = float(results[3]["elevation"])
                        z_west = float(results[4]["elevation"])

                        dist_m = delta * 111320.0  # meters per degree approx
                        dz_dy = (z_north - z_south) / (2.0 * dist_m)
                        dz_dx = (z_east - z_west) / (2.0 * dist_m * math.cos(math.radians(latitude)))
                        gradient = math.sqrt(dz_dx**2 + dz_dy**2)
                        slope_deg = math.degrees(math.atan(gradient))
                        
                        elev_final = round(max(0.0, z_center), 1)
                        slope_final = round(min(89.0, max(0.0, slope_deg)), 1)
                        self._cache[key] = (elev_final, slope_final)

                        return TerrainData(
                            elevation=elev_final,
                            slope=slope_final,
                            provider="Open-Elevation / SRTM DEM",
                            is_fallback=False,
                            status_note="High-resolution digital elevation and slope gradient computed from DEM grid."
                        )
        except Exception as e:
            logger.warning(f"Live DEM query failed: {e}. Falling back to regional topographical heuristics.")

        # Fallback estimation based on known geomorphology if external DEM service is unreachable
        # Wayanad/Western Ghats ~11.5N, 76.0E -> 800-1400m, slope 25-35°
        # Northeast India / Himalayas ~25-28N, 91-94E -> 1200-2500m, slope 30-45°
        # Plains -> 100-300m, slope 2-6°
        elev_est = 450.0
        slope_est = 14.0

        if 8.0 <= latitude <= 15.0 and 74.0 <= longitude <= 77.5:
            # Western Ghats region
            elev_est = 980.0
            slope_est = 29.5
        elif 22.0 <= latitude <= 29.0 and 88.0 <= longitude <= 97.0:
            # Northeast Region / Eastern Himalayas
            elev_est = 1420.0
            slope_est = 34.0
        elif 29.0 <= latitude <= 36.0 and 74.0 <= longitude <= 81.0:
            # Western Himalayas (Uttarakhand / Himachal)
            elev_est = 1850.0
            slope_est = 37.0

        return TerrainData(
            elevation=elev_est,
            slope=slope_est,
            provider="Topographical Geomorphology (Fallback)",
            is_fallback=True,
            status_note="FALLBACK: Live DEM API timed out. Region geomorphological estimate used."
        )
