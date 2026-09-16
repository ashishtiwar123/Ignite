import math
from typing import Dict, Any, List, Tuple
from ml.src.incident.schemas import Report

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
        
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371.0 # Radius of earth in kilometers
    return c * r

def match_reports(r1: Report, r2: Report) -> Dict[str, Any]:
    """
    Compare two reports and determine if they describe the same incident.
    Returns:
    {
        "match_score": float,
        "decision": "MATCH" | "POSSIBLE_MATCH" | "NO_MATCH",
        "reasons": list,
        "conflicting_fields": list
    }
    """
    reasons = []
    conflicts = []
    score = 0.0
    
    # Hazard Compatibility
    if r1.hazard_type != "UNKNOWN" and r2.hazard_type != "UNKNOWN":
        if r1.hazard_type != r2.hazard_type:
            return {
                "match_score": 0.0,
                "decision": "NO_MATCH",
                "reasons": ["Different hazard types"],
                "conflicting_fields": ["hazard_type"]
            }
        else:
            reasons.append(f"Same hazard ({r1.hazard_type})")
            score += 0.3
            
    # Temporal Compatibility
    if r1.observed_at and r2.observed_at:
        time_diff = abs((r1.observed_at - r2.observed_at).total_seconds())
        # If time diff is > 24 hours, very unlikely to be same event unless it's a long-running hazard
        # We will use stricter rules for events like Earthquake
        if r1.hazard_type == "Earthquake":
            max_time_diff = 3600 * 2  # 2 hours
        else:
            max_time_diff = 3600 * 48 # 48 hours for Flood, Cyclone
            
        if time_diff > max_time_diff:
            return {
                "match_score": 0.0,
                "decision": "NO_MATCH",
                "reasons": [f"Time difference too large ({time_diff/3600:.1f} hours)"],
                "conflicting_fields": ["observed_at"]
            }
        else:
            reasons.append(f"{time_diff/60:.1f} minute temporal difference")
            # Score decays with time diff
            score += max(0.0, 0.4 * (1.0 - (time_diff / max_time_diff)))
            
    # Spatial Compatibility
    if r1.latitude and r1.longitude and r2.latitude and r2.longitude:
        dist = haversine_distance(r1.latitude, r1.longitude, r2.latitude, r2.longitude)
        if r1.hazard_type == "Earthquake":
            max_dist = 100.0 # 100 km
        else:
            max_dist = 500.0 # 500 km
            
        if dist > max_dist:
            return {
                "match_score": 0.0,
                "decision": "NO_MATCH",
                "reasons": [f"Spatial distance too large ({dist:.1f} km)"],
                "conflicting_fields": ["latitude", "longitude"]
            }
        else:
            reasons.append(f"{dist:.1f} km spatial difference")
            score += max(0.0, 0.3 * (1.0 - (dist / max_dist)))
            
    # Additional hazard specific signals could be added here
    if r1.hazard_type == "Earthquake" and r1.magnitude and r2.magnitude:
        mag_diff = abs(r1.magnitude - r2.magnitude)
        if mag_diff > 1.5:
            # Significant magnitude difference for same event
            conflicts.append("magnitude")
            # Might still be same event but different measurements, just flag it.
            
    # Determine Decision
    decision = "NO_MATCH"
    if score >= 0.7:
        decision = "MATCH"
    elif score >= 0.3:
        decision = "POSSIBLE_MATCH"
        
    return {
        "match_score": round(score, 2),
        "decision": decision,
        "reasons": reasons,
        "conflicting_fields": conflicts
    }
