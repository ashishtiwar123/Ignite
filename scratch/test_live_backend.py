import sys, os
sys.path.insert(0, os.path.abspath("backend"))

from app.api.schemas.internal import AgentRunRequest
from app.services.agent_service import AgentService
from app.db.dependencies import (
    get_incident_repository,
    get_assessment_repository,
    get_approval_repository,
    get_allocation_repository
)

INCIDENT_ID = "56862ef4-18f4-4bfc-bcf6-795850362551"

print("=== START DIRECT AGENT SERVICE TEST ===")
service = AgentService()
req = AgentRunRequest(incident_id=INCIDENT_ID)

res = service.run_agent(req)
print("Run Agent Response:")
print("Status:", res.status)
print("Run ID:", res.run_id)
print("Approval State:", res.human_approval_state)
print("Errors:", res.errors)

# Check governance
appr_repo = get_approval_repository()
apprs = appr_repo.get_by_incident(INCIDENT_ID)
print("\nApprovals count in DB:", len(apprs))
if apprs:
    print("Latest approval status:", apprs[-1].status, "opt_run_id:", apprs[-1].optimization_run_id)

alloc_repo = get_allocation_repository()
allocs = alloc_repo.get_by_incident(INCIDENT_ID)
print("\nAllocations count in DB:", len(allocs))
if allocs:
    print("Allocations:", [(a.resource_type, a.quantity_allocated) for a in allocs])
