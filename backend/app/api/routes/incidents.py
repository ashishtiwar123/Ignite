from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.api.schemas.responses import (
    IncidentSummaryResponse,
    AssessmentResponse,
    UnsupportedHazardResponse,
    IncidentGovernanceResponse,
)
from app.api.schemas.requests import AssessmentReassessRequest

from app.db.dependencies import (
    get_incident_repository,
    get_assessment_repository,
    get_approval_repository,
    get_action_repository,
    get_allocation_repository,
)
from app.db.base_repository import BaseIncidentRepository
from app.db.assessment_repository import BaseAssessmentRepository
from app.db.approval_repository import BaseApprovalRepository
from app.db.action_repository import BaseActionRepository

from app.services.assessment_service import AssessmentService


router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
)


# ============================================================
# INCIDENTS
# ============================================================

@router.get(
    "",
    response_model=List[IncidentSummaryResponse],
)
def get_incidents(
    incident_repo: BaseIncidentRepository = Depends(
        get_incident_repository
    ),
):
    incidents = incident_repo.get_all()

    return [
        IncidentSummaryResponse(
            incident_id=i.incident_id,
            hazard_type=i.hazard_type,
            status=i.status,
            first_observed_at=i.first_observed_at,
            centroid_latitude=i.centroid_latitude,
            centroid_longitude=i.centroid_longitude,
        )
        for i in incidents
    ]


# ============================================================
# INCIDENT ASSESSMENT
# ============================================================

@router.get(
    "/{incident_id}/assessment",
)
def get_incident_assessment(
    incident_id: str,
    incident_repo: BaseIncidentRepository = Depends(
        get_incident_repository
    ),
    assessment_repo: BaseAssessmentRepository = Depends(
        get_assessment_repository
    ),
):
    incident = incident_repo.get(incident_id)

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    assessment_service = AssessmentService(
        assessment_repo
    )

    # --------------------------------------------------------
    # Build canonical predictor features
    # --------------------------------------------------------

    canonical_attrs = (
        dict(incident.canonical_attributes)
        if getattr(incident, "canonical_attributes", None)
        else {}
    )

    features_x = dict(canonical_attrs)

    # Earthquake aliases
    if (
        "magnitude" in features_x
        and "seismic_magnitude" not in features_x
    ):
        features_x["seismic_magnitude"] = features_x["magnitude"]

    if (
        "depth" in features_x
        and "seismic_depth_km" not in features_x
    ):
        features_x["seismic_depth_km"] = features_x["depth"]

    # Cyclone aliases
    if (
        "wind_speed" in features_x
        and "cyclone_max_wind_knots" not in features_x
    ):
        features_x["cyclone_max_wind_knots"] = features_x[
            "wind_speed"
        ]

    if (
        "pressure" in features_x
        and "cyclone_min_pressure_mb" not in features_x
    ):
        features_x["cyclone_min_pressure_mb"] = features_x[
            "pressure"
        ]

    event_features = {
        "incident_id": incident.incident_id,
        "disaster_type": incident.hazard_type,
        "predictor_features_x": features_x,
    }

    # --------------------------------------------------------
    # Calculate / retrieve assessment
    # --------------------------------------------------------

    try:
        record = assessment_service.get_or_calculate_assessment(
            incident,
            event_features,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    # --------------------------------------------------------
    # Unsupported hazard handling
    # --------------------------------------------------------

    if record.severity_status == "unsupported_hazard":
        severity = UnsupportedHazardResponse(
            hazard_type=incident.hazard_type,
            message="Hazard type not supported by severity model",
        )
    else:
        severity = record.severity

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return AssessmentResponse(
        incident_id=record.incident_id,
        verification_status=record.verification_status,
        severity=severity,
        trajectory=(
            record.trajectory
            if record.trajectory
            else {"status": "not_calculated"}
        ),
        needs={"status": "not_calculated"},
        priority={"status": "not_calculated"},
    )


# ============================================================
# GOVERNANCE
# ============================================================

@router.get(
    "/{incident_id}/governance",
    response_model=IncidentGovernanceResponse,
)
def get_incident_governance(
    incident_id: str,
    approval_repo: BaseApprovalRepository = Depends(
        get_approval_repository
    ),
    action_repo: BaseActionRepository = Depends(
        get_action_repository
    ),
    allocation_repo=Depends(
        get_allocation_repository
    ),
):
    """
    Read-only governance state endpoint.

    Determines the active proposal from persisted allocation
    records and resolves the approval belonging to that exact
    optimization_run_id.

    Important:
    - Legacy allocations with optimization_run_id=NULL are ignored.
    - An approval from an older optimization run cannot replace
      the approval for the current run.
    - thread_id and optimization_run_id remain separate concepts.
    """

    # --------------------------------------------------------
    # 1. Load persisted governance data
    # --------------------------------------------------------

    approvals = approval_repo.get_by_incident(
        incident_id
    )

    actions = action_repo.get_by_incident(
        incident_id
    )

    allocations = allocation_repo.get_by_incident(
        incident_id
    )

    # --------------------------------------------------------
    # DEBUG: Inspect exactly what governance receives
    # --------------------------------------------------------

    print(
        "[DEBUG GOVERNANCE ALLOCATIONS]",
        [
            {
                "allocation_id": allocation.allocation_id,
                "run_id": allocation.optimization_run_id,
                "created_at": str(allocation.created_at),
            }
            for allocation in allocations
        ],
    )

    # --------------------------------------------------------
    # 2. Find optimization runs represented by allocations
    # --------------------------------------------------------

    allocations_by_run = {}

    for allocation in allocations:
        run_id = allocation.optimization_run_id

        # Ignore legacy allocation records that do not belong
        # to an optimization run.
        if not run_id:
            continue

        allocations_by_run.setdefault(
            run_id,
            [],
        ).append(allocation)

    active_run_id = None

    if allocations_by_run:
        # Determine the most recently persisted optimization
        # run using the allocation creation timestamp.
        active_run_id = max(
            allocations_by_run.keys(),
            key=lambda run_id: max(
                allocation.created_at
                for allocation in allocations_by_run[run_id]
            ),
        )

    # --------------------------------------------------------
    # 3. Find approval belonging to the active run
    # --------------------------------------------------------

    active_approval = None

    if active_run_id:
        matching_approvals = [
            approval
            for approval in approvals
            if approval.optimization_run_id == active_run_id
        ]

        if matching_approvals:
            active_approval = max(
                matching_approvals,
                key=lambda approval: approval.created_at,
            )

    # --------------------------------------------------------
    # 4. Determine approval state
    # --------------------------------------------------------

    if active_approval:
        approval_status = active_approval.status
        approval_id = active_approval.approval_id

        optimization_run_id = (
            active_approval.optimization_run_id
        )

        thread_id = getattr(
            active_approval,
            "thread_id",
            None,
        )

    elif active_run_id:
        # A proposal exists, but its approval record has not
        # been persisted yet.
        approval_status = "PENDING"
        approval_id = None
        optimization_run_id = active_run_id
        thread_id = None

    else:
        # No current optimization proposal exists.
        approval_status = "NONE"
        approval_id = None
        optimization_run_id = None
        thread_id = None

    # --------------------------------------------------------
    # 5. Find latest execution action
    # --------------------------------------------------------

    latest_action = (
        max(
            actions,
            key=lambda action: action.created_at,
        )
        if actions
        else None
    )

    execution_status = (
        latest_action.status
        if latest_action
        else "UNEXECUTED"
    )

    execution_id = (
        latest_action.execution_id
        if latest_action
        else None
    )

    # --------------------------------------------------------
    # 6. Extract deducted resources
    # --------------------------------------------------------

    deducted_resources = []

    if (
        latest_action
        and latest_action.payload
        and isinstance(
            latest_action.payload,
            dict,
        )
    ):
        deducted_resources = latest_action.payload.get(
            "deducted_resources",
            [],
        )

    # --------------------------------------------------------
    # 7. Return governance state
    # --------------------------------------------------------

    return IncidentGovernanceResponse(
        incident_id=incident_id,
        optimization_run_id=optimization_run_id,
        thread_id=thread_id,
        approval_status=approval_status,
        execution_status=execution_status,
        execution_id=execution_id,
        approval_id=approval_id,
        deducted_resources=deducted_resources,
        errors=[],
    )


# ============================================================
# REASSESSMENT
# ============================================================

@router.post(
    "/{incident_id}/reassess",
)
def reassess_incident(
    incident_id: str,
    request: AssessmentReassessRequest,
    incident_repo: BaseIncidentRepository = Depends(
        get_incident_repository
    ),
):
    incident = incident_repo.get(incident_id)

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    # The full reassessment pipeline is handled through
    # the LangGraph agent workflow.
    raise HTTPException(
        status_code=501,
        detail=(
            "Full reassessment lifecycle via LangGraph "
            "is not yet supported in this phase."
        ),
    )