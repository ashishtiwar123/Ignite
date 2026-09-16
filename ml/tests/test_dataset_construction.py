import pytest
import json
import os

CANONICAL_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents.json"
OUTCOMES_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes.json"
DATASET_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate.json"

def test_canonical_incident_schema():
    assert os.path.exists(CANONICAL_PATH), "Canonical incidents file must exist"
    with open(CANONICAL_PATH, 'r', encoding='utf-8') as f:
        incidents = json.load(f)
    assert len(incidents) > 0, "Canonical incidents must not be empty"
    
    for inc in incidents:
        assert "incident_id" in inc
        assert "hazard_category" in inc
        assert "event_start" in inc
        assert "confidence_score" in inc

def test_null_vs_zero_preservation():
    assert os.path.exists(OUTCOMES_PATH), "Observed outcomes file must exist"
    with open(OUTCOMES_PATH, 'r', encoding='utf-8') as f:
        outcomes = json.load(f)
        
    somalia_drought = next((o for o in outcomes if "SOM" in o['incident_id']), None)
    if somalia_drought:
        # Assert injured is None/null, NOT forced to 0
        assert somalia_drought['observed_outcomes']['injured'] is None, "Un-reported field must remain None, not 0"

def test_prediction_timestamp_boundary():
    assert os.path.exists(DATASET_PATH), "Training dataset file must exist"
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
        
    for row in dataset:
        assert "prediction_timestamp_t0" in row
        assert row['prediction_timestamp_t0'] is not None
        # Predictor features X must be isolated from outcomes Y
        features_keys = set(row['predictor_features_x'].keys())
        outcomes_keys = set(row['observed_outcomes_y'].keys())
        assert len(features_keys.intersection(outcomes_keys)) == 0, "Predictor features X and outcomes Y must not overlap"
