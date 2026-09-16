# Needs Assessment Engine Policy Registry

# AUTHORITATIVE STANDARDS
# Reference: Sphere Handbook 2018 (WASH Standard 2.1)
SPHERE_WATER_L_PER_PERSON_DAY = 15.0
SPHERE_WATER_TABLETS_PER_BOX = 500

# Reference: Sphere Handbook 2018 (Food Security Standard 2.1)
SPHERE_FOOD_CEREAL_KG_PER_PERSON_DAY = 0.450
SPHERE_FOOD_PULSES_KG_PER_PERSON_DAY = 0.050
SPHERE_FOOD_VEG_OIL_KG_PER_PERSON_DAY = 0.025
SPHERE_FOOD_SALT_KG_PER_PERSON_DAY = 0.005

# Reference: Sphere Handbook 2018 (Shelter Standard 3.1)
SPHERE_SHELTER_SQM_PER_PERSON = 3.5
SPHERE_SHELTER_PERSONS_PER_HOUSEHOLD = 5.0
SPHERE_SHELTER_TARPAULINS_PER_HOUSEHOLD = 2

# OPERATIONAL HEURISTICS
# These are internal project rules not derived directly from Sphere

# Medical Urgency Mapping
# Derived from Severity Score and Hazard Type
def get_medical_urgency(severity: float, trajectory: str, hazard_type: str) -> str:
    if severity >= 4.0:
        return "CRITICAL" if trajectory in ["WORSENING", "RAPIDLY_WORSENING"] else "HIGH"
    elif severity >= 3.0:
        return "HIGH" if trajectory in ["WORSENING", "RAPIDLY_WORSENING"] else "MODERATE"
    elif severity >= 2.0:
        return "MODERATE"
    return "LOW"

# Rescue Urgency Mapping
# Highly dependent on hazard type
def get_rescue_urgency(severity: float, hazard_type: str) -> str:
    if hazard_type in ["Earthquake", "Landslide"]:
        if severity >= 4.0:
            return "CRITICAL"
        elif severity >= 3.0:
            return "HIGH"
        return "MODERATE"
    elif hazard_type in ["Flood", "Cyclone"]:
        if severity >= 4.0:
            return "HIGH"
        return "MODERATE"
    
    return "LOW"
