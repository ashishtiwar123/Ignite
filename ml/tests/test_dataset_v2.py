import pytest
import json
import os

CANONICAL_V2 = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents_v2.json"
OUTCOMES_V2 = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes_v2.json"
DATASET_V2 = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v2.json"

def test_canonical_incidents_v2_scale():
    assert os.path.exists(CANONICAL_V2), "Canonical incidents v2 file must exist"
    with open(CANONICAL_V2, 'r', encoding='utf-8') as f:
        incidents = json.load(f)
    assert len(incidents) >= 40, f"Canonical incident count must be significantly expanded (found {len(incidents)})"

def test_null_vs_zero_preservation_v2():
    assert os.path.exists(OUTCOMES_V2), "Observed outcomes v2 file must exist"
    with open(OUTCOMES_V2, 'r', encoding='utf-8') as f:
        outcomes = json.load(f)
    
    somalia = next((o for o in outcomes if "SOM" in o['incident_id']), None)
    if somalia:
        assert somalia['observed_outcomes']['injured'] is None, "Un-reported data must remain None, not 0"

def test_prediction_timestamp_boundary_v2():
    assert os.path.exists(DATASET_V2), "Dataset v2 file must exist"
    with open(DATASET_V2, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    for row in dataset:
        assert "prediction_timestamp_t0" in row
        features_keys = set(row['predictor_features_x'].keys())
        outcomes_keys = set(row['observed_outcomes_y'].keys())
        assert len(features_keys.intersection(outcomes_keys)) == 0, "Predictor features X and outcomes Y must not overlap"

def test_no_duplicate_incidents():
    with open(CANONICAL_V2, 'r', encoding='utf-8') as f:
        incidents = json.load(f)
    ids = [inc['incident_id'] for inc in incidents]
    assert len(ids) == len(set(ids)), "Canonical incident IDs must be unique"
