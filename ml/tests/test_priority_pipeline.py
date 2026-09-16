import json
import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml.src.priority.schemas import PriorityEngineInput
from ml.src.priority.engine import assess_priority, rank_incidents

@pytest.fixture
def fixtures_data():
    path = os.path.join(os.path.dirname(__file__), '../data/fixtures/priority/inputs.json')
    with open(path, 'r') as f:
        return json.load(f)

def get_scenario_input(fixtures, name):
    for s in fixtures['scenarios']:
        if s['id'] == name:
            return PriorityEngineInput(**s['input'])
    return None

def test_scenario_1_critical(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_1")
    ass = assess_priority(inp)
    
    assert ass.priority_level == "CRITICAL"
    assert ass.priority_score > 70.0
    
    # Severity (4.8*8=38.4) + Traj (20) + Pop (log10(50000)*3.2=15.03) + Urgency (15+10=25->20) = 93.4
    assert "severity" in ass.factor_scores
    assert "trajectory" in ass.factor_scores
    assert "population" in ass.factor_scores
    assert "urgency" in ass.factor_scores

def test_scenario_2_high_stable(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_2")
    ass = assess_priority(inp)
    assert ass.priority_level == "MEDIUM"
    
def test_scenario_3_missing_population(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_3")
    ass = assess_priority(inp)
    
    assert "population" in ass.missing_factors
    assert "population" not in ass.factor_scores
    assert ass.priority_score > 0 # Should still calculate

def test_scenario_4_unverified_gating(fixtures_data):
    inp = get_scenario_input(fixtures_data, "scenario_4")
    ass = assess_priority(inp)
    
    assert ass.priority_level == "PENDING_VERIFICATION"
    assert ass.priority_score == 0.0

def test_ranking_and_tie_breaking(fixtures_data):
    inp_a = get_scenario_input(fixtures_data, "scenario_5_a")
    inp_b = get_scenario_input(fixtures_data, "scenario_5_b")
    
    # Let's check their scores.
    ass_a = assess_priority(inp_a)
    ass_b = assess_priority(inp_b)
    
    # A: Sev(20) + Traj(0) + Pop(log10(100)*3.2=6.4) + Urg(15+0=15) = 41.4
    # B: Sev(20) + Traj(0) + Pop(log10(100000)*3.2=16) + Urg(10+5=15) = 51.0
    # Wait, B is 51, A is 41.4. Let's make them tie explicitly.
    
    # Override for test tie-breaking:
    ass_a.priority_score = 50.0
    ass_b.priority_score = 50.0
    
    # In rank_incidents, it recalculates so the override on 'ass' won't work.
    # I'll just artificially create a tie with mock inputs.
    inp_a.severity_score = 3.0 # 24
    inp_a.trajectory = "STABLE" # 0
    inp_a.affected_population = 1000 # log10(1k)*3.2 = 9.6
    inp_a.rescue_urgency = "CRITICAL" # 15
    inp_a.medical_urgency = "LOW" # 0
    # A Total = 24 + 9.6 + 15 = 48.6
    
    inp_b.severity_score = 3.0 # 24
    inp_b.trajectory = "STABLE" # 0
    inp_b.affected_population = 1000 # 9.6
    inp_b.rescue_urgency = "HIGH" # 10
    inp_b.medical_urgency = "HIGH" # 5 (Total 15)
    # B Total = 24 + 9.6 + 15 = 48.6
    
    ranked = rank_incidents([inp_a, inp_b])
    
    assert ranked[0].verified_incident_id == "v_tie_a"
    assert ranked[1].verified_incident_id == "v_tie_b"
    assert ranked[0].priority_score == ranked[1].priority_score
    # A wins because it has CRITICAL rescue urgency
