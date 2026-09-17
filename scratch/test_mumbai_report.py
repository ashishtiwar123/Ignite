import requests
import json

url = "http://127.0.0.1:8001/reports"
payload = {
    "source": "FIELD_OPERATOR_REPORT",
    "source_record_id": "field-op-mumbai-1",
    "hazard_type": "Flood",
    "location_name": "Kurla West Operational Sector",
    "latitude": 19.0701,
    "longitude": 72.8792,
    "affected_population": 1200,
    "raw_text": "Severe water accumulation at Kurla West at coordinates 19.0701, 72.8792."
}

print("Submitting Mumbai report...")
resp = requests.post(url, json=payload)
print("Status code:", resp.status_code)
print("Response:", resp.json())

# Verify in GET /incidents
inc_resp = requests.get("http://127.0.0.1:8001/incidents")
incidents = inc_resp.json()
mumbai_inc = [i for i in incidents if i.get("centroid_latitude") == 19.0701]
print("Found Mumbai incident:", len(mumbai_inc) > 0)
if mumbai_inc:
    print("Incident:", mumbai_inc[0])
