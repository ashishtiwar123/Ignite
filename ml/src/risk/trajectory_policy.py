from typing import Dict

# Operational Trajectory Policy v1
# NOTE: These values are NOT statistically validated. They are operational
# deterministic heuristics for trajectory evaluation.

# Primary feature to track for trend determination per hazard
HAZARD_INTENSITY_KEYS: Dict[str, str] = {
    "Earthquake": "magnitude",
    "Cyclone": "wind_speed",
    "Flood": "water_level",
    "Wildfire": "area_burned",
    "UNKNOWN": "severity_score"
}

# Delta thresholds for classification: (worsening_min, rapidly_worsening_min)
# IMPROVING < -worsening_min
# STABLE is between -worsening_min and worsening_min
HAZARD_DELTA_THRESHOLDS: Dict[str, tuple[float, float]] = {
    "Earthquake": (0.2, 1.0),   # E.g., a +0.2 mag increase over t-1 is worsening. +1.0 is rapid.
    "Cyclone": (10.0, 30.0),    # E.g., +10km/h wind speed
    "Flood": (0.5, 2.0),        # E.g., +0.5m water level
    "Wildfire": (100.0, 500.0), # E.g., +100 acres burned
    "UNKNOWN": (1.0, 3.0)       # Generic fallback
}

def get_primary_intensity_key(hazard_type: str) -> str:
    return HAZARD_INTENSITY_KEYS.get(hazard_type, HAZARD_INTENSITY_KEYS["UNKNOWN"])

def get_hazard_delta_thresholds(hazard_type: str) -> tuple[float, float]:
    return HAZARD_DELTA_THRESHOLDS.get(hazard_type, HAZARD_DELTA_THRESHOLDS["UNKNOWN"])
