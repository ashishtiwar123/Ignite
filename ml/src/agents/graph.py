import json
from typing import Dict, Any, TypedDict, Literal

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import schemas and engines
from ml.src.agents.state import AgentState
from ml.src.agents.gemini_client import GeminiAdapter

from ml.src.optimization.schemas import AllocationContext, ResourceInventory
from ml.src.needs.schemas import ResourceRequirement, NeedsAssessmentInput
from ml.src.needs.engine import assess_needs
from ml.src.priority.schemas import PriorityAssessment, PriorityEngineInput
from ml.src.priority.engine import assess_priority
from ml.src.optimization.engine import optimize_allocation
from ml.src.models.severity_v2.predictor_v2 import SeverityPredictorV2
from ml.src.severity.engine import UnifiedSeverityEngine
from ml.src.risk.trajectory_schemas import RiskObservation
from ml.src.risk.trajectory import assess_trajectory

# Initialize clients
gemini_client = GeminiAdapter()
severity_predictor = SeverityPredictorV2()
severity_engine = UnifiedSeverityEngine(
    predictor_v2=severity_predictor
)

# Define the State graph dictionary
class GraphState(TypedDict):
    state: AgentState


import uuid
from datetime import datetime, timezone

from ml.src.incident.schemas import Report, IncidentCandidate
from ml.src.incident.normalization import (
    normalize_hazard_type,
    normalize_timestamp,
)
from ml.src.incident.validation import validate_report_fields
from ml.src.incident.deduplication import deduplicate_reports
from ml.src.incident.clustering import cluster_reports
from ml.src.incident.verification import assess_incident


# ============================================================
# REPORT INTELLIGENCE
# ============================================================

def report_intelligence_node(
    state_obj: GraphState,
) -> GraphState:

    state = state_obj["state"]
    structured_reports = []

    for raw in state.raw_reports:

        res = gemini_client.extract_structured_report(raw)

        if res:

            if "error" in res:
                state.errors.append(res["error"])
                continue

            source = "USER_REPORT"
            source_record_id = str(uuid.uuid4())
            parsed_raw = {}

            try:
                val = json.loads(raw)

                if isinstance(val, dict):
                    parsed_raw = val

                    if "source" in parsed_raw:
                        source = parsed_raw["source"]

                    if "source_record_id" in parsed_raw:
                        source_record_id = parsed_raw[
                            "source_record_id"
                        ]

            except Exception:
                pass

            hazard_raw = (
                parsed_raw.get("hazard_type")
                or res.get("hazard_type", "UNKNOWN")
            )

            if hazard_raw == "PROMPT_INJECTION_DETECTED":
                hazard = hazard_raw
            else:
                hazard = normalize_hazard_type(hazard_raw)

            report_dict = {
                "source": source,
                "source_record_id": source_record_id,
                "ingested_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "hazard_type": hazard,
                "location_name": (
                    parsed_raw.get("location")
                    or res.get("location")
                ),
                "latitude": (
                    parsed_raw.get("latitude")
                    if parsed_raw.get("latitude") is not None
                    else res.get("latitude")
                ),
                "longitude": (
                    parsed_raw.get("longitude")
                    if parsed_raw.get("longitude") is not None
                    else res.get("longitude")
                ),
                "magnitude": (
                    parsed_raw.get("magnitude")
                    if parsed_raw.get("magnitude") is not None
                    else res.get("magnitude")
                ),
                "wind_speed": (
                    parsed_raw.get("wind_speed")
                    if parsed_raw.get("wind_speed") is not None
                    else res.get("wind_speed")
                ),
                "pressure": (
                    parsed_raw.get("pressure")
                    if parsed_raw.get("pressure") is not None
                    else res.get("pressure")
                ),
                "depth": (
                    parsed_raw.get("depth")
                    if parsed_raw.get("depth") is not None
                    else res.get("depth")
                ),
                "affected_population": (
                    parsed_raw.get("affected_population")
                    if parsed_raw.get("affected_population") is not None
                    else res.get("affected_population")
                ),
                "displaced_population": (
                    parsed_raw.get("displaced_population")
                    if parsed_raw.get("displaced_population") is not None
                    else res.get("displaced_population")
                ),
                "observed_at": (
                    parsed_raw.get("observed_at")
                    or res.get("observed_at")
                ),
                "raw_text": raw,
                "raw_payload_reference": res,
            }

            structured_reports.append(report_dict)

    state.structured_reports = structured_reports

    return {"state": state}


# ============================================================
# INCIDENT DETECTION
# ============================================================

def incident_detection_node(
    state_obj: GraphState,
) -> GraphState:

    state = state_obj["state"]

    if not state.structured_reports:
        state.errors.append(
            "No structured reports extracted."
        )
        return {"state": state}

    # --------------------------------------------------------
    # 1. Validate and normalize reports
    # --------------------------------------------------------

    reports = []

    for r_dict in state.structured_reports:

        validated_dict, errs = validate_report_fields(
            r_dict.copy()
        )

        if errs:
            state.errors.extend(
                [
                    f"Validation error: {e['message']}"
                    for e in errs
                ]
            )

        if (
            "ingested_at" in validated_dict
            and isinstance(
                validated_dict["ingested_at"],
                str,
            )
        ):
            validated_dict["ingested_at"] = (
                normalize_timestamp(
                    validated_dict["ingested_at"]
                )
                or datetime.now(timezone.utc)
            )

        if (
            "observed_at" in validated_dict
            and isinstance(
                validated_dict["observed_at"],
                str,
            )
        ):
            validated_dict["observed_at"] = (
                normalize_timestamp(
                    validated_dict["observed_at"]
                )
            )

        reports.append(
            Report(**validated_dict)
        )

    # --------------------------------------------------------
    # 2. Deduplicate reports
    # --------------------------------------------------------

    deduped_reports = deduplicate_reports(
        reports
    )

    # --------------------------------------------------------
    # 3. Persist normalized reports
    # --------------------------------------------------------

    try:

        import sys
        import os

        backend_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "../../../backend",
            )
        )

        if backend_path not in sys.path:
            sys.path.insert(
                0,
                backend_path,
            )

        from app.db.dependencies import (
            get_incident_repository,
        )

        inc_repo = get_incident_repository()

        for report in deduped_reports:
            inc_repo.save_report(report)

    except Exception as e:

        state.errors.append(
            f"Persistence error saving report: {e}"
        )

    # --------------------------------------------------------
    # 4. Capture existing incident identity BEFORE clustering
    #
    # If /agents/run was started for an existing incident,
    # that incident ID is authoritative.
    #
    # The clustering process may create a candidate with a
    # generated ID, but that ID must NOT replace the canonical
    # incident identity.
    # --------------------------------------------------------

    # The API-selected incident is authoritative.
    # Fall back to the legacy candidate identity only when no target was supplied.
    existing_incident_id = state.target_incident_id
    existing_latitude = None
    existing_longitude = None

    if state.incident_candidates:

        existing_cand = (
            state.incident_candidates[0]
        )

        if isinstance(
            existing_cand,
            dict,
        ):

            if not existing_incident_id:
                existing_incident_id = (
                    existing_cand.get(
                        "incident_id"
                    )
                )

            existing_latitude = (
                existing_cand.get(
                    "centroid_latitude"
                )
            )

            existing_longitude = (
                existing_cand.get(
                    "centroid_longitude"
                )
            )

        else:

            if not existing_incident_id:
                existing_incident_id = getattr(
                    existing_cand,
                    "incident_id",
                    None,
                )

            existing_latitude = getattr(
                existing_cand,
                "centroid_latitude",
                None,
            )

            existing_longitude = getattr(
                existing_cand,
                "centroid_longitude",
                None,
            )

    # --------------------------------------------------------
    # 5. Cluster reports
    # --------------------------------------------------------

    candidates = cluster_reports(
        deduped_reports
    )

    # --------------------------------------------------------
    # 6. Preserve canonical incident identity
    #
    # This applies to BOTH:
    #
    #   - normal analysis of an existing incident
    #   - reassessment of an existing incident
    #
    # Previously this happened only when
    # state.reassessment_requested == True.
    # --------------------------------------------------------

    if (
        existing_incident_id
        and candidates
    ):

        candidates[0].incident_id = (
            existing_incident_id
        )

        # ----------------------------------------------------
        # Preserve canonical coordinates when newly clustered
        # reports don't provide coordinates.
        # ----------------------------------------------------

        if (
            candidates[0].centroid_latitude is None
            and existing_latitude is not None
        ):

            candidates[0].centroid_latitude = (
                existing_latitude
            )

        if (
            candidates[0].centroid_longitude is None
            and existing_longitude is not None
        ):

            candidates[0].centroid_longitude = (
                existing_longitude
            )

        if (
            existing_latitude is not None
            and existing_longitude is not None
            and candidates[0].centroid_latitude
            == existing_latitude
            and candidates[0].centroid_longitude
            == existing_longitude
        ):

            candidates[0].location_precision = (
                "POINT"
            )

    # --------------------------------------------------------
    # 7. Update graph state
    # --------------------------------------------------------

    state.incident_candidates = [
        candidate.model_dump()
        for candidate in candidates
    ]

    state.structured_reports = [
        report.model_dump()
        for report in deduped_reports
    ]

    return {"state": state}


# ============================================================
# VERIFICATION
# ============================================================

def verification_node(
    state_obj: GraphState,
) -> GraphState:

    state = state_obj["state"]

    if not state.incident_candidates:
        state.verification_status = "REJECTED"
        return {"state": state}

    cand_dict = (
        state.incident_candidates[0]
    )

    # Never allow a generated/legacy candidate ID to replace the API-selected ID.
    if state.target_incident_id:
        cand_dict["incident_id"] = state.target_incident_id
        state.incident_candidates[0] = cand_dict

    candidate = IncidentCandidate(
        **cand_dict
    )

    # Preserve graph-level prompt injection rejection
    if (
        candidate.hazard_type
        == "PROMPT_INJECTION_DETECTED"
    ):

        state.verification_status = (
            "REJECTED"
        )

        cand_dict["status"] = (
            "REJECTED"
        )

        state.incident_candidates[0] = (
            cand_dict
        )

        return {"state": state}

    reports = [
        Report(**r)
        for r in state.structured_reports
        if r["report_id"]
        in candidate.report_ids
    ]

    if not reports:

        state.verification_status = (
            "REJECTED"
        )

        return {"state": state}

    assessment = assess_incident(
        candidate,
        reports,
    )

    state.verification_status = (
        assessment.verification_status
    )

    cand_dict["status"] = (
        assessment.verification_status
    )

    state.incident_candidates[0] = (
        cand_dict
    )

    # Persist verification result
    try:

        import sys
        import os

        backend_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "../../../backend",
            )
        )

        if backend_path not in sys.path:
            sys.path.insert(
                0,
                backend_path,
            )

        from app.db.dependencies import (
            get_incident_repository,
        )

        candidate.status = (
            assessment.verification_status
        )

        get_incident_repository().save(
            candidate
        )

    except Exception as e:

        state.errors.append(
            f"Persistence error saving candidate: {e}"
        )

    return {"state": state}


# ============================================================
# SITUATION ASSESSMENT
# ============================================================

def situation_assessment_node(
    state_obj: GraphState,
) -> GraphState:

    state = state_obj["state"]

    if (
        state.verification_status
        != "VERIFIED"
    ):
        return {"state": state}

    cand_dict = (
        state.incident_candidates[0]
    )

    # Never allow a generated/legacy candidate ID to replace the API-selected ID.
    if state.target_incident_id:
        cand_dict["incident_id"] = state.target_incident_id
        state.incident_candidates[0] = cand_dict

    candidate = IncidentCandidate(
        **cand_dict
    )

    reports = [
        Report(**r)
        for r in state.structured_reports
        if r["report_id"]
        in candidate.report_ids
    ]

    canonical = (
        candidate.canonical_attributes
    )

    primary_report = (
        reports[0]
        if reports
        else None
    )

    affected_pop = (
        canonical.get(
            "affected_population"
        )
        or (
            getattr(
                primary_report,
                "affected_population",
                None,
            )
            if primary_report
            else None
        )
    )

    displaced_pop = (
        canonical.get(
            "displaced_population"
        )
        or (
            getattr(
                primary_report,
                "displaced_population",
                None,
            )
            if primary_report
            else None
        )
    )

    damage_est = (
        canonical.get(
            "damage_estimate"
        )
        or (
            getattr(
                primary_report,
                "damage_estimate",
                None,
            )
            if primary_report
            else None
        )
    )

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    event_features = {

        "disaster_type":
            candidate.hazard_type,

        "incident_id":
            candidate.incident_id,

        "country":
            (
                getattr(
                    primary_report,
                    "country",
                    None,
                )
                if primary_report
                else None
            ),

        "trajectory":
            getattr(
                state,
                "trajectory",
                None,
            ),

        "predictor_features_x": {

            "seismic_magnitude":
                canonical.get("magnitude")
                or (
                    getattr(
                        primary_report,
                        "magnitude",
                        None,
                    )
                    if primary_report
                    else None
                ),

            "seismic_depth_km":
                canonical.get("depth")
                or (
                    getattr(
                        primary_report,
                        "depth",
                        None,
                    )
                    if primary_report
                    else None
                ),

            "cyclone_max_wind_knots":
                canonical.get("wind_speed")
                or (
                    getattr(
                        primary_report,
                        "wind_speed",
                        None,
                    )
                    if primary_report
                    else None
                ),

            "cyclone_min_pressure_mb":
                canonical.get("pressure")
                or (
                    getattr(
                        primary_report,
                        "pressure",
                        None,
                    )
                    if primary_report
                    else None
                ),

            "country_population":
                canonical.get(
                    "country_population"
                ),

            "population_density_sqkm":
                canonical.get(
                    "population_density_sqkm"
                ),

            "affected_population":
                affected_pop,

            "displaced_population":
                displaced_pop,

            "damage_estimate":
                damage_est,

            "wind_speed":
                canonical.get("wind_speed")
                or (
                    getattr(
                        primary_report,
                        "wind_speed",
                        None,
                    )
                    if primary_report
                    else None
                ),

            "pressure":
                canonical.get("pressure")
                or (
                    getattr(
                        primary_report,
                        "pressure",
                        None,
                    )
                    if primary_report
                    else None
                ),
        },
    }

    severity_res = (
        severity_engine.predict_severity(
            event_features
        )
    )

    state.severity = severity_res

    if (
        severity_res.get("status")
        == "success"
    ):

        state.severity_score = (
            severity_res.get(
                "severity_score"
            )
        )

        severity_val = (
            state.severity_score
        )

        severity_model_version = (
            severity_res.get(
                "model_version"
            )
            or severity_res.get(
                "policy_version"
            )
        )

        severity_status = "supported"

    else:

        state.severity_score = None
        severity_val = None

        severity_model_version = (
            severity_res.get(
                "model_version"
            )
            or severity_res.get(
                "policy_version"
            )
        )

        severity_status = (
            severity_res.get(
                "status",
                "unsupported_hazard",
            )
        )

    # --------------------------------------------------------
    # Trajectory
    # --------------------------------------------------------

    observations = []

    for report in reports:

        obs = RiskObservation(

            incident_candidate_id=
                candidate.incident_id,

            observed_at=
                report.observed_at
                or report.ingested_at,

            hazard_type=
                report.hazard_type,

            source=
                report.source,

            source_record_id=
                report.source_record_id,
        )

        if report.magnitude is not None:

            obs.intensity_features[
                "seismic_magnitude"
            ] = report.magnitude

        if report.wind_speed is not None:

            obs.intensity_features[
                "cyclone_max_wind_knots"
            ] = report.wind_speed

        observations.append(obs)

    traj_assessment = assess_trajectory(
        candidate.incident_id,
        observations,
    )

    state.trajectory = (
        traj_assessment.trajectory
    )

    state.trajectory_status = (
        "CALCULATED"
    )

    # --------------------------------------------------------
    # Needs
    # --------------------------------------------------------

    affected_pop = (
        canonical.get(
            "affected_population"
        )
        or (
            getattr(
                primary_report,
                "affected_population",
                None,
            )
            if primary_report
            else None
        )
    )

    displaced_pop = (
        canonical.get(
            "displaced_population"
        )
        or (
            getattr(
                primary_report,
                "displaced_population",
                None,
            )
            if primary_report
            else None
        )
    )

    needs_input = NeedsAssessmentInput(

        verified_incident_id=
            candidate.incident_id,

        hazard_type=
            candidate.hazard_type,

        severity_score=
            severity_val,

        trajectory=
            state.trajectory,

        affected_population=
            affected_pop,

        displaced_population=
            displaced_pop,
    )

    try:

        needs_reqs = assess_needs(
            needs_input
        )

        state.needs = [
            n.model_dump()
            for n in needs_reqs
        ]

        state.needs_status = (
            "CALCULATED"
        )

    except Exception as e:

        state.needs = []

        state.needs_status = (
            f"FAILED: {str(e)}"
        )

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    med_urgency = None
    rescue_urgency = None

    for need in state.needs:

        if need.get("category") == "MEDICAL":
            med_urgency = need.get(
                "urgency_category"
            )

        if need.get("category") == "RESCUE":
            rescue_urgency = need.get(
                "urgency_category"
            )

    priority_input = PriorityEngineInput(

        verified_incident_id=
            candidate.incident_id,

        verification_status=
            state.verification_status,

        severity_score=
            severity_val,

        trajectory=
            state.trajectory,

        affected_population=
            affected_pop,

        medical_urgency=
            med_urgency,

        rescue_urgency=
            rescue_urgency,
    )

    try:

        priority_assessment = (
            assess_priority(
                priority_input
            )
        )

        state.priority = (
            priority_assessment.model_dump()
        )

        state.priority_status = (
            "CALCULATED"
        )

    except Exception as e:

        state.priority = None

        state.priority_status = (
            f"FAILED: {str(e)}"
        )

        priority_assessment = None

    # --------------------------------------------------------
    # Assessment persistence
    # --------------------------------------------------------

    import sys
    import os

    backend_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../../backend",
        )
    )

    if backend_path not in sys.path:
        sys.path.insert(
            0,
            backend_path,
        )

    from app.api.schemas.internal import (
        AssessmentRecord,
    )

    from app.db.dependencies import (
        get_assessment_repository,
        get_needs_repository,
    )

    from app.services.assessment_service import (
        AssessmentService,
    )

    from app.services.needs_service import (
        NeedsService,
    )

    idempotency_key = state.run_id

    assessment_service = (
        AssessmentService(
            get_assessment_repository()
        )
    )

    needs_service = (
        NeedsService(
            get_needs_repository()
        )
    )

    prev_latest = (
        get_assessment_repository()
        .get_latest_for_incident(
            candidate.incident_id
        )
    )

    parent_id = (
        prev_latest.assessment_id
        if prev_latest
        else state.parent_assessment_id
    )

    record = AssessmentRecord(

        incident_id=
            candidate.incident_id,

        idempotency_key=
            idempotency_key,

        parent_assessment_id=
            parent_id,

        reassessment_reason=
            state.reassessment_reason,

        verification_status=
            state.verification_status,

        severity_status=
            severity_status,

        severity=
            severity_res,

        trajectory_status=
            state.trajectory_status,

        trajectory=
            traj_assessment.model_dump(),

        priority_level=
            (
                priority_assessment.priority_level
                if priority_assessment
                else None
            ),

        priority_score=
            (
                priority_assessment.priority_score
                if priority_assessment
                else None
            ),

        severity_model_version=
            severity_model_version,

        verification_policy_version=
            "verification_v1",

        trajectory_policy_version=
            traj_assessment.policy_version,

        needs_policy_version=
            "needs_policy_v1",

        priority_policy_version=
            (
                priority_assessment.policy_version
                if priority_assessment
                else None
            ),
    )

    try:

        saved_record = (
            assessment_service
            .save_complete_assessment(
                record
            )
        )

        state.assessment_record = (
            saved_record.model_dump()
        )

        state.current_assessment_id = (
            saved_record.assessment_id
        )

        state.parent_assessment_id = (
            parent_id
        )

        if state.needs:

            needs_service.save_needs_from_assessment(

                incident_id=
                    candidate.incident_id,

                assessment_id=
                    saved_record.assessment_id,

                raw_needs=
                    state.needs,
            )

        if (
            "FAILED"
            in state.needs_status
            or
            "FAILED"
            in state.priority_status
        ):

            state.assessment_status = (
                "FAILED"
            )

        else:

            state.assessment_status = (
                "ASSESSMENT_COMPLETE"
            )

    except Exception as e:

        state.assessment_record = None

        state.assessment_status = (
            f"PERSISTENCE_FAILED: {str(e)}"
        )

    return {"state": state}


# ============================================================
# ASSESSMENT COMPARISON
# ============================================================

def assessment_comparison_node(
    state_obj: GraphState,
) -> GraphState:

    state = state_obj["state"]

    import sys
    import os

    backend_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../../backend",
        )
    )

    if backend_path not in sys.path:
        sys.path.insert(
            0,
            backend_path,
        )

    from app.services.reassessment_service import (
        ReassessmentService,
    )

    from app.db.dependencies import (
        get_assessment_repository,
        get_needs_repository,
        get_allocation_repository,
        get_action_repository,
    )

    svc = ReassessmentService(

        assessment_repo=
            get_assessment_repository(),

        needs_repo=
            get_needs_repository(),

        allocation_repo=
            get_allocation_repository(),

        action_repo=
            get_action_repository(),
    )

    cand = (
        state.incident_candidates[0]
        if state.incident_candidates
        else None
    )

    inc_id = (
        state.target_incident_id
        or (
            cand.get("incident_id")
            if isinstance(cand, dict)
            else (
                getattr(
                    cand,
                    "incident_id",
                    None,
                )
                if cand
                else None
            )
        )
    )

    if inc_id:

        assessments = (
            svc.assessment_repo
            .get_all_for_incident(
                inc_id
            )
        )

        current_ass_id = (
            state.assessment_record.get(
                "assessment_id"
            )
            if isinstance(
                state.assessment_record,
                dict,
            )
            else getattr(
                state.assessment_record,
                "assessment_id",
                None,
            )
        )

        previous_assessments = [
            a
            for a in assessments
            if getattr(
                a,
                "assessment_id",
                None,
            )
            != current_ass_id
        ]

        prev_record = (
            previous_assessments[-1]
            if previous_assessments
            else None
        )

        curr_record_dict = (
            state.assessment_record
        )

        if curr_record_dict:

            from backend.app.api.schemas.internal import (
                AssessmentRecord,
            )

            curr_record = (
                curr_record_dict
                if isinstance(
                    curr_record_dict,
                    AssessmentRecord,
                )
                else AssessmentRecord(
                    **curr_record_dict
                )
            )

            diff = (
                svc.compare_assessments(
                    prev_record,
                    curr_record,
                )
            )

            state.assessment_diff = (
                diff.model_dump()
            )

            (
                baseline_run_id,
                executed_allocs,
            ) = (
                svc
                .get_operational_allocation_baseline(
                    inc_id
                )
            )

            if baseline_run_id:

                state.operational_allocation_baseline_id = (
                    baseline_run_id
                )

    return {"state": state}


# ============================================================
# REALLOCATION DECISION
# ============================================================

def reallocation_decision_node(
    state_obj: GraphState,
) -> GraphState:

    state = state_obj["state"]

    import sys
    import os

    backend_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../../backend",
        )
    )

    if backend_path not in sys.path:
        sys.path.insert(
            0,
            backend_path,
        )

    from app.services.reassessment_service import (
        ReassessmentService,
    )

    from app.db.dependencies import (
        get_assessment_repository,
        get_needs_repository,
        get_allocation_repository,
        get_action_repository,
    )

    from app.api.schemas.internal import (
        AssessmentDiff,
        AllocationDiff,
    )

    svc = ReassessmentService(

        assessment_repo=
            get_assessment_repository(),

        needs_repo=
            get_needs_repository(),

        allocation_repo=
            get_allocation_repository(),

        action_repo=
            get_action_repository(),
    )

    diff = (
        AssessmentDiff(**state.assessment_diff)
        if isinstance(
            state.assessment_diff,
            dict,
        )
        else state.assessment_diff
    )

    alloc_diff = (
        AllocationDiff(**state.allocation_diff)
        if isinstance(
            state.allocation_diff,
            dict,
        )
        else state.allocation_diff
    )

    (
        status_str,
        is_req,
    ) = svc.is_reallocation_required(
        diff,
        alloc_diff,
    )

    state.reallocation_decision_status = (
        status_str
    )

    state.reallocation_required = (
        is_req
    )

    return {"state": state}


# ============================================================
# OPTIMIZATION
# ============================================================

def optimization_node(
    state_obj: GraphState,
    config: RunnableConfig = None,
) -> GraphState:

    state = state_obj["state"]

    if (
        state.verification_status
        != "VERIFIED"
    ):
        return {"state": state}

    if not state.incident_candidates:
        return {"state": state}

    cand_dict = (
        state.incident_candidates[0]
    )

    # API-selected incident ID is authoritative for optimization.
    incident_id = (
        state.target_incident_id
        or cand_dict.get("incident_id")
    )

    if state.target_incident_id:
        cand_dict["incident_id"] = state.target_incident_id
        state.incident_candidates[0] = cand_dict

    if not incident_id:
        return {"state": state}

    import sys
    import os

    backend_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../../backend",
        )
    )

    if backend_path not in sys.path:
        sys.path.insert(
            0,
            backend_path,
        )

    from app.api.schemas.internal import (
        OptimizationRequest,
    )

    from app.db.dependencies import (
        get_allocation_repository,
        get_needs_repository,
        get_resource_repository,
        get_assessment_repository,
    )

    from app.services.allocation_service import (
        AllocationService,
    )

    allocation_service = AllocationService(

        allocation_repo=
            get_allocation_repository(),

        needs_repo=
            get_needs_repository(),

        resource_repo=
            get_resource_repository(),

        assessment_repo=
            get_assessment_repository(),
    )

    opt_run_id = (
        state.run_id
        or f"opt-{uuid.uuid4()}"
    )

    req = OptimizationRequest(

        incident_ids=[
            incident_id
        ],

        optimization_run_id=
            opt_run_id,
    )

    try:

        res = (
            allocation_service
            .optimize(req)
        )

        state.allocation_result = (
            res.model_dump()
        )

        if res.optimization_run_id:

            state.run_id = (
                res.optimization_run_id
            )

        state.errors.extend(
            [
                f"Solver Status: {res.solver_status}"
            ]
        )

        # ----------------------------------------------------
        # Approval persistence
        # ----------------------------------------------------

        from app.db.dependencies import (
            get_action_repository,
            get_approval_repository,
        )

        from app.api.schemas.internal import (
            ApprovalRecord,
        )

        appr_repo = (
            get_approval_repository()
        )

        existing_apprs = (
            appr_repo.get_by_incident(
                incident_id
            )
        )

        thread_id = None

        print(f"[DEBUG GRAPH CONFIG] config={config}")

        if (
            config
            and isinstance(config, dict)
            and "configurable" in config
        ):

            thread_id = (
                config[
                    "configurable"
                ].get("thread_id")
            )

        print(f"[DEBUG GRAPH THREAD] thread_id={thread_id}")

        if not any(
            a.optimization_run_id
            == res.optimization_run_id
            for a in existing_apprs
        ):

            appr_repo.upsert(
                ApprovalRecord(

                    incident_id=
                        incident_id,

                    optimization_run_id=
                        res.optimization_run_id,

                    thread_id=
                        thread_id,

                    status=
                        "PENDING",
                )
            )

        # ----------------------------------------------------
        # Reassessment / allocation comparison
        # ----------------------------------------------------

        from app.services.reassessment_service import (
            ReassessmentService,
        )

        reassess_svc = ReassessmentService(

            assessment_repo=
                get_assessment_repository(),

            needs_repo=
                get_needs_repository(),

            allocation_repo=
                get_allocation_repository(),

            action_repo=
                get_action_repository(),
        )

        (
            base_run_id,
            prev_allocs,
        ) = (
            reassess_svc
            .get_operational_allocation_baseline(
                incident_id
            )
        )

        alloc_diff = (
            reassess_svc.compare_allocations(

                prev_allocs=
                    prev_allocs,

                curr_allocs=
                    res.allocations,

                baseline_run_id=
                    base_run_id,

                new_run_id=
                    state.run_id,
            )
        )

        state.allocation_diff = (
            alloc_diff.model_dump()
        )

        if base_run_id:

            state.previous_optimization_run_id = (
                base_run_id
            )

    except Exception as e:

        state.allocation_result = None

        state.errors.append(
            f"OPTIMIZATION_FAILED: {str(e)}"
        )

    return {"state": state}


# ============================================================
# COORDINATION
# ============================================================

def coordination_node(
    state_obj: GraphState,
) -> GraphState:

    state = state_obj["state"]

    if not state.allocation_result:
        return {"state": state}

    alloc_str = json.dumps(
        state.allocation_result.get(
            "allocations",
            [],
        ),
        default=str,
    )

    prior_str = json.dumps(
        state.priority,
        default=str,
    )

    plan = (
        gemini_client
        .explain_coordination(
            alloc_str,
            prior_str,
        )
    )

    state.coordination_plan = plan

    return {"state": state}


# ============================================================
# HUMAN REVIEW
# ============================================================

def human_review_node(
    state_obj: GraphState,
) -> GraphState:

    # This node is interrupted before execution.
    #
    # The human decision
    # (APPROVED / REJECTED / REVISION_REQUESTED)
    # is injected into state.human_approval_state.

    return state_obj


# ============================================================
# EXECUTION
# ============================================================

def execution_node(
    state_obj: GraphState,
) -> GraphState:

    """
    Phase 4F Controlled Execution Node.

    Delegates to backend ExecutionService which independently
    validates PERSISTED database approval.
    """

    state = state_obj["state"]

    if (
        state.human_approval_state
        != "APPROVED"
    ):
        return {"state": state}

    import sys
    import os

    backend_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../../backend",
        )
    )

    if backend_path not in sys.path:
        sys.path.insert(
            0,
            backend_path,
        )

    from app.api.schemas.internal import (
        ExecutionRequest,
    )

    from app.services.execution_service import (
        ExecutionService,
    )

    from app.db.dependencies import (
        get_approval_repository,
        get_allocation_repository,
        get_resource_repository,
        get_action_repository,
    )

    inc_id = (
        state.target_incident_id
        or (
            state.incident_candidates[0]
            .get("incident_id")
            if state.incident_candidates
            else None
        )
    )

    req = ExecutionRequest(

        optimization_run_id=
            state.run_id,

        incident_id=
            inc_id,

        executor_id=
            "GRAPH_NODE",
    )

    exec_svc = ExecutionService(

        approval_repo=
            get_approval_repository(),

        allocation_repo=
            get_allocation_repository(),

        resource_repo=
            get_resource_repository(),

        action_repo=
            get_action_repository(),
    )

    res = (
        exec_svc.execute_proposal(
            req
        )
    )

    if res.status in [
        "EXECUTED",
        "ALREADY_EXECUTED",
    ]:

        state.workflow_status = (
            "EXECUTED"
        )

    else:

        state.workflow_status = (
            f"EXECUTION_FAILED: {res.status}"
        )

        state.errors.extend(
            res.errors
        )

    return {"state": state}


# ============================================================
# ROUTING
# ============================================================

def route_after_verification(
    state_obj: GraphState,
) -> str:

    status = (
        state_obj["state"]
        .verification_status
    )

    if status == "VERIFIED":
        return "situation_assessment"

    elif status == "NEEDS_VERIFICATION":
        return "human_review"

    else:
        return "end"


def route_after_assessment(
    state_obj: GraphState,
) -> str:

    # After situation_assessment, compare
    # assessment with previous if reassessment.

    return "assessment_comparison"


def route_after_reassessment_decision(
    state_obj: GraphState,
) -> str:

    state = state_obj["state"]

    if (
        not state.reassessment_requested
        or state.reallocation_required
    ):

        return "optimization"

    return "end"


def route_after_optimization(
    state_obj: GraphState,
) -> str:

    res = (
        state_obj["state"]
        .allocation_result
    )

    if not res:
        return "end"

    return "human_review"


def route_after_human(
    state_obj: GraphState,
) -> str:

    status = (
        state_obj["state"]
        .human_approval_state
    )

    if status == "APPROVED":
        return "execution"

    return "end"


# ============================================================
# BUILD GRAPH
# ============================================================

def build_graph() -> StateGraph:

    workflow = StateGraph(
        GraphState
    )

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    workflow.add_node(
        "report_intelligence",
        report_intelligence_node,
    )

    workflow.add_node(
        "incident_detection",
        incident_detection_node,
    )

    workflow.add_node(
        "verification",
        verification_node,
    )

    workflow.add_node(
        "situation_assessment",
        situation_assessment_node,
    )

    workflow.add_node(
        "assessment_comparison",
        assessment_comparison_node,
    )

    workflow.add_node(
        "reallocation_decision",
        reallocation_decision_node,
    )

    workflow.add_node(
        "optimization",
        optimization_node,
    )

    workflow.add_node(
        "coordination",
        coordination_node,
    )

    workflow.add_node(
        "human_review",
        human_review_node,
    )

    workflow.add_node(
        "execution",
        execution_node,
    )

    # --------------------------------------------------------
    # Entry
    # --------------------------------------------------------

    workflow.set_entry_point(
        "report_intelligence"
    )

    # --------------------------------------------------------
    # Report Intelligence → Incident Detection
    # --------------------------------------------------------

    workflow.add_edge(
        "report_intelligence",
        "incident_detection",
    )

    # --------------------------------------------------------
    # Incident Detection → Verification
    # --------------------------------------------------------

    workflow.add_edge(
        "incident_detection",
        "verification",
    )

    # --------------------------------------------------------
    # Verification routing
    # --------------------------------------------------------

    workflow.add_conditional_edges(

        "verification",

        route_after_verification,

        {
            "situation_assessment":
                "situation_assessment",

            "human_review":
                "human_review",

            "end":
                END,
        },
    )

    # --------------------------------------------------------
    # Assessment → Comparison
    # --------------------------------------------------------

    workflow.add_edge(
        "situation_assessment",
        "assessment_comparison",
    )

    # --------------------------------------------------------
    # Comparison → Reallocation Decision
    # --------------------------------------------------------

    workflow.add_edge(
        "assessment_comparison",
        "reallocation_decision",
    )

    # --------------------------------------------------------
    # Reallocation Decision routing
    # --------------------------------------------------------

    workflow.add_conditional_edges(

        "reallocation_decision",

        route_after_reassessment_decision,

        {
            "optimization":
                "optimization",

            "end":
                END,
        },
    )

    # --------------------------------------------------------
    # Optimization routing
    # --------------------------------------------------------

    workflow.add_conditional_edges(

        "optimization",

        route_after_optimization,

        {
            "human_review":
                "human_review",

            "end":
                END,
        },
    )

    # --------------------------------------------------------
    # Coordination
    # --------------------------------------------------------

    workflow.add_edge(
        "coordination",
        "human_review",
    )

    # --------------------------------------------------------
    # Human Review routing
    # --------------------------------------------------------

    workflow.add_conditional_edges(

        "human_review",

        route_after_human,

        {
            "execution":
                "execution",

            "end":
                END,
        },
    )

    # --------------------------------------------------------
    # Execution → END
    # --------------------------------------------------------

    workflow.add_edge(
        "execution",
        END,
    )

    # --------------------------------------------------------
    # Checkpointer
    # --------------------------------------------------------

    try:

        from langgraph.checkpoint.serde.jsonplus import (
            JsonPlusSerializer,
        )

        serde = JsonPlusSerializer(
            allowed_msgpack_modules=[
                (
                    "ml.src.agents.state",
                    "AgentState",
                )
            ]
        )

        memory = MemorySaver(
            serde=serde
        )

    except Exception:

        memory = MemorySaver()

    # --------------------------------------------------------
    # Compile graph
    # --------------------------------------------------------

    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=[
            "human_review"
        ],
    )

    return app