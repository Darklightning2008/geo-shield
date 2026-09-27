from typing import List, Dict, Any
from app.schemas import DemoEscalationStep, RiskAssessmentResponse, WeatherData, TerrainData, HistoricalData
from app.services.risk_engine import risk_engine

class DemoService:
    """
    Scripted Severe-Weather Escalation Replay Service.
    Demonstrates model reactivity under escalating meteorological crisis conditions:
    (moisture ↑ → instability ↑ → precipitation ↑ → flash flood / landslide risk ↑ → HIGH ALERT)
    Unambiguously isolates demo scenarios with DEMO SCENARIO metadata.
    """

    SCENARIO_LOCATION = {
        "name": "Wayanad Escarpment Corridor (Demo Scenario)",
        "latitude": 11.5300,
        "longitude": 76.1300,
        "elevation": 1150.0,
        "slope": 36.5,
        "historical_count": 8
    }

    SCRIPTED_STEPS: List[Dict[str, Any]] = [
        {
            "step_number": 1,
            "title": "Stage 1: Pre-Monsoon Ambient Conditions",
            "stage_name": "Normal Baseline",
            "description": "Stable seasonal conditions. Dry soil profile, negligible 24h precipitation, and sound retaining stability.",
            "rainfall_24h": 0.0,
            "rainfall_72h": 2.5,
            "soil_moisture": 28.0,
            "temperature_2m": 27.5,
            "relative_humidity": 45.0
        },
        {
            "step_number": 2,
            "title": "Stage 2: Tropical Depression Influx (Moisture ↑)",
            "stage_name": "Moisture Surge",
            "description": "Depression in Bay of Bengal / Arabian Sea sweeps moisture inland. Relative humidity spikes, continuous light showers begin.",
            "rainfall_24h": 32.0,
            "rainfall_72h": 48.0,
            "soil_moisture": 62.0,
            "temperature_2m": 24.0,
            "relative_humidity": 78.0
        },
        {
            "step_number": 3,
            "title": "Stage 3: Orographic Cloudburst & Soil Saturation (Instability ↑)",
            "stage_name": "Subsoil Saturation",
            "description": "Persistent torrential squalls hit the mountain escarpment. Subsoil moisture reaches critical absorption capacity.",
            "rainfall_24h": 98.0,
            "rainfall_72h": 165.0,
            "soil_moisture": 84.0,
            "temperature_2m": 21.5,
            "relative_humidity": 92.0
        },
        {
            "step_number": 4,
            "title": "Stage 4: Extreme Continuous Downpour (Precipitation ↑)",
            "stage_name": "Torrential Deluge",
            "description": "Severe weather event. High pore water pressure builds beneath soil mantle. Minor tension cracks and runoff rivulets form.",
            "rainfall_24h": 195.0,
            "rainfall_72h": 310.0,
            "soil_moisture": 94.0,
            "temperature_2m": 19.8,
            "relative_humidity": 98.0
        },
        {
            "step_number": 5,
            "title": "Stage 5: Critical Threshold Breach (Landslide Risk ↑ → HIGH ALERT)",
            "stage_name": "Slope Failure Imminent",
            "description": "Catastrophic threshold reached. Complete volumetric liquefaction on 36.5° slope. Debris flow and flash mudslide imminent. High Alert.",
            "rainfall_24h": 285.0,
            "rainfall_72h": 460.0,
            "soil_moisture": 99.5,
            "temperature_2m": 18.5,
            "relative_humidity": 100.0
        }
    ]

    def get_all_demo_steps(self) -> List[DemoEscalationStep]:
        results: List[DemoEscalationStep] = []
        loc = self.SCENARIO_LOCATION

        for item in self.SCRIPTED_STEPS:
            ml_prob = risk_engine.predict_ml_probability(
                rainfall_24h=item["rainfall_24h"],
                rainfall_72h=item["rainfall_72h"],
                soil_moisture=item["soil_moisture"],
                slope=loc["slope"],
                elevation=loc["elevation"],
                historical_count=loc["historical_count"]
            )
            baseline = risk_engine.calculate_rule_based_baseline(
                rainfall_24h=item["rainfall_24h"],
                rainfall_72h=item["rainfall_72h"],
                soil_moisture=item["soil_moisture"],
                slope=loc["slope"],
                elevation=loc["elevation"],
                historical_count=loc["historical_count"]
            )
            risk_level, color = risk_engine.determine_risk_level(ml_prob)

            results.append(DemoEscalationStep(
                step_number=item["step_number"],
                title=item["title"],
                stage_name=item["stage_name"],
                description=item["description"],
                rainfall_24h=item["rainfall_24h"],
                rainfall_72h=item["rainfall_72h"],
                soil_moisture=item["soil_moisture"],
                slope=loc["slope"],
                elevation=loc["elevation"],
                historical_count=loc["historical_count"],
                ml_probability=round(ml_prob, 4),
                baseline_risk_score=round(baseline, 4),
                risk_level=risk_level,
                alert_color=color,
                is_demo=True,
                mode_label="DEMO SCENARIO"
            ))

        return results

    def get_step_assessment(self, step_number: int) -> RiskAssessmentResponse:
        clamped_step = max(1, min(len(self.SCRIPTED_STEPS), step_number))
        step_data = self.SCRIPTED_STEPS[clamped_step - 1]
        loc = self.SCENARIO_LOCATION

        weather = WeatherData(
            rainfall_24h=step_data["rainfall_24h"],
            rainfall_72h=step_data["rainfall_72h"],
            soil_moisture=step_data["soil_moisture"],
            temperature_2m=step_data["temperature_2m"],
            relative_humidity=step_data["relative_humidity"],
            provider="Scripted Severe Weather Simulation (Demo Mode)",
            is_fallback=False,
            status_note=f"DEMO SCENARIO: Step {clamped_step} of 5 - {step_data['stage_name']}"
        )

        terrain = TerrainData(
            elevation=loc["elevation"],
            slope=loc["slope"],
            provider="Wayanad Escarpment Profile (Demo Mode)",
            is_fallback=False,
            status_note="Calibrated test terrain model."
        )

        history = HistoricalData(
            historical_landslide_count=loc["historical_count"],
            catalog_source="NASA COOLR Western Ghats Catalog",
            notable_events=["Meppadi-Chooralmala 2024 Historical Escarpment Surge"],
            is_fallback=False
        )

        assessment = risk_engine.assess_risk(
            latitude=loc["latitude"],
            longitude=loc["longitude"],
            location_name=f"{loc['name']} [Step {clamped_step}: {step_data['stage_name']}]",
            weather=weather,
            terrain=terrain,
            history=history,
            is_demo=True
        )

        return assessment

demo_service = DemoService()
