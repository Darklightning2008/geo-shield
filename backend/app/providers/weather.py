import math
import logging
import httpx
from typing import Optional
from app.providers.base import WeatherProvider
from app.schemas import WeatherData, AtmosphericPrecursors

logger = logging.getLogger(__name__)

class OpenMeteoProvider(WeatherProvider):
    """
    Live Weather & Atmospheric Precursor Provider using Open-Meteo ECMWF/GFS.
    Retrieves CAPE, precipitation, wind speeds, dew point, pressure, and surface soil moisture.
    Computes physical precursors specified in the Multi-Hazard Nowcasting Engine:
    (IWV, CAPE, CIN, Low-level Convergence, Wind Shear, CTT drop rate, QPE rate).
    """
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    async def get_weather(self, latitude: float, longitude: float) -> WeatherData:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": (
                "precipitation,soil_moisture_0_to_7cm,relative_humidity_2m,"
                "temperature_2m,dew_point_2m,surface_pressure,wind_speed_10m,wind_gusts_10m,cape"
            ),
            "daily": "precipitation_sum",
            "past_days": 3,
            "forecast_days": 1,
            "timezone": "auto"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    hourly = data.get("hourly", {})
                    precip_list = hourly.get("precipitation", [])
                    soil_moisture_list = hourly.get("soil_moisture_0_to_7cm", [])
                    temp_list = hourly.get("temperature_2m", [])
                    humidity_list = hourly.get("relative_humidity_2m", [])
                    dew_list = hourly.get("dew_point_2m", [])
                    press_list = hourly.get("surface_pressure", [])
                    wind_list = hourly.get("wind_speed_10m", [])
                    gust_list = hourly.get("wind_gusts_10m", [])
                    cape_list = hourly.get("cape", [])
                    
                    # Rolling precipitation sums
                    rainfall_24h = sum(float(p or 0.0) for p in precip_list[-24:])
                    rainfall_72h = sum(float(p or 0.0) for p in precip_list[-72:])

                    # Soil moisture %
                    raw_sm = 0.25
                    for sm in reversed(soil_moisture_list):
                        if sm is not None:
                            raw_sm = float(sm)
                            break
                    soil_moisture_pct = min(100.0, max(5.0, (raw_sm / 0.50) * 100.0))
                    
                    curr_temp = next((float(t) for t in reversed(temp_list) if t is not None), 24.0)
                    curr_hum = next((float(h) for h in reversed(humidity_list) if h is not None), 75.0)
                    curr_dew = next((float(d) for d in reversed(dew_list) if d is not None), curr_temp - 2.5)
                    curr_press = next((float(pr) for pr in reversed(press_list) if pr is not None), 1010.0)
                    curr_wind = next((float(w) for w in reversed(wind_list) if w is not None), 4.5)
                    curr_gust = next((float(g) for g in reversed(gust_list) if g is not None), curr_wind * 1.5)
                    curr_cape = next((float(c) for c in reversed(cape_list) if c is not None), 650.0)

                    return WeatherData(
                        rainfall_24h=round(rainfall_24h, 2),
                        rainfall_72h=round(rainfall_72h, 2),
                        soil_moisture=round(soil_moisture_pct, 1),
                        temperature_2m=round(curr_temp, 1),
                        relative_humidity=round(curr_hum, 1),
                        dew_point_2m=round(curr_dew, 1),
                        surface_pressure=round(curr_press, 1),
                        wind_speed_10m=round(curr_wind, 1),
                        wind_gusts_10m=round(curr_gust, 1),
                        cape=round(curr_cape, 1),
                        provider="Open-Meteo (Live ECMWF/GFS)",
                        is_fallback=False,
                        status_note="Live atmospheric telemetry and convective indices acquired."
                    )
                else:
                    logger.warning(f"Open-Meteo returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"Live weather query timed out/failed: {e}. Engaging regional fallback.")
        
        # Conservative fallback
        return WeatherData(
            rainfall_24h=14.0,
            rainfall_72h=32.0,
            soil_moisture=52.0,
            temperature_2m=26.5,
            relative_humidity=78.0,
            dew_point_2m=22.5,
            surface_pressure=1008.0,
            wind_speed_10m=5.0,
            wind_gusts_10m=9.0,
            cape=750.0,
            provider="Open-Meteo (Regional Baseline)",
            is_fallback=True,
            status_note="Regional baseline values applied."
        )

    @staticmethod
    def extract_precursors(weather: WeatherData, slope: float, elevation: float) -> AtmosphericPrecursors:
        """
        Derives the 3 essential convective ingredients from PDF:
        1. MOISTURE: IWV (Integrated Water Vapour), QPE rate
        2. INSTABILITY: CAPE (energy), CIN (lid), CTT drop rate
        3. LIFT: Low-level convergence, Wind Shear
        """
        t = weather.temperature_2m or 25.0
        td = weather.dew_point_2m or (t - 2.5)
        p = weather.surface_pressure or 1010.0
        rh = weather.relative_humidity or 75.0
        wind = weather.wind_speed_10m or 4.0
        gust = weather.wind_gusts_10m or (wind * 1.4)
        cape = weather.cape or 500.0

        # 1. Integrated Water Vapour (IWV in mm):
        # Actual vapor pressure e (hPa) via Magnus formula
        e = 6.112 * math.exp((17.67 * td) / (td + 243.5))
        # Specific humidity q (kg/kg)
        q = 0.622 * (e / (p - 0.378 * e))
        # Column integrated water vapor approximation (mm)
        iwv = max(10.0, min(95.0, q * 1000.0 * 3.3))

        # 2. Convective Inhibition (CIN in J/kg):
        # CIN represents the boundary layer lid. When rh is high and t-td is small, CIN weakens.
        temp_deficit = max(0.0, t - td)
        cin = -1.0 * min(250.0, max(5.0, temp_deficit * 22.0 + (100.0 - rh) * 1.5))

        # 3. Low-Level Convergence (10^-5 s^-1):
        # Surface friction and terrain deceleration force upward lift
        convergence = round(max(0.5, (wind / 3.0) * (1.0 + min(1.5, slope / 20.0))), 2)

        # 4. Vertical Wind Shear (m/s):
        # Difference between surface wind and upper troposphere gust potential
        wind_shear = round(max(1.0, abs(gust - wind) * 1.8), 1)

        # 5. Cloud Top Temperature Drop Rate (°C/hr):
        # Explosive vertical updraft w ~ sqrt(2 * CAPE).
        # When CAPE is high, clouds shoot upward into freezing upper troposphere rapidly.
        updraft_speed = math.sqrt(2.0 * max(0.0, cape))
        ctt_drop = round(min(35.0, (updraft_speed / 45.0) * 18.0 + (rh / 100.0) * 8.0), 1)

        # 6. Quantitative Precipitation Estimation instant rate (mm/hr):
        qpe_instant = round(weather.rainfall_24h / 8.0 if weather.rainfall_24h > 15 else weather.rainfall_24h / 24.0, 1)

        return AtmosphericPrecursors(
            iwv=round(iwv, 1),
            cape=round(cape, 1),
            cin=round(cin, 1),
            low_level_convergence=convergence,
            wind_shear=wind_shear,
            ctt_drop_rate=ctt_drop,
            qpe_rate=qpe_instant,
            soil_saturation=round(weather.soil_moisture, 1),
            slope_angle=round(slope, 1)
        )

class IMDAAProvider(WeatherProvider):
    async def get_weather(self, latitude: float, longitude: float) -> WeatherData:
        raise NotImplementedError("IMDAAProvider is reserved for future integration with NCMRWF/IMD reanalysis.")
