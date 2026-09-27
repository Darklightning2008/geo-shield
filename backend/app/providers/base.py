from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.schemas import WeatherData, TerrainData, HistoricalData

class WeatherProvider(ABC):
    """Abstract interface for weather data providers."""
    
    @abstractmethod
    async def get_weather(self, latitude: float, longitude: float) -> WeatherData:
        """Fetch current & accumulated precipitation, soil moisture, and meteorological factors."""
        pass

class TerrainProvider(ABC):
    """Abstract interface for digital elevation and terrain morphology providers."""
    
    @abstractmethod
    async def get_terrain(self, latitude: float, longitude: float) -> TerrainData:
        """Fetch surface elevation in meters and compute slope gradient in degrees."""
        pass

class HistoricalProvider(ABC):
    """Abstract interface for historical landslide occurrence catalogs."""
    
    @abstractmethod
    async def get_historical_risk(self, latitude: float, longitude: float) -> HistoricalData:
        """Query historical landslide events catalog within regional radius."""
        pass

class SatelliteProvider(ABC):
    """Abstract interface for satellite visual imagery and meteorological sensor feeds."""
    
    @abstractmethod
    def get_satellite_layers(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Provide map tile layers, capabilities, and imagery metadata."""
        pass

    @abstractmethod
    async def get_numeric_satellite_features(self, latitude: float, longitude: float) -> Dict[str, float]:
        """Extract quantitative satellite bands (e.g. Brightness Temperature, Cloud Top Index)."""
        pass
