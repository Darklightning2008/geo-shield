import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib

from app.config import settings
from app.schemas import (
    WeatherData, TerrainData, HistoricalData,
    ContributingFactor, RiskAssessmentResponse
)

logger = logging.getLogger(__name__)

class RiskEngine:
    """
    Core Risk Prediction and Heuristic Baseline Engine.
    Executes LightGBM model inference alongside a transparent rule-based physical baseline.
    Produces human-interpretable factor attributions without false claims of black-box SHAP certainty.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.model = None
        self.feature_columns = [
            "rainfall_24h", "rainfall_72h", "soil_moisture",
            "slope", "elevation", "historical_landslide_count"
        ]
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                if isinstance(data, dict) and "model" in data:
                    self.model = data["model"]
                    self.feature_columns = data.get("feature_columns", self.feature_columns)
                else:
                    self.model = data
                logger.info(f"Loaded ML model successfully from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load model from {self.model_path}: {e}. Baseline only mode active.")
                self.model = None
        else:
            logger.warning(f"Model file not found at {self.model_path}. Running with rule-based baseline.")
            self.model = None

    def calculate_rule_based_baseline(
        self,
        rainfall_24h: float,
        rainfall_72h: float,
        soil_moisture: float,
        slope: float,
        elevation: float,
        historical_count: int
    ) -> float:
        """
        Transparent, physics-informed empirical heuristic:
        Weights:
        - 35% 24-hour antecedent rainfall (scaled to 300mm max)
        - 15% 72-hour cumulative saturation (scaled to 500mm max)
        - 20% soil moisture volumetric percentage (0-100%)
        - 20% terrain slope gradient (scaled to 60° critical angle)
        - 10% historical regional incidence frequency (scaled to 10 events)
        """
        score = (
            0.35 * min(1.0, max(0.0, rainfall_24h / 300.0))
            + 0.15 * min(1.0, max(0.0, rainfall_72h / 500.0))
            + 0.20 * min(1.0, max(0.0, soil_moisture / 100.0))
            + 0.20 * min(1.0, max(0.0, slope / 60.0))
            + 0.10 * min(1.0, max(0.0, historical_count / 10.0))
        )
        return round(float(np.clip(score, 0.0, 1.0)), 4)

    def predict_ml_probability(
        self,
        rainfall_24h: float,
        rainfall_72h: float,
        soil_moisture: float,
        slope: float,
        elevation: float,
        historical_count: int
    ) -> float:
        """Runs inference against LightGBM model if available; else falls back to baseline."""
        if self.model is None:
            return self.calculate_rule_based_baseline(
                rainfall_24h, rainfall_72h, soil_moisture, slope, elevation, historical_count
            )

        features = pd.DataFrame([{
            "rainfall_24h": float(rainfall_24h),
            "rainfall_72h": float(rainfall_72h),
            "soil_moisture": float(soil_moisture),
            "slope": float(slope),
            "elevation": float(elevation),
            "historical_landslide_count": int(historical_count)
        }])[self.feature_columns]

        try:
            probabilities = self.model.predict_proba(features)
            # Probability of landslide class (index 1)
            prob = float(probabilities[0][1])
            return round(prob, 4)
        except Exception as e:
            logger.error(f"ML inference error: {e}. Falling back to baseline.")
            return self.calculate_rule_based_baseline(
                rainfall_24h, rainfall_72h, soil_moisture, slope, elevation, historical_count
            )

    def determine_risk_level(self, risk_score: float) -> tuple[str, str]:
        """Maps probabilistic risk score to categorical level and UI color token."""
        if risk_score >= 0.75:
            return "Critical", "#ef4444"  # Red
        elif risk_score >= 0.50:
            return "High", "#f97316"      # Orange
        elif risk_score >= 0.25:
            return "Moderate", "#f59e0b"  # Yellow
        else:
            return "Low", "#10b981"       # Green

    def compute_factor_breakdown(
        self,
        rainfall_24h: float,
        rainfall_72h: float,
        soil_moisture: float,
        slope: float,
        elevation: float,
        historical_count: int
    ) -> List[ContributingFactor]:
        """Provides factor contributions based on empirical physical sensitivity."""
        f_rain24 = min(1.0, rainfall_24h / 150.0)
        f_rain72 = min(1.0, rainfall_72h / 250.0)
        f_soil = min(1.0, soil_moisture / 90.0)
        f_slope = min(1.0, slope / 45.0)
        f_hist = min(1.0, historical_count / 8.0)

        return [
            ContributingFactor(
                factor="24h Precipitation Intensity",
                value=round(rainfall_24h, 1),
                unit="mm",
                contribution_weight=round(f_rain24, 2),
                description=f"Direct surface runoff and pore pressure trigger ({round(rainfall_24h, 1)} mm)."
            ),
            ContributingFactor(
                factor="72h Antecedent Rainfall",
                value=round(rainfall_72h, 1),
                unit="mm",
                contribution_weight=round(f_rain72, 2),
                description=f"Multi-day saturation weakening subsoil shear strength ({round(rainfall_72h, 1)} mm)."
            ),
            ContributingFactor(
                factor="Soil Moisture Saturation",
                value=round(soil_moisture, 1),
                unit="%",
                contribution_weight=round(f_soil, 2),
                description=f"Volumetric water retention near surface ({round(soil_moisture, 1)}%)."
            ),
            ContributingFactor(
                factor="Terrain Slope Gradient",
                value=round(slope, 1),
                unit="°",
                contribution_weight=round(f_slope, 2),
                description=f"Gravitational driving force on hillside incline ({round(slope, 1)}°)."
            ),
            ContributingFactor(
                factor="Historical Landslide Incidence",
                value=float(historical_count),
                unit="events",
                contribution_weight=round(f_hist, 2),
                description=f"Geological predisposition from past catalog records ({historical_count} recorded)."
            )
        ]

    def generate_advisory(self, risk_level: str, rainfall_24h: float, slope: float) -> tuple[str, List[str]]:
        if risk_level == "Critical":
            advisory = (
                "EMERGENCY ALERT: High probability of immediate slope failure, debris flows, or flash mudslides. "
                "Extreme soil saturation coupled with critical terrain gradient."
            )
            actions = [
                "Evacuate vulnerable downhill dwellings and identified talus zones immediately.",
                "Avoid mountain transit corridors, ghat roads, and underpasses.",
                "Monitor emergency disaster response broadcasts (NDRF / SDRF).",
                "Report visible ground fissures or muddy spring discharge immediately."
            ]
        elif risk_level == "High":
            advisory = (
                "WARNING: Environmental conditions indicate high susceptibility to localized landslides, "
                "rockfalls, and drainage blockages within the next 12-24 hours."
            )
            actions = [
                "Restrict movement on steep hillside slopes (>25°).",
                "Ensure municipal storm water channels and culverts remain unblocked.",
                "Prepare emergency go-bags with essentials and first aid.",
                "Keep continuous watch on slope stability and retaining walls."
            ]
        elif risk_level == "Moderate":
            advisory = (
                "ADVISORY: Elevated antecedent rainfall detected. Terrain stability requires heightened situational awareness."
            )
            actions = [
                "Inspect retaining structures and roadside cuts for signs of weeping or displacement.",
                "Check regional meteorological forecast updates regularly.",
                "Refrain from camping or parking vehicles directly beneath steep embankments."
            ]
        else:
            advisory = (
                "NORMAL: Environmental conditions within manageable thresholds. Low estimated slope instability."
            )
            actions = [
                "Standard seasonal monitoring routine.",
                "Maintain functional hillside drainage systems.",
                "Report unusual ground shifts or retaining wall cracks if observed."
            ]

        return advisory, actions

    def assess_risk(
        self,
        latitude: float,
        longitude: float,
        location_name: str,
        weather: WeatherData,
        terrain: TerrainData,
        history: HistoricalData,
        is_demo: bool = False
    ) -> RiskAssessmentResponse:
        """Aggregates all components into an honest, fully transparent risk evaluation."""
        
        ml_prob = self.predict_ml_probability(
            rainfall_24h=weather.rainfall_24h,
            rainfall_72h=weather.rainfall_72h,
            soil_moisture=weather.soil_moisture,
            slope=terrain.slope,
            elevation=terrain.elevation,
            historical_count=history.historical_landslide_count
        )

        baseline = self.calculate_rule_based_baseline(
            rainfall_24h=weather.rainfall_24h,
            rainfall_72h=weather.rainfall_72h,
            soil_moisture=weather.soil_moisture,
            slope=terrain.slope,
            elevation=terrain.elevation,
            historical_count=history.historical_landslide_count
        )

        # Use model probability for primary level categorization
        primary_score = ml_prob
        risk_level, color = self.determine_risk_level(primary_score)
        
        factors = self.compute_factor_breakdown(
            weather.rainfall_24h,
            weather.rainfall_72h,
            weather.soil_moisture,
            terrain.slope,
            terrain.elevation,
            history.historical_landslide_count
        )

        advisory, actions = self.generate_advisory(risk_level, weather.rainfall_24h, terrain.slope)

        mode_label = "DEMO SCENARIO" if is_demo else "LIVE DATA ASSESSMENT"

        return RiskAssessmentResponse(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            ml_probability=round(ml_prob, 4),
            baseline_risk_score=round(baseline, 4),
            risk_level=risk_level,
            alert_color=color,
            weather=weather,
            terrain=terrain,
            history=history,
            primary_factors=factors,
            advisory=advisory,
            recommended_actions=actions,
            is_demo=is_demo,
            mode_label=mode_label
        )

# Singleton instance
risk_engine = RiskEngine()
