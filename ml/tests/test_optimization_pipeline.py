import json
import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml.src.optimization.schemas import AllocationContext
from ml.src.optimization.engine import optimize_allocation

@pytest.fixture
def fixtures_data():
    path = os.path.join(os.path.dirname(__file__), '../data/fixtures/optimization/inputs.json')
    with open(path, 'r') as f:
        return json.load(f)

def get_scenario_input(fixtures, name):
    for s in fixtures['scenarios']:
        if s['id'] == name:
            return AllocationContext(**s['input'])
    return None

def test_scenario_1_sufficient(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_1")
    res = optimize_allocation(inp)
    
    assert res.solver_status == "OPTIMAL"
    assert len(res.allocations) == 1
    
    alloc = res.allocations[0]
    assert alloc.quantity_allocated == 10000.0
    assert alloc.quantity_unmet == 0.0
    
    assert res.total_requested == 10000.0
    assert res.total_allocated == 10000.0
    assert res.total_unmet == 0.0

def test_scenario_2_scarcity_prioritizes_critical(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_2")
    res = optimize_allocation(inp)
    
    assert res.solver_status == "OPTIMAL"
    
    # We have 120 total food.
    # Crit needs 100. Low needs 50. Total 150.
    # Crit weight > Low weight, so Crit should get 100, Low gets 20.
    
    crit_alloc = next(a for a in res.allocations if a.verified_incident_id == "v_inc_crit")
    low_alloc = next(a for a in res.allocations if a.verified_incident_id == "v_inc_low")
    
    assert crit_alloc.quantity_allocated == pytest.approx(100.0)
    assert crit_alloc.quantity_unmet == pytest.approx(0.0)
    
    assert low_alloc.quantity_allocated == pytest.approx(20.0)
    assert low_alloc.quantity_unmet == pytest.approx(30.0)
    
    assert res.total_allocated == pytest.approx(120.0)
    assert res.total_unmet == pytest.approx(30.0)

def test_scenario_3_unit_safety(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_3")
    res = optimize_allocation(inp)
    
    assert res.solver_status == "OPTIMAL"
    
    # Requirement is Gallons, Inventory is Liters. They should not match.
    # So allocation should be 0, and unmet should be 100.
    alloc = res.allocations[0]
    assert alloc.quantity_allocated == 0.0
    assert alloc.quantity_unmet == 100.0
    assert res.total_unmet == 100.0
