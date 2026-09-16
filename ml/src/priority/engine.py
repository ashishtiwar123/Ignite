from typing import List
from ml.src.priority.schemas import PriorityEngineInput, PriorityAssessment
import ml.src.priority.policy as p

def assess_priority(input_data: PriorityEngineInput) -> PriorityAssessment:
    """
    Assess priority for a single incident.
    """
    assessment = PriorityAssessment(verified_incident_id=input_data.verified_incident_id, explanation="")
    
    # 1. Verification Gating
    if input_data.verification_status != "VERIFIED":
        assessment.priority_level = "PENDING_VERIFICATION"
        assessment.explanation = f"Priority assessment bypassed because incident is {input_data.verification_status}."
        assessment.contributing_factors.append("verification_status")
        return assessment

    # 2. Factor Calculation
    factors = {}
    explanation_parts = []
    
    # Severity
    if input_data.severity_score is not None:
        s_score = p.calculate_severity_score(input_data.severity_score)
        factors['severity'] = s_score
        assessment.contributing_factors.append("severity")
        explanation_parts.append(f"severity {input_data.severity_score} (+{s_score:.1f} pts)")
    else:
        assessment.missing_factors.append("severity")
        
    # Trajectory
    if input_data.trajectory not in ["UNKNOWN", "INSUFFICIENT_EVIDENCE"]:
        t_score = p.calculate_trajectory_score(input_data.trajectory)
        factors['trajectory'] = t_score
        assessment.contributing_factors.append("trajectory")
        explanation_parts.append(f"trajectory is {input_data.trajectory} ({t_score:+.1f} pts)")
    else:
        assessment.missing_factors.append("trajectory")
        
    # Population
    if input_data.affected_population is not None:
        pop_score = p.calculate_population_score(input_data.affected_population)
        factors['population'] = pop_score
        assessment.contributing_factors.append("population")
        explanation_parts.append(f"affected population is {input_data.affected_population} (+{pop_score:.1f} pts)")
    else:
        assessment.missing_factors.append("population")
        
    # Urgency (Needs)
    if input_data.rescue_urgency or input_data.medical_urgency:
        u_score = p.calculate_urgency_score(input_data.medical_urgency, input_data.rescue_urgency)
        factors['urgency'] = u_score
        assessment.contributing_factors.append("urgency")
        explanation_parts.append(f"urgency (Rescue: {input_data.rescue_urgency}, Medical: {input_data.medical_urgency}) (+{u_score:.1f} pts)")
    else:
        assessment.missing_factors.append("urgency")

    # Time Sensitivity and Vulnerability (currently unsupported by upstream data feeds)
    assessment.missing_factors.extend(["time_sensitivity", "vulnerability"])
    
    # 3. Summation and Normalized Cap
    total_score = sum(factors.values())
    # Ensure it stays within 0-100 range
    final_score = max(0.0, min(100.0, total_score))
    
    level = p.map_score_to_level(final_score)
    
    assessment.priority_score = final_score
    assessment.factor_scores = factors
    assessment.priority_level = level
    
    assessment.explanation = f"{level} priority ({final_score:.1f}/100) because: " + ", ".join(explanation_parts) + "."
    
    return assessment

def rank_incidents(inputs: List[PriorityEngineInput]) -> List[PriorityAssessment]:
    """
    Ranks multiple incidents.
    """
    assessments = [assess_priority(inp) for inp in inputs]
    
    # Tie-breaking logic:
    # 1. Priority Score (Desc)
    # 2. Rescue Urgency == CRITICAL (Desc / boolean)
    # 3. Trajectory == RAPIDLY_WORSENING (Desc / boolean)
    # 4. Affected Population (Desc)
    # 5. Incident ID (Asc, deterministic fallback)
    
    def sort_key(pa: PriorityAssessment):
        # We need original inputs for tie-breakers
        inp = next(i for i in inputs if i.verified_incident_id == pa.verified_incident_id)
        
        score = pa.priority_score
        has_critical_rescue = 1 if inp.rescue_urgency == "CRITICAL" else 0
        is_rapidly_worsening = 1 if inp.trajectory == "RAPIDLY_WORSENING" else 0
        pop = inp.affected_population or 0
        
        return (-score, -has_critical_rescue, -is_rapidly_worsening, -pop, pa.verified_incident_id)
        
    assessments.sort(key=sort_key)
    return assessments
