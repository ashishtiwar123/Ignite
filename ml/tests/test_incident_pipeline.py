import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from datetime import datetime, timezone
from ml.src.incident.schemas import Report, IncidentCandidate
from ml.src.incident.normalization import normalize_hazard_type, normalize_timestamp
from ml.src.incident.validation import validate_report_fields
from ml.src.incident.matching import haversine_distance, match_reports
from ml.src.incident.deduplication import deduplicate_reports
from ml.src.incident.clustering import cluster_reports
from ml.src.ingestion.adapters import USGSAdapter, GDACSAdapter

@pytest.fixture
def fixtures_data():
    path = os.path.join(os.path.dirname(__file__), '../data/fixtures/incidents/reports.json')
    with open(path, 'r') as f:
        return json.load(f)
        
def get_scenario(fixtures, name):
    for s in fixtures['scenarios']:
        if s['id'] == name:
            return s
    return None

def process_reports(scenario) -> list:
    usgs = USGSAdapter()
    gdacs = GDACSAdapter()
    reports = []
    
    for item in scenario['input']:
        if item['adapter'] == 'USGS':
            reports.append(usgs.parse(item['raw_record']))
        elif item['adapter'] == 'GDACS':
            reports.append(gdacs.parse(item['raw_record']))
            
    return reports

def test_normalization_and_validation():
    assert normalize_hazard_type("EQ") == "Earthquake"
    assert normalize_hazard_type("Earth Quake") == "Earthquake"
    assert normalize_hazard_type("Hurricane") == "Cyclone"
    assert normalize_hazard_type("ALIEN_INVASION") == "UNKNOWN"
    
    dt = normalize_timestamp(1694860320000)
    assert dt.year == 2023
    assert dt.month == 9
    assert dt.tzinfo == timezone.utc
    
    # Validation logic
    report_dict = {"latitude": 95.0}
    _, errors = validate_report_fields(report_dict)
    assert any(e["field"] == "latitude" for e in errors)
    
    report_dict2 = {"wind_speed": -10}
    _, errors2 = validate_report_fields(report_dict2)
    assert any(e["field"] == "wind_speed" for e in errors2)

def test_haversine_distance():
    # Pune to Mumbai (approx 118 km)
    dist = haversine_distance(18.5204, 73.8567, 19.0760, 72.8777)
    assert 110 < dist < 125

def test_scenario_1_single_event(fixtures_data):
    s = get_scenario(fixtures_data, "scenario_1")
    reports = process_reports(s)
    candidates = cluster_reports(reports)
    
    assert len(candidates) == 1
    assert candidates[0].hazard_type == "Earthquake"
    assert candidates[0].source_count == 1

def test_scenario_2_merge(fixtures_data):
    s = get_scenario(fixtures_data, "scenario_2")
    reports = process_reports(s)
    candidates = cluster_reports(reports)
    
    assert len(candidates) == 1
    assert candidates[0].source_count == 2
    assert set(candidates[0].source_list) == {"USGS", "GDACS"}

def test_scenario_3_separate_locations(fixtures_data):
    s = get_scenario(fixtures_data, "scenario_3")
    reports = process_reports(s)
    candidates = cluster_reports(reports)
    
    assert len(candidates) == 2

def test_scenario_4_different_times(fixtures_data):
    s = get_scenario(fixtures_data, "scenario_4")
    reports = process_reports(s)
    candidates = cluster_reports(reports)
    
    assert len(candidates) == 2

def test_scenario_5_deduplication(fixtures_data):
    s = get_scenario(fixtures_data, "scenario_5")
    reports = process_reports(s)
    
    assert len(reports) == 2
    dedup = deduplicate_reports(reports)
    assert len(dedup) == 1

def test_scenario_6_invalid_latitude(fixtures_data):
    # Tests that the adapter creates a report but validation would complain
    s = get_scenario(fixtures_data, "scenario_6")
    reports = process_reports(s)
    assert reports[0].latitude == 95.0
    _, errs = validate_report_fields(reports[0].model_dump())
    assert len(errs) > 0

def test_scenario_8_conflict_handling(fixtures_data):
    s = get_scenario(fixtures_data, "scenario_8")
    reports = process_reports(s)
    candidates = cluster_reports(reports)
    
    assert len(candidates) == 1
    conflicts = candidates[0].conflicting_information
    
    assert len(conflicts) > 0
    assert any(c['field'] == 'magnitude' for c in conflicts)
    
def test_scenario_9_unknown_hazard(fixtures_data):
    s = get_scenario(fixtures_data, "scenario_9")
    reports = process_reports(s)
    
    assert reports[0].hazard_type == "UNKNOWN"

