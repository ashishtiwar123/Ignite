from datetime import datetime, timezone
import dateutil.parser
from typing import Optional

# Canonical Hazard Taxonomy
CANONICAL_HAZARDS = {
    "FLOOD": "Flood",
    "CYCLONE": "Cyclone",
    "EARTHQUAKE": "Earthquake",
    "WILDFIRE": "Wildfire",
    "LANDSLIDE": "Landslide",
    "DROUGHT": "Drought",
    "EXTREME_WEATHER": "Extreme Weather",
    "CONFLICT": "Conflict",
}

HAZARD_ALIASES = {
    "EQ": "EARTHQUAKE",
    "EARTH QUAKE": "EARTHQUAKE",
    "HURRICANE": "CYCLONE",
    "TYPHOON": "CYCLONE",
    "TROPICAL STORM": "CYCLONE",
    "WILD FIRE": "WILDFIRE",
    "FIRE": "WILDFIRE",
}

def normalize_hazard_type(raw_hazard: str) -> str:
    if not raw_hazard:
        return "UNKNOWN"
        
    normalized = str(raw_hazard).upper().strip()
    
    if normalized in CANONICAL_HAZARDS:
        return CANONICAL_HAZARDS[normalized]
        
    if normalized in HAZARD_ALIASES:
        return CANONICAL_HAZARDS[HAZARD_ALIASES[normalized]]
        
    for canonical_key, canonical_val in CANONICAL_HAZARDS.items():
        if canonical_key in normalized:
            return canonical_val
            
    return "UNKNOWN"

def normalize_timestamp(timestamp_val) -> Optional[datetime]:
    if not timestamp_val:
        return None
    
    if isinstance(timestamp_val, datetime):
        dt = timestamp_val
    elif isinstance(timestamp_val, str):
        try:
            dt = dateutil.parser.parse(timestamp_val)
        except ValueError:
            return None
    elif isinstance(timestamp_val, (int, float)):
        try:
            dt = datetime.fromtimestamp(timestamp_val / 1000.0 if timestamp_val > 253402300799 else timestamp_val, tz=timezone.utc)
        except ValueError:
            return None
    else:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
        
    return dt
