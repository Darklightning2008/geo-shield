#!/usr/bin/env python3
"""
GeoShield Disaster Risk Platform — Quick Launcher
Runs the backend on http://127.0.0.1:8000/ with interactive dashboard and OpenAPI documentation.
"""
import os
import sys
import webbrowser
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    print("=" * 70)
    print("  GeoShield: AI Landslide & Meteorological Early Warning Platform")
    print("=" * 70)
    print("  * Dashboard UI:  http://127.0.0.1:8000/")
    print("  * OpenAPI Docs:  http://127.0.0.1:8000/docs")
    print("  * Health Probe:  http://127.0.0.1:8000/api/health")
    print("=" * 70)
    
    import uvicorn
    from main import app

    # Automatically launch web browser
    try:
        webbrowser.open("http://127.0.0.1:8000/")
    except Exception:
        pass

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, app_dir=str(BASE_DIR))
