import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.db.client import get_supabase_client

c = get_supabase_client()
print("Connected:", c is not None)
if c:
    reps = c.table("reports").select("report_id, source, latitude, longitude, hazard_type").execute()
    print("Reports count:", len(reps.data))
    for r in reps.data:
        print("Report:", r)
    
    incs = c.table("incidents").select("incident_id, hazard_type, status, centroid_latitude, centroid_longitude").execute()
    print("Incidents count:", len(incs.data))
    for i in incs.data:
        print("Incident:", i)
