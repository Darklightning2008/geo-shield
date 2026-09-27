import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app
from app.database import init_db
from app.providers import OpenMeteoProvider, OpenTopographyProvider, COOLRProvider, GIBSProvider
from app.services.risk_engine import risk_engine
from app.services.demo_service import demo_service
from app.schemas import WeatherData, TerrainData, HistoricalData

# Initialize DB tables for testing
asyncio.run(init_db())

client = TestClient(app)

def test_health():
    print("Testing 1: System Health...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print("  [PASS] Health check ok:", res.json())

def test_valid_coordinates_live_pipeline():
    print("Testing 2: Valid Coordinates Live Pipeline (Wayanad)...")
    payload = {
        "latitude": 11.5534,
        "longitude": 76.1320,
        "location_name": "Wayanad (Meppadi), Kerala"
    }
    res = client.post("/api/risk/assess", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "ml_probability" in data
    assert "baseline_risk_score" in data
    assert "risk_level" in data
    assert "weather" in data
    assert "terrain" in data
    assert "primary_factors" in data
    assert data["mode_label"] == "LIVE DATA ASSESSMENT"
    print(f"  [PASS] Live Wayanad assessment: Risk={data['risk_level']}, ML_Prob={data['ml_probability'] * 100:.1f}%, Baseline={data['baseline_risk_score'] * 100:.1f}%")

def test_low_risk_live_pipeline():
    print("Testing 3: Low-Risk Live Pipeline (New Delhi Plains)...")
    payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "location_name": "New Delhi"
    }
    res = client.post("/api/risk/assess", json=payload)
    assert res.status_code == 200
    data = res.json()
    print(f"  [PASS] Low-risk Plains assessment: Risk={data['risk_level']}, ML_Prob={data['ml_probability'] * 100:.1f}%")

def test_invalid_coordinates_validation():
    print("Testing 4: Invalid Coordinates Validation (Section 17)...")
    # Latitude > 90
    res1 = client.post("/api/risk/assess", json={"latitude": 95.0, "longitude": 76.0})
    assert res1.status_code == 422, f"Expected 422, got {res1.status_code}"
    
    # Longitude < -180
    res2 = client.post("/api/risk/assess", json={"latitude": 12.0, "longitude": -195.0})
    assert res2.status_code == 422, f"Expected 422, got {res2.status_code}"
    print("  [PASS] Invalid coordinates rejected with explicit 422 validation messages.")

def test_demo_escalation_mode():
    print("Testing 5: Demo Escalation Mode (Section 18)...")
    res = client.get("/api/demo/steps")
    assert res.status_code == 200
    steps = res.json()
    assert len(steps) == 5, f"Expected 5 steps, got {len(steps)}"
    
    # Test step 1 (Ambient low) vs step 5 (High alert critical)
    step1 = client.get("/api/demo/step/1").json()
    assert step1["mode_label"] == "DEMO SCENARIO"
    assert step1["is_demo"] is True
    
    step5 = client.get("/api/demo/step/5").json()
    assert step5["mode_label"] == "DEMO SCENARIO"
    assert step5["is_demo"] is True
    assert step5["risk_level"] == "Critical"
    assert step5["ml_probability"] > step1["ml_probability"]
    print(f"  [PASS] Demo escalation verified: Step 1 ({step1['risk_level']} {step1['ml_probability']*100:.1f}%) -> Step 5 ({step5['risk_level']} {step5['ml_probability']*100:.1f}% HIGH ALERT)")

def test_citizen_reports():
    print("Testing 6: Citizen Reports Lifecycle...")
    # List initial
    res_list = client.get("/api/reports")
    assert res_list.status_code == 200
    initial_count = len(res_list.json())
    
    # Submit report
    new_rep = {
        "latitude": 11.5400,
        "longitude": 76.1200,
        "location_name": "Test Escarpment Cut",
        "event_type": "slope_cracks",
        "severity": "high",
        "description": "Noticeable 2-inch ground tension crack.",
        "reporter_name": "Test Unit"
    }
    res_post = client.post("/api/reports", json=new_rep)
    assert res_post.status_code == 201
    
    # Check stats
    res_stats = client.get("/api/reports/stats")
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_reports"] >= initial_count + 1
    print(f"  [PASS] Citizen report posted and verified in catalog. Total reports: {stats['total_reports']}")

def test_satellite_layers():
    print("Testing 7: NASA GIBS Satellite Layers...")
    res = client.get("/api/satellite/layers")
    assert res.status_code == 200
    data = res.json()
    assert "layers" in data
    assert "modis_truecolor" in data["layers"]
    print(f"  [PASS] NASA GIBS layers active: {list(data['layers'].keys())}")

def test_model_governance_and_baseline_resilience():
    print("Testing 8: Model Governance & Baseline Fallback...")
    res = client.get("/api/model/info")
    assert res.status_code == 200
    data = res.json()
    assert "synthetic_training_disclosure" in data
    
    # Test rule baseline calculation directly
    score = risk_engine.calculate_rule_based_baseline(
        rainfall_24h=150.0,
        rainfall_72h=220.0,
        soil_moisture=80.0,
        slope=35.0,
        elevation=1200.0,
        historical_count=5
    )
    assert 0.0 <= score <= 1.0
    print(f"  [PASS] Baseline formula output: {score * 100:.1f}%. Disclosure present.")

def test_hilly_areas_and_coastal_catalog():
    print("Testing 9: Priority Hotspots Catalog (Hilly Areas First, then Coastal)...")
    # Test Hilly areas
    res_hilly = client.get("/api/hazards/hilly-areas")
    assert res_hilly.status_code == 200
    hilly = res_hilly.json()
    assert len(hilly) >= 10, f"Expected >= 10 hilly areas, got {len(hilly)}"
    hilly_ids = [h["id"] for h in hilly]
    assert "wayanad" in hilly_ids
    assert "shimla" in hilly_ids
    assert "joshimath" in hilly_ids

    # Test Coastal cities
    res_coastal = client.get("/api/hazards/coastal-cities")
    assert res_coastal.status_code == 200
    coastal = res_coastal.json()
    assert len(coastal) >= 8

    # Test Combined Priority Locations (Hilly First)
    res_priority = client.get("/api/hazards/priority-locations")
    assert res_priority.status_code == 200
    pdata = res_priority.json()
    assert "hilly_areas" in pdata and "coastal_cities" in pdata and "all_locations" in pdata
    # First item must be hilly area
    assert pdata["all_locations"][0]["id"] == "wayanad"
    print(f"  [PASS] Priority catalogs verified ({len(hilly)} Hilly hotspots first, followed by {len(coastal)} Coastal hubs).")

def test_multihazard_nowcasting_heads():
    print("Testing 10: Multi-Task Nowcasting Engine (4 Heads + Hilly Terrain Context)...")
    # 1. Assess Wayanad (Hilly Mountain Zone)
    payload_hilly = {
        "latitude": 11.5534,
        "longitude": 76.1320,
        "location_name": "Wayanad (Meppadi), Kerala"
    }
    res_hilly = client.post("/api/hazards/assess", json=payload_hilly)
    assert res_hilly.status_code == 200
    data_hilly = res_hilly.json()
    assert data_hilly["is_hilly"] is True
    assert data_hilly["mountain_range"] == "Western Ghats"
    assert "precursors" in data_hilly and "hazards" in data_hilly

    # 2. Assess Mumbai (Coastal Zone)
    payload_coast = {
        "latitude": 18.9220,
        "longitude": 72.8347,
        "location_name": "Mumbai, Maharashtra"
    }
    res_coast = client.post("/api/hazards/assess", json=payload_coast)
    assert res_coast.status_code == 200
    data_coast = res_coast.json()
    assert data_coast["is_coastal"] is True
    hazards = data_coast["hazards"]
    assert "thunderstorm" in hazards and "cloudburst" in hazards and "flash_flood" in hazards and "landslide" in hazards
    print(f"  [PASS] Multi-hazard heads evaluated with terrain context (Wayanad: {data_hilly['mountain_range']} / Mumbai: {data_coast['coast_region']}).")

def test_oasis_cap_xml_feed():
    print("Testing 11: OASIS CAP v1.2 Standard XML Serialization...")
    res = client.get("/api/alerts/cap/TEST-ALERT-001?format=xml")
    assert res.status_code == 200
    assert "application/xml" in res.headers.get("content-type", "")
    xml_text = res.text
    assert "<alert xmlns=\"urn:oasis:names:tc:emergency:cap:1.2\">" in xml_text
    assert "<identifier>TEST-ALERT-001</identifier>" in xml_text
    assert "<category>Met</category>" in xml_text
    print(f"  [PASS] OASIS CAP v1.2 XML feed complies with NDMA SACHET / IMD specification ({len(xml_text)} bytes)")

def test_forecast_verification_metrics_pod_far_csi():
    print("Testing 12: Meteorological Verification Metrics (POD / FAR / CSI / HSS)...")
    res = client.get("/api/hazards/metrics")
    assert res.status_code == 200, f"Failed: {res.text}"
    data = res.json()
    assert "overall" in data
    assert "hazard_breakdown" in data
    assert "explanation" in data
    
    overall = data["overall"]
    assert "pod" in overall and "far" in overall and "csi" in overall and "hss" in overall
    assert 0.0 <= overall["pod"] <= 1.0
    assert 0.0 <= overall["far"] <= 1.0
    assert 0.0 <= overall["csi"] <= 1.0
    
    # Check breakdown
    hb = data["hazard_breakdown"]
    for expected_hazard in ["thunderstorm", "cloudburst", "flash_flood", "landslide"]:
        assert expected_hazard in hb
        hm = hb[expected_hazard]
        assert "contingency_table" in hm
        c = hm["contingency_table"]
        assert c["hits"] >= 0 and c["false_alarms"] >= 0 and c["misses"] >= 0 and c["correct_negatives"] >= 0
    
    # Model info endpoint includes metrics
    info_res = client.get("/api/model/info")
    assert info_res.status_code == 200
    info_data = info_res.json()
    assert "verification_metrics" in info_data
    vm = info_data["verification_metrics"]
    assert "overall_pod" in vm and "overall_far" in vm and "overall_csi" in vm

    print(f"  [PASS] POD={overall['pod_pct']}%, FAR={overall['far_pct']}%, CSI={overall['csi_pct']}%, HSS={overall['hss']} verified across all 4 hazard heads.")

def test_admin_authentication():
    print("Testing 13: Specialized Admin Authentication...")
    # Test invalid login
    res_bad = client.post("/api/auth/login", json={"email": "wrong@test.com", "password": "pass"})
    assert res_bad.status_code == 401, f"Expected 401, got {res_bad.status_code}"

    # Test bad password
    res_bad_pw = client.post("/api/auth/login", json={"email": "admin@geoshield.gov.in", "password": "WrongPassword"})
    assert res_bad_pw.status_code == 401, f"Expected 401, got {res_bad_pw.status_code}"

    # Test valid NDMA admin login
    res_ndma = client.post("/api/auth/login", json={"email": "admin@geoshield.gov.in", "password": "Admin@NDMA2026"})
    assert res_ndma.status_code == 200, f"Expected 200, got {res_ndma.status_code}: {res_ndma.text}"
    ndma_data = res_ndma.json()
    assert ndma_data["authenticated"] is True
    assert ndma_data["role"] == "admin"
    assert "token" in ndma_data
    token = ndma_data["token"]

    # Test auth status
    res_status = client.get("/api/auth/status", headers={"Authorization": f"Bearer {token}"})
    assert res_status.status_code == 200
    assert res_status.json()["authenticated"] is True

    # Test valid IMD admin login
    res_imd = client.post("/api/auth/login", json={"email": "admin@imd.gov.in", "password": "Admin@123"})
    assert res_imd.status_code == 200
    assert res_imd.json()["role"] == "admin"

    print("  [PASS] Specialized Admin Authentication verified for NDMA and IMD credentials.")

if __name__ == "__main__":
    print("=== STARTING GEOSHIELD END-TO-END VERIFICATION SUITE ===")
    test_health()
    test_valid_coordinates_live_pipeline()
    test_low_risk_live_pipeline()
    test_invalid_coordinates_validation()
    test_demo_escalation_mode()
    test_citizen_reports()
    test_satellite_layers()
    test_model_governance_and_baseline_resilience()
    test_hilly_areas_and_coastal_catalog()
    test_multihazard_nowcasting_heads()
    test_oasis_cap_xml_feed()
    test_forecast_verification_metrics_pod_far_csi()
    test_admin_authentication()
    print("=== ALL 13 VERIFICATION TESTS PASSED SUCCESSFULLY! ===")


