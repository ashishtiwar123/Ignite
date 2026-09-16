import json
import os
import sys
import pytest
from datetime import datetime, timezone
import dateutil.parser

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml.src.incident.schemas import Report, IncidentCandidate
from ml.src.incident.verification import assess_incident

@pytest.fixture
def fixtures_data():
    path = os.path.join(os.path.dirname(__file__), '../data/fixtures/verification/evidence.json')
    with open(path, 'r') as f:
        return json.load(f)

def _parse_time(t_str):
    if not t_str: return None
    return dateutil.parser.parse(t_str)

def get_scenario_data(fixtures, name):
    for s in fixtures['scenarios']:
        if s['id'] == name:
            cand_dict = s['candidate']
            if 'first_observed_at' in cand_dict:
                cand_dict['first_observed_at'] = _parse_time(cand_dict['first_observed_at'])
            
            candidate = IncidentCandidate(**cand_dict)
            
            reports = []
            for r in s['reports']:
                if 'observed_at' in r:
                    r['observed_at'] = _parse_time(r['observed_at'])
                # Provide defaults required by Report schema
                if 'source_url' not in r: r['source_url'] = None
                if 'ingested_at' not in r: r['ingested_at'] = datetime.utcnow()
                reports.append(Report(**r))
            return candidate, reports
    return None, None

def test_scenario_1_strongly_corroborated(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_1")
    assessment = assess_incident(candidate, reports)
    
    assert assessment.verification_status == "VERIFIED"
    assert assessment.independent_source_count == 3
    assert assessment.spatial_consistency_score > 0
    assert assessment.temporal_consistency_score > 0

def test_scenario_2_insufficient_corroboration(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_2")
    assessment = assess_incident(candidate, reports)
    
    # 1 authoritative source = Score ~1.0
    # independent sources = 1
    # Threshold needs 2 independent sources
    assert assessment.verification_status == "NEEDS_VERIFICATION"
    assert assessment.independent_source_count == 1

def test_scenario_3_conflicting_evidence(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_3")
    assessment = assess_incident(candidate, reports)
    
    # Needs 2 independent sources, has USGS and NEWS
    assert assessment.independent_source_count == 2
    # But it has attribute conflicts (magnitude 6.2 vs 8.5 passed from candidate)
    assert len(assessment.conflicts) > 0
    assert assessment.attribute_consistency_score < 0
    # Because of penalties, might fall below 2.5
    assert assessment.verification_status == "NEEDS_VERIFICATION"

def test_scenario_4_duplicate_inflation(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_4")
    assessment = assess_incident(candidate, reports)
    
    # 2 USGS reports should count as 1 independent source
    assert assessment.independent_source_count == 1
    assert assessment.verification_status == "NEEDS_VERIFICATION"

def test_scenario_5_temporal_mismatch(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_5")
    assessment = assess_incident(candidate, reports)
    
    # Sep 16 vs Sep 17 for an Earthquake (max 2 hours)
    assert assessment.temporal_consistency_score < 0
    assert any(c['type'] == 'temporal' for c in assessment.conflicts)
    assert assessment.verification_status == "NEEDS_VERIFICATION"

def test_scenario_6_spatial_mismatch(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_6")
    assessment = assess_incident(candidate, reports)
    
    # Pune vs Japan
    assert assessment.spatial_consistency_score < 0
    assert any(c['type'] == 'spatial' for c in assessment.conflicts)
    assert assessment.verification_status == "NEEDS_VERIFICATION"

def test_scenario_7_hazard_mismatch(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_7")
    assessment = assess_incident(candidate, reports)
    
    # EQ vs Flood
    assert assessment.hazard_consistency_score < 0
    assert any(c['type'] == 'hazard' for c in assessment.conflicts)
    assert assessment.verification_status == "NEEDS_VERIFICATION"

def test_scenario_8_missing_fields(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_8")
    assessment = assess_incident(candidate, reports)
    
    # No penalties for spatial/temporal because candidate has None for centroid and observed_at
    # Missing fields shouldn't crash it, but it shouldn't be easily verified either
    assert assessment.verification_status == "NEEDS_VERIFICATION"
    assert assessment.spatial_consistency_score == 0.0

def test_scenario_9_cyclone(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_9")
    assessment = assess_incident(candidate, reports)
    
    # 2 independent authoritative sources, cyclone temporal window is 48hrs, spatial is 500km
    assert assessment.verification_status == "VERIFIED"
    assert assessment.temporal_consistency_score > 0
    assert assessment.spatial_consistency_score > 0

def test_scenario_10_unknown_sources(fixtures_data):
    candidate, reports = get_scenario_data(fixtures_data, "scenario_10")
    assessment = assess_incident(candidate, reports)
    
    assert assessment.independent_source_count == 2
    # Reliability score should be very low (0.1 each)
    assert assessment.source_reliability_score == 0.2
    assert assessment.verification_status == "NEEDS_VERIFICATION"
    assert assessment.verification_score < 4.5
