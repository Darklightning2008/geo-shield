from app.routers.risk import router as risk_router
from app.routers.demo import router as demo_router
from app.routers.satellite import router as satellite_router
from app.routers.reports import router as reports_router
from app.routers.model import router as model_router
from app.routers.multihazard import router as multihazard_router, cap_router
from app.routers.auth import router as auth_router

__all__ = [
    "risk_router",
    "demo_router",
    "satellite_router",
    "reports_router",
    "model_router",
    "multihazard_router",
    "cap_router",
    "auth_router"
]

