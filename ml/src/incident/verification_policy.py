from typing import Dict, Tuple

# Operational Verification Policy v1
# NOTE: These values are NOT empirically validated probabilities. 
# They are deterministic operational weights for the verification engine.

# Source Reliability Weights
# Max 1.0 for authoritative, lower for unverified.
SOURCE_RELIABILITY_WEIGHTS: Dict[str, float] = {
    "USGS": 1.0,
    "GDACS": 1.0,
    "NOAA": 1.0,
    "FIRMS": 1.0,
    "EM-DAT": 1.0, # Historical/authoritative
    "NEWS": 0.5,
    "SOCIAL": 0.2,
    "UNKNOWN": 0.1
}

# Hazard Spatial Thresholds (in kilometers)
# The maximum distance between evidence locations to be considered spatially consistent.
HAZARD_SPATIAL_THRESHOLDS: Dict[str, float] = {
    "Earthquake": 100.0,
    "Cyclone": 500.0,
    "Flood": 300.0,
    "Wildfire": 50.0,
    "Landslide": 50.0,
    "Drought": 1000.0,
    "Extreme Weather": 500.0,
    "Conflict": 200.0,
    "UNKNOWN": 100.0
}

# Hazard Temporal Thresholds (in hours)
# The maximum time difference between evidence observations to be considered temporally consistent.
HAZARD_TEMPORAL_THRESHOLDS: Dict[str, float] = {
    "Earthquake": 2.0,       # Very sudden, narrow window
    "Cyclone": 48.0,         # Tracks over days
    "Flood": 72.0,           # Rises and falls over days
    "Wildfire": 48.0,        # Burns over days
    "Landslide": 24.0,       # Sudden but reporting may lag
    "Drought": 24.0 * 30,    # Very slow onset
    "Extreme Weather": 48.0, # Multi-day events
    "Conflict": 72.0,        # Ongoing
    "UNKNOWN": 24.0
}

# Verification Thresholds
# These determine the final status based on the computed verification score
VERIFICATION_THRESHOLDS = {
    "VERIFIED_MIN_SCORE": 4.5,
    "VERIFIED_MIN_INDEPENDENT_SOURCES": 2,
    "NEEDS_VERIFICATION_MIN_SCORE": 1.0
}

def get_source_reliability(source: str) -> float:
    # Use explicit mapping or fallback to UNKNOWN
    return SOURCE_RELIABILITY_WEIGHTS.get(str(source).upper(), SOURCE_RELIABILITY_WEIGHTS["UNKNOWN"])

def get_spatial_threshold(hazard_type: str) -> float:
    return HAZARD_SPATIAL_THRESHOLDS.get(hazard_type, HAZARD_SPATIAL_THRESHOLDS["UNKNOWN"])

def get_temporal_threshold(hazard_type: str) -> float:
    return HAZARD_TEMPORAL_THRESHOLDS.get(hazard_type, HAZARD_TEMPORAL_THRESHOLDS["UNKNOWN"])
