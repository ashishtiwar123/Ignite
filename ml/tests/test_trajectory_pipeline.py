import json
import os
import sys
import pytest
from datetime import datetime, timezone
import dateutil.parser

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml.src.risk.trajectory_schemas import RiskObservation
from ml.src.risk.trajectory import assess_trajectory

@pytest.fixture
def fixtures_data():
    path = os.path.join(os.path.dirname(__file__), '../data/fixtures/trajectory/observations.json')
    with open(path, 'r') as f:
        return json.load(f)

def _parse_time(t_str):
    if not t_str: return None
    return dateutil.parser.parse(t_str)

def get_scenario_data(fixtures, name):
    for s in fixtures['scenarios']:
        if s['id'] == name:
            candidate_id = s['candidate_id']
            observations = []
            for obs_dict in s['observations']:
                obs_dict['observed_at'] = _parse_time(obs_dict['observed_at'])
                observations.append(RiskObservation(**obs_dict))
            return candidate_id, observations
    return None, None

def test_scenario_1_improving(fixtures_data):
    candidate_id, observations = get_scenario_data(fixtures_data, "scenario_1")
    assessment = assess_trajectory(candidate_id, observations)
    
    assert assessment.trajectory == "IMPROVING"
    assert assessment.trend_strength == -1.0 # 4.0 - 5.0
    assert assessment.observation_window_hours == 12.0

def test_scenario_2_stable(fixtures_data):
    candidate_id, observations = get_scenario_data(fixtures_data, "scenario_2")
    assessment = assess_trajectory(candidate_id, observations)
    
    assert assessment.trajectory == "STABLE"
    assert assessment.trend_strength == pytest.approx(0.2) # 5.2 - 5.0
    
def test_scenario_3_worsening(fixtures_data):
    candidate_id, observations = get_scenario_data(fixtures_data, "scenario_3")
    assessment = assess_trajectory(candidate_id, observations)
    
    assert assessment.trajectory == "WORSENING"
    assert assessment.trend_strength == 1.0 # 6.0 - 5.0
    
def test_scenario_4_rapidly_worsening(fixtures_data):
    candidate_id, observations = get_scenario_data(fixtures_data, "scenario_4")
    assessment = assess_trajectory(candidate_id, observations)
    
    assert assessment.trajectory == "RAPIDLY_WORSENING"
    assert assessment.trend_strength == 3.0 # 8.0 - 5.0
    
def test_scenario_5_insufficient_observations(fixtures_data):
    candidate_id, observations = get_scenario_data(fixtures_data, "scenario_5")
    assessment = assess_trajectory(candidate_id, observations)
    
    assert assessment.trajectory == "INSUFFICIENT_EVIDENCE"
    
def test_scenario_6_missing_intensity(fixtures_data):
    candidate_id, observations = get_scenario_data(fixtures_data, "scenario_6")
    assessment = assess_trajectory(candidate_id, observations)
    
    assert assessment.trajectory == "INSUFFICIENT_EVIDENCE"
    
def test_scenario_7_cyclone_rapid(fixtures_data):
    candidate_id, observations = get_scenario_data(fixtures_data, "scenario_7")
    assessment = assess_trajectory(candidate_id, observations)
    
    assert assessment.trajectory == "RAPIDLY_WORSENING"
    assert assessment.trend_strength == 40.0 # 150.0 - 110.0
