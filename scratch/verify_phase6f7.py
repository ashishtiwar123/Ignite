import urllib.request
import json

INCIDENT_ID = "56862ef4-18f4-4bfc-bcf6-795850362551"
BASE_URL = "http://localhost:8001"

def get_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def post_json(url, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

print("=== 1. BEFORE RUN: GET /assessment ===")
ass_before = get_json(f"{BASE_URL}/incidents/{INCIDENT_ID}/assessment")
print(json.dumps(ass_before, indent=2))

print("\n=== 2. RUN OPERATIONAL WORKFLOW: POST /agents/run ===")
run_res = post_json(f"{BASE_URL}/agents/run", {"incident_id": INCIDENT_ID})
print(json.dumps(run_res, indent=2))

print("\n=== 3. AFTER RUN: GET /governance ===")
gov_after = get_json(f"{BASE_URL}/incidents/{INCIDENT_ID}/governance")
print(json.dumps(gov_after, indent=2))

print("\n=== 4. AFTER RUN: GET /assessment ===")
ass_after = get_json(f"{BASE_URL}/incidents/{INCIDENT_ID}/assessment")
print(json.dumps(ass_after, indent=2))

print("\n=== 5. AFTER RUN: GET /allocations/incident/{id} ===")
alloc_after = get_json(f"{BASE_URL}/allocations/incident/{INCIDENT_ID}")
print(json.dumps(alloc_after, indent=2))
