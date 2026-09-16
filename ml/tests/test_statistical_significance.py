import os
import pytest
import numpy as np
import pandas as pd
from ml.src.validation.statistical_significance import (
    compute_multiclass_brier,
    compute_metrics,
    run_paired_bootstrap,
    V1_PREDS_PATH,
    V2_PREDS_PATH,
    DEFAULT_REPORT_CSV_PATH
)

def test_v1_v2_incident_id_equality():
    v1_df = pd.read_csv(V1_PREDS_PATH)
    v2_df = pd.read_csv(V2_PREDS_PATH)
    assert len(v1_df) == 336, f"Expected 336 data rows in V1, got {len(v1_df)}"
    assert len(v2_df) == 336, f"Expected 336 data rows in V2, got {len(v2_df)}"
    assert (v1_df['incident_id'] == v2_df['incident_id']).all(), "Incident ID or ordering mismatch"

def test_target_equality_after_normalization():
    v1_df = pd.read_csv(V1_PREDS_PATH)
    v2_df = pd.read_csv(V2_PREDS_PATH)
    y1 = v1_df['severity_class'].astype(int).values
    y2 = v2_df['severity_class'].astype(int).values
    assert (y1 == y2).all(), "Normalized target labels must match exactly between V1 and V2"

def test_direct_metric_calculation():
    v1_df = pd.read_csv(V1_PREDS_PATH)
    v2_df = pd.read_csv(V2_PREDS_PATH)
    y_true = v1_df['severity_class'].astype(int).values
    v1_preds = v1_df['predicted_class'].astype(int).values
    v2_preds = v2_df['predicted_class'].astype(int).values
    v1_probs = v1_df[['prob_low', 'prob_moderate', 'prob_high', 'prob_critical']].values
    v2_probs = v2_df[['prob_low', 'prob_moderate', 'prob_high', 'prob_critical']].values

    m_v1 = compute_metrics(y_true, v1_preds, v1_probs)
    m_v2 = compute_metrics(y_true, v2_preds, v2_probs)

    assert pytest.approx(m_v1['macro_f1'], abs=1e-4) == 0.2497
    assert pytest.approx(m_v2['macro_f1'], abs=1e-4) == 0.2794
    assert pytest.approx(m_v1['weighted_f1'], abs=1e-4) == 0.3045
    assert pytest.approx(m_v2['weighted_f1'], abs=1e-4) == 0.3139
    assert pytest.approx(m_v1['high_recall'], abs=1e-4) == 0.0000
    assert pytest.approx(m_v2['high_recall'], abs=1e-4) == 0.1594
    assert pytest.approx(m_v1['critical_recall'], abs=1e-4) == 0.1389
    assert pytest.approx(m_v2['critical_recall'], abs=1e-4) == 0.1389

def test_temporary_output_path_prevents_official_artifact_mutation(tmp_path):
    # Store modification time of official report if it exists
    official_exists = os.path.exists(DEFAULT_REPORT_CSV_PATH)
    mtime_before = os.path.getmtime(DEFAULT_REPORT_CSV_PATH) if official_exists else None

    out_csv = str(tmp_path / "test_stat_sig.csv")
    out_doc = str(tmp_path / "test_stat_sig.md")
    
    df_res = run_paired_bootstrap(n_iterations=50, random_seed=42, output_csv=out_csv, output_doc=out_doc)
    assert os.path.exists(out_csv)
    assert os.path.exists(out_doc)
    assert (df_res['bootstrap_iterations'] == 50).all()

    if official_exists:
        mtime_after = os.path.getmtime(DEFAULT_REPORT_CSV_PATH)
        assert mtime_before == mtime_after, "Running tests MUST NOT mutate the official statistical CSV artifact"

def test_deterministic_seed_behavior(tmp_path):
    out1 = str(tmp_path / "run1.csv")
    out2 = str(tmp_path / "run2.csv")
    df1 = run_paired_bootstrap(n_iterations=200, random_seed=42, output_csv=out1, output_doc=None)
    df2 = run_paired_bootstrap(n_iterations=200, random_seed=42, output_csv=out2, output_doc=None)
    
    pd.testing.assert_frame_equal(df1, df2)

def test_official_config_small_sample_run(tmp_path):
    out_csv = str(tmp_path / "stat_10k_sample.csv")
    df_res = run_paired_bootstrap(n_iterations=100, random_seed=42, output_csv=out_csv, output_doc=None)
    expected_cols = {"metric", "v1_metric", "v2_metric", "observed_difference", "ci_95_lower", "ci_95_upper", "bootstrap_iterations", "random_seed", "statistical_significance", "methodology"}
    assert set(df_res.columns) == expected_cols
