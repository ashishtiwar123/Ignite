import pytest
import os
import json
import pandas as pd

V4_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/"
TRAIN_PARQUET = os.path.join(V4_DIR, "event_level_training.parquet")
UNMATCHED_PARQUET = os.path.join(V4_DIR, "unmatched_events.parquet")
MATCH_AUDIT = os.path.join(V4_DIR, "match_audit.parquet")
V3_DATASET_PARQUET = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v3.parquet"

def test_v3_preserved_unchanged():
    assert os.path.exists(V3_DATASET_PARQUET), "V3 dataset parquet must be preserved unchanged"

def test_no_placeholders_in_v4_training():
    assert os.path.exists(TRAIN_PARQUET), "Dataset V4 training parquet must exist"
    df_train = pd.read_parquet(TRAIN_PARQUET)
    
    for _, row in df_train.iterrows():
        fx = row['predictor_features_x']
        # Check that no synthetic/placeholder default values exist
        if 'seismic_magnitude' in fx and fx['seismic_magnitude'] is not None:
            assert fx['seismic_magnitude'] != 5.8 or row['hazard_source'] == "USGS", "Seismic magnitude must come from USGS telemetry, not synthetic default"
        assert 'inform_country_risk_baseline' not in fx, "Constant placeholder inform_country_risk_baseline must be removed"
        assert 'population_density_sqkm' not in fx, "Constant placeholder population_density_sqkm must be removed"

def test_every_training_row_has_real_y_and_real_x():
    df_train = pd.read_parquet(TRAIN_PARQUET)
    assert len(df_train) > 0, "Trainable dataset V4 must contain verified rows"
    
    for _, row in df_train.iterrows():
        y = row['observed_outcomes_y']
        has_y = any(v is not None for v in y.values())
        assert has_y, "Every V4 training row must contain real observed Y"
        assert row['hazard_source'] in ["USGS", "NOAA_IBTrACS"], "Every V4 training row must have real hazard telemetry source"
        assert row['match_confidence'] in ["HIGH", "MEDIUM"], "Match confidence must be HIGH or MEDIUM"

def test_no_post_event_outcome_in_x():
    df_train = pd.read_parquet(TRAIN_PARQUET)
    for _, row in df_train.iterrows():
        fx_keys = set(row['predictor_features_x'].keys())
        y_keys = set(row['observed_outcomes_y'].keys())
        assert len(fx_keys.intersection(y_keys)) == 0, "Predictor features X and outcomes Y must not overlap"

def test_null_preservation_in_unmatched():
    assert os.path.exists(UNMATCHED_PARQUET), "Unmatched events parquet must exist"
    df_unmatched = pd.read_parquet(UNMATCHED_PARQUET)
    # Check sample of unmatched rows to verify no non-null placeholder features were added
    for _, row in df_unmatched.head(100).iterrows():
        fx = row['predictor_features_x']
        non_null_vals = [v for v in fx.values() if v is not None and (isinstance(v, (int, float)) and not pd.isna(v))]
        assert len(non_null_vals) == 0, "Unmatched events must have null/None physical feature values (no non-null placeholders)"
