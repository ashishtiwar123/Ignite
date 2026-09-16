from typing import List, Dict, Any, Tuple
from ml.src.risk.trajectory_schemas import RiskObservation, TrajectoryAssessment
from ml.src.risk.trajectory_policy import get_primary_intensity_key, get_hazard_delta_thresholds

def assess_trajectory(candidate_id: str, observations: List[RiskObservation]) -> TrajectoryAssessment:
    """
    Deterministically assess the trajectory of an incident based on historical observations.
    Returns a TrajectoryAssessment object.
    """
    assessment = TrajectoryAssessment(incident_candidate_id=candidate_id)
    
    if not observations:
        assessment.explanation = "No observations provided."
        return assessment
        
    assessment.observations_used = len(observations)
    assessment.evidence = [obs.observation_id for obs in observations]
    
    # Sort observations chronologically
    sorted_obs = sorted(observations, key=lambda x: x.observed_at)
    
    if len(sorted_obs) < 2:
        assessment.trajectory = "INSUFFICIENT_EVIDENCE"
        assessment.explanation = "INSUFFICIENT_EVIDENCE: Only 1 observation available. Absence of evidence is not evidence of stability."
        return assessment

    # Calculate observation window
    t0 = sorted_obs[0].observed_at
    tN = sorted_obs[-1].observed_at
    window_seconds = (tN - t0).total_seconds()
    assessment.observation_window_hours = round(window_seconds / 3600.0, 2)
    
    # Determine the primary hazard type from the latest observation
    latest_hazard = sorted_obs[-1].hazard_type
    primary_key = get_primary_intensity_key(latest_hazard)
    
    # Find valid observations for the primary key
    valid_values = []
    for obs in sorted_obs:
        if primary_key in obs.intensity_features:
            valid_values.append((obs.observed_at, obs.intensity_features[primary_key]))
            
    if len(valid_values) < 2:
        assessment.trajectory = "INSUFFICIENT_EVIDENCE"
        assessment.explanation = f"INSUFFICIENT_EVIDENCE: Less than 2 observations contain the primary intensity key '{primary_key}'."
        return assessment
        
    # Calculate delta between the oldest and newest valid value
    # To be more resilient, we might want to calculate between t-1 and t, or overall trend.
    # We will use the overall delta from the first valid observation to the last valid observation for simplicity in v1.
    val_first = valid_values[0][1]
    val_last = valid_values[-1][1]
    delta = val_last - val_first
    
    assessment.relevant_changes[primary_key] = delta
    
    worsening_min, rapid_worsening_min = get_hazard_delta_thresholds(latest_hazard)
    
    if delta >= rapid_worsening_min:
        assessment.trajectory = "RAPIDLY_WORSENING"
        assessment.trend_strength = delta
        assessment.confidence_level = min(1.0, len(valid_values) / 5.0)
        assessment.explanation = f"RAPIDLY_WORSENING because {primary_key} increased by {delta} (>= {rapid_worsening_min}) over {assessment.observation_window_hours} hours across {len(valid_values)} observations."
    elif delta >= worsening_min:
        assessment.trajectory = "WORSENING"
        assessment.trend_strength = delta
        assessment.confidence_level = min(1.0, len(valid_values) / 5.0)
        assessment.explanation = f"WORSENING because {primary_key} increased by {delta} (>= {worsening_min}) over {assessment.observation_window_hours} hours across {len(valid_values)} observations."
    elif delta <= -worsening_min:
        assessment.trajectory = "IMPROVING"
        assessment.trend_strength = delta
        assessment.confidence_level = min(1.0, len(valid_values) / 5.0)
        assessment.explanation = f"IMPROVING because {primary_key} decreased by {abs(delta)} (>= {worsening_min}) over {assessment.observation_window_hours} hours across {len(valid_values)} observations."
    else:
        assessment.trajectory = "STABLE"
        assessment.trend_strength = delta
        assessment.confidence_level = min(1.0, len(valid_values) / 5.0)
        assessment.explanation = f"STABLE because {primary_key} changed by only {delta} (within +/- {worsening_min}) over {assessment.observation_window_hours} hours across {len(valid_values)} observations."
        
    return assessment
