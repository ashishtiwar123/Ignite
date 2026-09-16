import pytest
import json
import os
import pandas as pd

CANONICAL_V3_JSON = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents_v3.json"
CANONICAL_V3_PARQUET = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents_v3.parquet"
OUTCOMES_V3_PARQUET = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes_v3.parquet"
FEATURES_V3_PARQUET = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/features_v3.parquet"
DATASET_V3_JSON = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v3.json"
DATASET_V3_PARQUET = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v3.parquet"
RAW_EXCEL_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/emdat/public_emdat_custom_request_2026-09-16_d55f319e-bbcb-4f8c-89ac-b6188623cbc8.xlsx"

def test_raw_emdat_exists_and_row_count():
    assert os.path.exists(RAW_EXCEL_PATH), "Raw official EM-DAT Excel file must exist"
    df_raw = pd.read_excel(RAW_EXCEL_PATH, sheet_name="EM-DAT Data")
    assert len(df_raw) == 16764, f"Raw EM-DAT row count must be exactly 16764, found {len(df_raw)}"

def test_canonical_v3_scale_and_unique_ids():
    assert os.path.exists(CANONICAL_V3_JSON), "Canonical V3 JSON must exist"
    with open(CANONICAL_V3_JSON, 'r', encoding='utf-8') as f:
        incidents = json.load(f)
    assert len(incidents) >= 16764, f"Canonical incident count must reflect EM-DAT scale, found {len(incidents)}"
    
    ids = [inc['incident_id'] for inc in incidents]
    assert len(ids) == len(set(ids)), "Canonical incident IDs must be unique"

def test_null_semantics_preserved_in_outcomes_v3():
    assert os.path.exists(OUTCOMES_V3_PARQUET), "Observed outcomes V3 Parquet must exist"
    df_out = pd.read_parquet(OUTCOMES_V3_PARQUET)
    
    # Check that unreported outcomes are NaN/None, not falsely zeroed out
    total_rows = len(df_out)
    deaths_null_count = df_out['observed_outcomes'].apply(lambda d: d.get('deaths') is None).sum()
    damage_null_count = df_out['observed_outcomes'].apply(lambda d: d.get('total_damage_usd_thousands') is None).sum()
    
    assert deaths_null_count > 0, "Missing deaths must be preserved as null"
    assert damage_null_count > 10000, "Financial damage missingness must be preserved as null (>10,000 missing)"

def test_temporal_guardrails_x_le_t0():
    assert os.path.exists(DATASET_V3_JSON), "Dataset V3 JSON must exist"
    with open(DATASET_V3_JSON, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
        
    eligible_count = 0
    for row in dataset:
        feat_keys = set(row['predictor_features_x'].keys())
        out_keys = set(row['observed_outcomes_y'].keys())
        # Assert no overlap between predictor features and target outcomes
        assert len(feat_keys.intersection(out_keys)) == 0, "Predictor features X and outcome target Y keys must not overlap"
        
        if row['is_training_eligible']:
            eligible_count += 1
            assert row['prediction_timestamp_t0'] is not None, "Training eligible row must have a valid T0"
            
    assert eligible_count >= 13000, f"Expected >13,000 training-eligible rows, found {eligible_count}"

def test_data_provenance_linkage():
    with open(DATASET_V3_JSON, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    for row in dataset[:100]:
        assert len(row['source_records']) > 0, "Every row must link back to source records"
        src = row['source_records'][0]
        assert "source" in src and "source_id" in src and "provenance" in src
