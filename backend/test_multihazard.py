import urllib.request
import json

base = "http://127.0.0.1:8000"

print("--- TESTING MULTI-HAZARD COASTAL SYSTEM ---")

# 1. Coastal cities
with urllib.request.urlopen(f"{base}/api/hazards/coastal-cities") as r:
    cities = json.loads(r.read().decode())
    print(f"1. Coastal cities loaded: {len(cities)}")
    for c in cities:
        print(f"   - {c['name']} ({c['coast']})")

# 2. Assess Mumbai
req_data = json.dumps({"latitude": 18.9220, "longitude": 72.8347, "location_name": "Mumbai, Maharashtra"}).encode()
req = urllib.request.Request(f"{base}/api/hazards/assess", data=req_data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    mumbai_res = json.loads(r.read().decode())
    print("\n2. Mumbai Assessment Results:")
    print("   Dominant Hazard:", mumbai_res["highest_risk_hazard"])
    print("   Overall Alert Level:", mumbai_res["overall_alert_level"])
    print("   Atmospheric Precursors:", mumbai_res["precursors"])
    print("   Multi-Task Output Heads:")
    for h_type, h_val in mumbai_res["hazards"].items():
        print(f"     * {h_val['hazard_title']}: {int(h_val['probability']*100)}% ({h_val['risk_level']}) - {h_val['primary_warning_sign']}")
    
    cap = mumbai_res.get("cap_alert")
    if cap:
        print("\n3. OASIS CAP v1.2 Alert:")
        print("   Identifier:", cap["identifier"])
        print("   Headline:", cap["headline"])
        # Fetch CAP XML feed
        with urllib.request.urlopen(f"{base}{cap['cap_xml_url']}") as xr:
            xml_text = xr.read().decode()
            print(f"   CAP XML Feed Verified ({len(xml_text)} bytes):")
            for line in xml_text.splitlines()[:15]:
                print("     " + line)

# 3. Assess Kozhikode (Western Ghats coastal gateway)
req_data2 = json.dumps({"latitude": 11.2588, "longitude": 75.7804, "location_name": "Kozhikode, Kerala"}).encode()
req2 = urllib.request.Request(f"{base}/api/hazards/assess", data=req_data2, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req2) as r2:
    kozhi_res = json.loads(r2.read().decode())
    print("\n4. Kozhikode Assessment Results:")
    print("   Dominant Hazard:", kozhi_res["highest_risk_hazard"])
    print("   Overall Alert Level:", kozhi_res["overall_alert_level"])
    print("   Atmospheric Precursors:", kozhi_res["precursors"])
    for h_type, h_val in kozhi_res["hazards"].items():
        print(f"     * {h_val['hazard_title']}: {int(h_val['probability']*100)}% ({h_val['risk_level']})")

# 4. Check Root HTML
with urllib.request.urlopen(f"{base}/") as r:
    html = r.read().decode()
    print(f"\n5. Frontend Index Served: {len(html)} bytes")
    assert "Coastal Sectors:" in html
    assert "Atmospheric Precursor Telemetry" in html
    assert "OASIS CAP v1.2 Standard Alert Feed" in html
    print("   All expected HTML components verified!")

print("\n--- ALL TESTS PASSED SUCCESSFULLY! ---")
