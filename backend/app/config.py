import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "GeoShield - Landslide & Disaster Risk Early Warning Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Origins allowed for CORS (Local development + Vercel deployment preview / prod)
    ALLOWED_ORIGINS_RAW: str = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:8000,http://localhost:8000"
    )
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        origins = [o.strip() for o in self.ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
        if "*" not in origins and "https://*.vercel.app" in origins:
            # Allow origin regex or wildcard matching in FastAPI middleware
            pass
        return origins

    # External APIs
    OPENTOPOGRAPHY_API_KEY: str = os.getenv("OPENTOPOGRAPHY_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/landslide_risk.db")
    
    # ML Model Path
    MODEL_PATH: Path = BASE_DIR / os.getenv("MODEL_PATH", "ml/risk_model.pkl")

settings = Settings()
