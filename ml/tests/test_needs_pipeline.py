import json
import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml.src.needs.schemas import NeedsAssessmentInput, ResourceRequirement
from ml.src.needs.engine import assess_needs

@pytest.fixture
def fixtures_data():
    path = os.path.join(os.path.dirname(__file__), '../data/fixtures/needs/inputs.json')
    with open(path, 'r') as f:
        return json.load(f)

def get_scenario_input(fixtures, name):
    for s in fixtures['scenarios']:
        if s['id'] == name:
            return NeedsAssessmentInput(**s['input'])
    return None

def test_scenario_1_high_severity(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_1")
    reqs = assess_needs(inp)
    
    assert len(reqs) == 5 # WATER, FOOD, SHELTER, MEDICAL, RESCUE
    
    # WATER: 10000 pop * 15 L * 1.1 (severity >= 4)
    water = next(r for r in reqs if r.category == "WATER")
    assert water.status == "CALCULATED"
    assert water.quantity == pytest.approx(165000.0)
    
    # FOOD: 10000 pop * 0.45 kg / 1000
    food = next(r for r in reqs if r.category == "FOOD")
    assert food.status == "CALCULATED"
    assert food.quantity == pytest.approx(4.5)
    
    # SHELTER: 2500 pop / 5 = 500 households * 2 = 1000 tarps
    shelter = next(r for r in reqs if r.category == "SHELTER")
    assert shelter.status == "CALCULATED"
    assert shelter.quantity == 1000.0
    
    # MEDICAL
    med = next(r for r in reqs if r.category == "MEDICAL")
    assert med.urgency_category == "CRITICAL"
    
    # RESCUE (Earthquake, Sev 4.5)
    res = next(r for r in reqs if r.category == "RESCUE")
    assert res.urgency_category == "CRITICAL"

def test_scenario_2_moderate_cyclone(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_2")
    reqs = assess_needs(inp)
    
    # WATER: 5000 pop * 15 L * 1.0 (severity < 4)
    water = next(r for r in reqs if r.category == "WATER")
    assert water.quantity == pytest.approx(75000.0)
    
    med = next(r for r in reqs if r.category == "MEDICAL")
    assert med.urgency_category == "MODERATE"
    
    res = next(r for r in reqs if r.category == "RESCUE")
    assert res.urgency_category == "MODERATE" # Cyclone severity 3.0 -> MODERATE

def test_scenario_3_missing_affected_population(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_3")
    reqs = assess_needs(inp)
    
    water = next(r for r in reqs if r.category == "WATER")
    assert water.status == "INSUFFICIENT_DATA"
    assert water.quantity is None
    
    shelter = next(r for r in reqs if r.category == "SHELTER")
    assert shelter.status == "CALCULATED"
    assert shelter.quantity == 200.0 # 500 / 5 * 2

def test_scenario_4_missing_displaced_population(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_4")
    reqs = assess_needs(inp)
    
    water = next(r for r in reqs if r.category == "WATER")
    assert water.status == "CALCULATED"
    
    shelter = next(r for r in reqs if r.category == "SHELTER")
    assert shelter.status == "INSUFFICIENT_DATA"
    assert shelter.quantity is None

def test_scenario_5_zero_population(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_5")
    reqs = assess_needs(inp)
    
    water = next(r for r in reqs if r.category == "WATER")
    assert water.status == "CALCULATED"
    assert water.quantity == 0.0
    
    shelter = next(r for r in reqs if r.category == "SHELTER")
    assert shelter.status == "CALCULATED"
    assert shelter.quantity == 0.0

def test_negative_population_raises_error():
    inp = NeedsAssessmentInput(
        verified_incident_id="test",
        hazard_type="Earthquake",
        affected_population=-100
    )
    with pytest.raises(ValueError):
        assess_needs(inp)
