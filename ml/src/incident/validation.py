from typing import List, Dict, Any, Tuple

def validate_report_fields(report_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Validates deterministically fields like latitude, longitude, magnitude, etc.
    Returns the original dictionary (with invalid values preserved if needed, though typically we just flag errors)
    and a list of validation errors.
    """
    errors = []
    
    # Latitude
    lat = report_dict.get('latitude')
    if lat is not None:
        if not (-90.0 <= lat <= 90.0):
            errors.append({"field": "latitude", "value": lat, "message": "Latitude must be between -90 and 90"})
            
    # Longitude
    lon = report_dict.get('longitude')
    if lon is not None:
        if not (-180.0 <= lon <= 180.0):
            errors.append({"field": "longitude", "value": lon, "message": "Longitude must be between -180 and 180"})
            
    # Population
    pop = report_dict.get('affected_population')
    if pop is not None:
        if pop < 0:
            errors.append({"field": "affected_population", "value": pop, "message": "Population cannot be negative"})
            
    # Wind Speed
    wind = report_dict.get('wind_speed')
    if wind is not None:
        if wind < 0:
            errors.append({"field": "wind_speed", "value": wind, "message": "Wind speed cannot be negative"})
            
    # Pressure
    pressure = report_dict.get('pressure')
    if pressure is not None:
        if pressure < 0:
            errors.append({"field": "pressure", "value": pressure, "message": "Pressure cannot be negative"})
            
    # Magnitude
    mag = report_dict.get('magnitude')
    if mag is not None:
        if not isinstance(mag, (int, float)):
            errors.append({"field": "magnitude", "value": mag, "message": "Magnitude must be a number"})
        elif mag < -2.0 or mag > 10.0:  # Sensible range for earthquake magnitude
            errors.append({"field": "magnitude", "value": mag, "message": "Magnitude out of reasonable bounds"})

    return report_dict, errors
