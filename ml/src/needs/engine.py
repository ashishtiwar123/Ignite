import math
from typing import List, Dict, Any
from ml.src.needs.schemas import NeedsAssessmentInput, ResourceRequirement
import ml.src.needs.policy as p

def assess_needs(input_data: NeedsAssessmentInput) -> List[ResourceRequirement]:
    requirements = []
    
    # Pre-validate negatives
    if input_data.affected_population is not None and input_data.affected_population < 0:
        raise ValueError("affected_population cannot be negative")
    if input_data.displaced_population is not None and input_data.displaced_population < 0:
        raise ValueError("displaced_population cannot be negative")

    # 1. WASH - Water Volume
    water_req = ResourceRequirement(
        verified_incident_id=input_data.verified_incident_id,
        resource_type="Potable Water",
        category="WATER",
        rule_id="SPHERE_WASH_2.1_V1",
        explanation="",
        status="INSUFFICIENT_DATA"
    )
    if input_data.affected_population is not None:
        severity_mult = 1.1 if input_data.severity_score and input_data.severity_score >= 4.0 else 1.0
        qty = input_data.affected_population * p.SPHERE_WATER_L_PER_PERSON_DAY * severity_mult
        
        water_req.quantity = qty
        water_req.unit = "Liters"
        water_req.status = "CALCULATED"
        water_req.calculation_basis = {
            "affected_population": input_data.affected_population,
            "severity_multiplier": severity_mult,
            "base_liters_per_person_day": p.SPHERE_WATER_L_PER_PERSON_DAY
        }
        water_req.explanation = f"Calculated using {input_data.affected_population} affected people x {p.SPHERE_WATER_L_PER_PERSON_DAY} L/person/day, scaled by {severity_mult}x severity multiplier based on Sphere Handbook 2018 WASH Standard 2.1."
    else:
        water_req.explanation = "INSUFFICIENT_DATA: affected_population is missing."
        
    requirements.append(water_req)

    # 2. Food - Cereal
    food_req = ResourceRequirement(
        verified_incident_id=input_data.verified_incident_id,
        resource_type="Cereal",
        category="FOOD",
        rule_id="SPHERE_FOOD_2.1_V1",
        explanation="",
        status="INSUFFICIENT_DATA"
    )
    if input_data.affected_population is not None:
        # Convert kg to metric tons (MT) for standard logistics
        qty_mt = (input_data.affected_population * p.SPHERE_FOOD_CEREAL_KG_PER_PERSON_DAY) / 1000.0
        
        food_req.quantity = qty_mt
        food_req.unit = "Metric Tons"
        food_req.status = "CALCULATED"
        food_req.calculation_basis = {
            "affected_population": input_data.affected_population,
            "kg_per_person_day": p.SPHERE_FOOD_CEREAL_KG_PER_PERSON_DAY
        }
        food_req.explanation = f"Calculated using {input_data.affected_population} affected people x {p.SPHERE_FOOD_CEREAL_KG_PER_PERSON_DAY} kg/person/day based on Sphere Handbook 2018 Food Standard 2.1."
    else:
        food_req.explanation = "INSUFFICIENT_DATA: affected_population is missing."

    requirements.append(food_req)

    # 3. Shelter - Tarpaulins
    shelter_req = ResourceRequirement(
        verified_incident_id=input_data.verified_incident_id,
        resource_type="Family Tarpaulins",
        category="SHELTER",
        rule_id="SPHERE_SHELTER_3.1_V1",
        explanation="",
        status="INSUFFICIENT_DATA",
        time_window="immediate"
    )
    if input_data.displaced_population is not None:
        households = math.ceil(input_data.displaced_population / p.SPHERE_SHELTER_PERSONS_PER_HOUSEHOLD)
        qty = households * p.SPHERE_SHELTER_TARPAULINS_PER_HOUSEHOLD
        
        shelter_req.quantity = qty
        shelter_req.unit = "Units"
        shelter_req.status = "CALCULATED"
        shelter_req.calculation_basis = {
            "displaced_population": input_data.displaced_population,
            "persons_per_household": p.SPHERE_SHELTER_PERSONS_PER_HOUSEHOLD,
            "tarpaulins_per_household": p.SPHERE_SHELTER_TARPAULINS_PER_HOUSEHOLD
        }
        shelter_req.explanation = f"Calculated using {input_data.displaced_population} displaced people ({households} households) x {p.SPHERE_SHELTER_TARPAULINS_PER_HOUSEHOLD} tarpaulins based on Sphere Handbook 2018 Shelter Standard 3.1."
    else:
        shelter_req.explanation = "INSUFFICIENT_DATA: displaced_population is missing."

    requirements.append(shelter_req)

    # 4. Medical Demand (Qualitative)
    severity_val = input_data.severity_score if input_data.severity_score is not None else 1.0
    med_urgency = p.get_medical_urgency(severity_val, input_data.trajectory, input_data.hazard_type)
    
    med_req = ResourceRequirement(
        verified_incident_id=input_data.verified_incident_id,
        resource_type="Medical Support",
        category="MEDICAL",
        rule_id="OPERATIONAL_MEDICAL_URGENCY_V1",
        status="CALCULATED",
        urgency_category=med_urgency,
        time_window="immediate",
        explanation=f"Qualitative medical urgency is {med_urgency} because verified incident has severity {severity_val} and trajectory {input_data.trajectory}.",
        calculation_basis={"severity": severity_val, "trajectory": input_data.trajectory}
    )
    requirements.append(med_req)

    # 5. Rescue Demand (Qualitative)
    rescue_urgency = p.get_rescue_urgency(severity_val, input_data.hazard_type)
    
    rescue_req = ResourceRequirement(
        verified_incident_id=input_data.verified_incident_id,
        resource_type="Search and Rescue",
        category="RESCUE",
        rule_id="OPERATIONAL_RESCUE_URGENCY_V1",
        status="CALCULATED",
        urgency_category=rescue_urgency,
        time_window="immediate",
        explanation=f"Qualitative rescue urgency is {rescue_urgency} because verified incident is {input_data.hazard_type} with severity {severity_val}.",
        calculation_basis={"severity": severity_val, "hazard_type": input_data.hazard_type}
    )
    requirements.append(rescue_req)

    return requirements
