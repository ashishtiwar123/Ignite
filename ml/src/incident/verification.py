from typing import List, Dict, Any, Tuple
from ml.src.incident.schemas import Report, IncidentCandidate
from ml.src.incident.verification_schemas import VerificationEvidence, VerificationAssessment
from ml.src.incident.verification_policy import (
    get_source_reliability,
    get_spatial_threshold,
    get_temporal_threshold,
    VERIFICATION_THRESHOLDS
)
from ml.src.incident.matching import haversine_distance

def assess_incident(candidate: IncidentCandidate, reports: List[Report]) -> VerificationAssessment:
    """
    Assess an incident candidate using its underlying reports as evidence.
    Returns a VerificationAssessment with score, status, and explanation.
    """
    assessment = VerificationAssessment(incident_candidate_id=candidate.incident_id)
    
    evidence_list: List[VerificationEvidence] = []
    sources_seen = set()
    
    # 1. Build Evidence and Corroboration
    reliability_sum = 0.0
    for report in reports:
        # A report only counts as evidence if it's associated with this candidate
        if report.report_id not in candidate.report_ids:
            continue
            
        rel_score = get_source_reliability(report.source)
        
        evidence = VerificationEvidence(
            incident_candidate_id=candidate.incident_id,
            source=report.source,
            source_record_id=report.source_record_id,
            source_reliability_score=rel_score,
            observed_at=report.observed_at,
            latitude=report.latitude,
            longitude=report.longitude,
            hazard_type=report.hazard_type,
            attributes={"magnitude": report.magnitude} if report.magnitude is not None else {},
            provenance={"raw_report_id": report.report_id}
        )
        evidence_list.append(evidence)
        assessment.supporting_evidence_ids.append(evidence.evidence_id)
        
        # Corroboration: count independent sources
        if report.source not in sources_seen:
            sources_seen.add(report.source)
            assessment.independent_source_count += 1
            reliability_sum += rel_score
            
    assessment.evidence_count = len(evidence_list)
    
    if assessment.evidence_count == 0:
        assessment.verification_status = "REJECTED"
        assessment.explanation.append("No evidence found for this candidate.")
        return assessment
        
    assessment.source_reliability_score = reliability_sum
    # Simple corroboration score: log-like curve based on independent sources, scaled by reliability
    assessment.corroboration_score = min(2.0, (assessment.independent_source_count - 1) * 0.5)

    # 2. Consistency Checks
    hazard = candidate.hazard_type
    spatial_threshold = get_spatial_threshold(hazard)
    temporal_threshold = get_temporal_threshold(hazard)
    
    spatial_penalties = 0.0
    temporal_penalties = 0.0
    hazard_penalties = 0.0
    attribute_penalties = 0.0
    
    explanations = [f"Found {assessment.independent_source_count} independent source(s)."]
    
    # Check consistency against the candidate's canonical/centroid values
    # Or check pairwise consistency. We'll use candidate centroid for spatial.
    if candidate.centroid_latitude is not None and candidate.centroid_longitude is not None:
        for ev in evidence_list:
            if ev.latitude is not None and ev.longitude is not None:
                dist = haversine_distance(
                    candidate.centroid_latitude, candidate.centroid_longitude,
                    ev.latitude, ev.longitude
                )
                if dist > spatial_threshold:
                    spatial_penalties += 0.5
                    assessment.conflicts.append({
                        "type": "spatial",
                        "evidence_id": ev.evidence_id,
                        "distance": dist,
                        "threshold": spatial_threshold
                    })
        if spatial_penalties == 0.0:
            assessment.spatial_consistency_score = 1.0
            explanations.append("Spatial evidence is consistent.")
        else:
            assessment.spatial_consistency_score = -spatial_penalties
            explanations.append(f"Spatial conflicts detected ({spatial_penalties} penalty).")
    else:
        explanations.append("Spatial evidence is missing or incomplete.")

    if candidate.first_observed_at is not None:
        for ev in evidence_list:
            if ev.observed_at:
                diff_hours = abs((candidate.first_observed_at - ev.observed_at).total_seconds()) / 3600.0
                if diff_hours > temporal_threshold:
                    temporal_penalties += 0.5
                    assessment.conflicts.append({
                        "type": "temporal",
                        "evidence_id": ev.evidence_id,
                        "diff_hours": diff_hours,
                        "threshold": temporal_threshold
                    })
        if temporal_penalties == 0.0:
            assessment.temporal_consistency_score = 1.0
            explanations.append("Temporal evidence is consistent.")
        else:
            assessment.temporal_consistency_score = -temporal_penalties
            explanations.append(f"Temporal conflicts detected ({temporal_penalties} penalty).")
    else:
        explanations.append("Temporal evidence is missing or incomplete.")

    for ev in evidence_list:
        if ev.hazard_type != hazard and ev.hazard_type != "UNKNOWN":
            hazard_penalties += 1.0
            assessment.conflicts.append({
                "type": "hazard",
                "evidence_id": ev.evidence_id,
                "evidence_hazard": ev.hazard_type,
                "candidate_hazard": hazard
            })
            
    if hazard_penalties == 0.0:
        assessment.hazard_consistency_score = 1.0
        explanations.append("Hazard classification is consistent.")
    else:
        assessment.hazard_consistency_score = -hazard_penalties
        explanations.append(f"Hazard conflicts detected ({hazard_penalties} penalty).")

    # Pass through candidate conflicts as attribute penalties
    if len(candidate.conflicting_information) > 0:
        attribute_penalties = len(candidate.conflicting_information) * 0.5
        assessment.attribute_consistency_score = -attribute_penalties
        assessment.conflicts.extend(candidate.conflicting_information)
        explanations.append(f"Attribute conflicts inherited from candidate ({attribute_penalties} penalty).")
    else:
        assessment.attribute_consistency_score = 0.5 # slight positive for having no attribute conflicts
        explanations.append("No attribute conflicts detected.")

    # 3. Calculate Final Score
    # Score = Reliability + Corroboration + Spatial + Temporal + Hazard + Attribute
    total_score = (
        assessment.source_reliability_score +
        assessment.corroboration_score +
        assessment.spatial_consistency_score +
        assessment.temporal_consistency_score +
        assessment.hazard_consistency_score +
        assessment.attribute_consistency_score
    )
    
    assessment.verification_score = max(0.0, round(total_score, 2))
    
    # 4. Status Decision Policy
    # Hard bounds for verification: must have spatial and temporal consensus without active penalties
    has_critical_penalties = (
        assessment.spatial_consistency_score < 0 or
        assessment.temporal_consistency_score < 0 or
        assessment.hazard_consistency_score < 0 or
        assessment.attribute_consistency_score < 0
    )
    
    is_missing_critical_data = (
        assessment.spatial_consistency_score == 0.0 or
        assessment.temporal_consistency_score == 0.0
    )

    if (assessment.verification_score >= VERIFICATION_THRESHOLDS["VERIFIED_MIN_SCORE"] and 
        assessment.independent_source_count >= VERIFICATION_THRESHOLDS["VERIFIED_MIN_INDEPENDENT_SOURCES"] and
        not has_critical_penalties and
        not is_missing_critical_data):
        
        assessment.verification_status = "VERIFIED"
        explanations.append(f"Status set to VERIFIED. Score {assessment.verification_score} meets threshold with complete, unconflicted evidence.")
    elif assessment.verification_score >= VERIFICATION_THRESHOLDS["NEEDS_VERIFICATION_MIN_SCORE"]:
        assessment.verification_status = "NEEDS_VERIFICATION"
        reason = "Score is insufficient."
        if has_critical_penalties: reason = "Critical evidence conflicts exist."
        elif is_missing_critical_data: reason = "Critical spatial or temporal evidence is missing."
        explanations.append(f"Status set to NEEDS_VERIFICATION. {reason} (Score: {assessment.verification_score})")
    else:
        assessment.verification_status = "CANDIDATE"
        explanations.append(f"Status remains CANDIDATE. Score {assessment.verification_score} is very low.")
        
    assessment.explanation = explanations
    assessment.confidence = min(1.0, assessment.verification_score / 5.0) # Normalizing roughly to [0,1]

    return assessment
