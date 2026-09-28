import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import (
    risk_router,
    demo_router,
    satellite_router,
    reports_router,
    model_router,
    multihazard_router,
    cap_router,
    auth_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
   
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-grade environmental risk intelligence engine. "
        "Integrates Open-Meteo, OpenTopography, NASA COOLR, NASA GIBS, and LightGBM machine learning models."
    ),
    lifespan=lifespan
)

# CORS Middleware (supports local dev and deployed Vercel frontends)
# Render/Vercel cross-origin support
origins = settings.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(multihazard_router, prefix=settings.API_PREFIX)
app.include_router(cap_router, prefix=settings.API_PREFIX)
app.include_router(risk_router, prefix=settings.API_PREFIX)
app.include_router(demo_router, prefix=settings.API_PREFIX)
app.include_router(satellite_router, prefix=settings.API_PREFIX)
app.include_router(reports_router, prefix=settings.API_PREFIX)
app.include_router(model_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)

@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check probe for Render or monitoring services."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": "production" if os.getenv("RENDER") else "development"
    }

# Static file serving for standalone single-server deployment / local preview
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"message": f"{settings.PROJECT_NAME} API Online. Visit /docs for OpenAPI specs."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
