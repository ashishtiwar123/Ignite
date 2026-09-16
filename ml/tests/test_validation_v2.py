import os
import pytest
import numpy as np
import pandas as pd
from ml.src.validation.statistical_significance import compute_multiclass_brier, compute_metrics, run_paired_bootstrap
from ml.src.models.severity_v2.calibration_v2 import run_calibration_evaluation
from ml.src.models.severity_v2.explainer_v2 import SeverityV2Explainer
from ml.src.validation.benchmark_candidates import run_candidate_benchmark

def test_statistical_brier_calculation():
    y_true = np.array([0, 1, 2, 3])
    probs = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    brier = compute_multiclass_brier(y_true, probs)
    assert brier == 0.0

def test_statistical_significance_bootstrap(tmp_path):
    out_csv = str(tmp_path / "stat_sig.csv")
    out_doc = str(tmp_path / "stat_sig.md")
    df_rep = run_paired_bootstrap(n_iterations=100, random_seed=42, output_csv=out_csv, output_doc=out_doc)
    assert not df_rep.empty
    assert "statistical_significance" in df_rep.columns
    assert os.path.exists(out_csv)
    assert os.path.exists(out_doc)


def test_calibration_pipeline_and_artifacts():
    calib_meta = run_calibration_evaluation()
    assert calib_meta["leak_prevention_verified"] is True
    assert calib_meta["calibrated_v2_brier"] <= calib_meta["raw_v2_brier"]
    assert os.path.exists("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v2/calibration/v2_calibrator.joblib")

def test_explainer_artifact_loading_and_features():
    explainer = SeverityV2Explainer()
    assert len(explainer.feature_list) == 9
    assert "disaster_type_code" in explainer.feature_list
    assert "severity_class" not in explainer.feature_list

def test_explainer_deterministic_output():
    explainer = SeverityV2Explainer()
    sample = {
        "disaster_type_code": 0,
        "seismic_magnitude": 7.0,
        "seismic_depth_km": 10.0,
        "cyclone_max_wind_knots": None,
        "cyclone_min_pressure_mb": None,
        "hazard_intensity_index": 7.0,
        "country_population": 50000000.0,
        "population_density_sqkm": 100.0,
        "log_population_exposure": 17.72
    }
    res1 = explainer.explain_instance(sample, incident_id="INC-TEST", disaster_type="Earthquake")
    res2 = explainer.explain_instance(sample, incident_id="INC-TEST", disaster_type="Earthquake")
    assert res1["severity_class"] == res2["severity_class"]
    assert res1["probabilities"] == res2["probabilities"]
    assert res1["top_contributing_features"][0]["feature_name"] == res2["top_contributing_features"][0]["feature_name"]

def test_explainer_unsupported_hazard_fails_safely():
    explainer = SeverityV2Explainer()
    sample = {"disaster_type_code": 0}
    with pytest.raises(ValueError, match="Unsupported hazard"):
        explainer.explain_instance(sample, incident_id="INC-TEST-FLOOD", disaster_type="Flood")

def test_candidate_benchmark_execution():
    df_bm = run_candidate_benchmark()
    assert not df_bm.empty
    assert len(df_bm) >= 4
    assert os.path.exists("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity_v2/candidate_benchmark.csv")
