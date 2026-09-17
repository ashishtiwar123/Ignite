import requests
import json

url = "http://127.0.0.1:8001/reports"
payload = {
    "source": "FIELD_OPERATOR_REPORT",
    "source_record_id": "field-op-geo-test-1",
    "hazard_type": "Flood",
    "location_name": "Downtown Riverbank",
    "latitude": 34.0522,
    "longitude": -118.2437,
    "affected_population": 450,
    "raw_text": "Severe flooding at Downtown Riverbank at coordinates 34.0522, -118.2437 with 450 people needing immediate assistance."
}

print("Submitting report to POST /reports...")
resp = requests.post(url, json=payload)
print("Status code:", resp.status_code)
print("Response:", resp.json())

# Query GET /incidents
print("\nQuerying GET /incidents...")
inc_resp = requests.get("http://127.0.0.1:8001/incidents")
print("Status code:", inc_resp.status_code)
incidents = inc_resp.json()
print("Total incidents returned:", len(incidents))
for inc in incidents:
    print(f"Incident {inc['incident_id']} [{inc['hazard_type']} / {inc['status']}]: Lat={inc['centroid_latitude']}, Lon={inc['centroid_longitude']}")
