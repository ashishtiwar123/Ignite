import sys
import uuid
from datetime import datetime, timezone
sys.path.insert(0, '.')
sys.path.insert(0, 'backend')
from app.db.dependencies import get_incident_repository, get_resource_repository
from app.db.client import get_supabase_client
from ml.src.incident.schemas import Report
from app.api.schemas.internal import ResourceRecord

client = get_supabase_client()
assert client is not None

inc_repo = get_incident_repository()
res_repo = get_resource_repository()

test_marker = f"PHASE6B-TEST-CANARY-{uuid.uuid4().hex[:8]}"

# 1. Test Report write & read
report = Report(
    source="USGS",
    source_record_id=test_marker,
    hazard_type="EARTHQUAKE",
    latitude=34.05,
    longitude=-118.25,
    location_name="Canary Test Location",
    ingested_at=datetime.now(timezone.utc)
)
print(f"Writing report with source_record_id={test_marker}...")
inc_repo.save_report(report)

# Direct DB Query verification
res = client.table("reports").select("*").eq("source_record_id", test_marker).execute()
assert len(res.data) == 1, f"Expected 1 report in DB, got {len(res.data)}"
row = res.data[0]
print("PASS: Report persisted directly in Supabase reports table!")
print("  Report ID:", row["report_id"])
print("  Source record ID:", row["source_record_id"])

# 2. Test Resource write & read
res_id = str(uuid.uuid4())
resource = ResourceRecord(
    resource_id=res_id,
    location_id="LOC-PHASE6B-CANARY",
    resource_type="Potable Water",
    category="WATER",
    quantity_available=50000.0,
    unit="Liters",
    updated_at=datetime.now(timezone.utc),
    created_at=datetime.now(timezone.utc)
)
print("Writing resource...")
res_repo.upsert(resource)

# Direct DB Query verification
db_res = client.table("resources").select("*").eq("location_id", "LOC-PHASE6B-CANARY").execute()
assert len(db_res.data) >= 1, f"Expected resource in DB, got {len(db_res.data)}"
print("PASS: Resource persisted directly in Supabase resources table!")
print("  Location:", db_res.data[0]["location_id"])
print("  Quantity:", db_res.data[0]["quantity_available"])

# Cleanup canary records
client.table("reports").delete().eq("source_record_id", test_marker).execute()
client.table("resources").delete().eq("location_id", "LOC-PHASE6B-CANARY").execute()
print("Canary records cleaned up successfully.")
print("\nREAL WRITE/READ TEST THROUGH REPOSITORY LAYER SUCCEEDED LIVE IN SUPABASE!")
