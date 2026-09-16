import pytest
import os
import json
import pandas as pd

V4_PARQUET = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
V5_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v5/"
V5_PARQUET = os.path.join(V5_DIR, "event_level_features.parquet")
PROVENANCE_PARQUET = os.path.join(V5_DIR, "feature_provenance.parquet")

def test_v4_preserved_unchanged_by_v5():
    assert os.path.exists(V4_PARQUET), "V4 dataset parquet must be preserved unchanged"
    df_v4 = pd.read_parquet(V4_PARQUET)
    assert len(df_v4) == 336, f"V4 must retain 336 rows, found {len(df_v4)}"

def test_v5_schema_and_row_count():
    assert os.path.exists(V5_PARQUET), "Dataset V5 features parquet must exist"
    df_v5 = pd.read_parquet(V5_PARQUET)
    assert len(df_v5) == 336, f"V5 must retain 336 enriched rows, found {len(df_v5)}"

def test_no_placeholders_in_v5_exposure():
    df_v5 = pd.read_parquet(V5_PARQUET)
    for _, row in df_v5.iterrows():
        fx = row['predictor_features_x']
        pop = fx.get('country_population')
        den = fx.get('population_density_sqkm')
        assert pop is not None, "Population must be non-null historical World Bank value"
        assert den is not None, "Population density must be non-null historical World Bank value"
        assert den != 280.0, "Population density must NOT be constant 280.0 placeholder"

def test_v5_temporal_historical_alignment():
    df_prov = pd.read_parquet(PROVENANCE_PARQUET)
    for _, row in df_prov.iterrows():
        ev_yr = int(row['event_year'])
        pop_yr = int(row['matched_population_year'])
        assert pop_yr <= ev_yr, f"Matched population year ({pop_yr}) must NOT exceed event year ({ev_yr}) to prevent leakage"

def test_no_target_leakage_in_v5_features():
    df_v5 = pd.read_parquet(V5_PARQUET)
    for _, row in df_v5.iterrows():
        fx_keys = set(row['predictor_features_x'].keys())
        y_keys = set(row['observed_outcomes_y'].keys())
        assert len(fx_keys.intersection(y_keys)) == 0, "Predictor features X and outcomes Y must not overlap in V5"
