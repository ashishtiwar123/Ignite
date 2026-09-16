import pytest
import os
import json
import sys
import pandas as pd

# Add workspace root to python path for pytest module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ml.src.models.severity.predictor import SeverityPredictorV1

MODEL_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v1/"
MODEL_PATH = os.path.join(MODEL_DIR, "severity_model.joblib")
META_PATH = os.path.join(MODEL_DIR, "model_metadata.json")

def test_severity_v1_artifacts_exist():
    assert os.path.exists(MODEL_PATH), "Severity V1 model artifact must exist"
    assert os.path.exists(META_PATH), "Severity V1 metadata file must exist"

def test_predictor_supported_earthquake():
    predictor = SeverityPredictorV1()
    test_eq = {
        "incident_id": "INC-TEST-EQ",
        "emdat_dis_no": "2023-0001",
        "disaster_type": "Earthquake",
        "country": "Turkey",
        "hazard_source": "USGS",
        "match_confidence": "HIGH",
        "predictor_features_x": {"seismic_magnitude": 7.8, "seismic_depth_km": 10.0}
    }
    res = predictor.predict_severity(test_eq)
    assert res['status'] == "success"
    assert res['severity'] in ["Low", "Moderate", "High", "Critical"]
    assert "probabilities" in res
    assert 0.0 <= res['confidence'] <= 1.0

def test_predictor_unsupported_flood():
    predictor = SeverityPredictorV1()
    test_fl = {
        "incident_id": "INC-TEST-FLD",
        "disaster_type": "Flood",
        "country": "Pakistan"
    }
    res = predictor.predict_severity(test_fl)
    assert res['status'] == "unsupported_hazard"
    assert "supported_hazards" in res

def test_predictor_deterministic_output():
    predictor = SeverityPredictorV1()
    test_storm = {
        "incident_id": "INC-TEST-STORM",
        "disaster_type": "Storm",
        "country": "Philippines",
        "predictor_features_x": {"cyclone_max_wind_knots": 130.0, "cyclone_min_pressure_mb": 910.0}
    }
    res1 = predictor.predict_severity(test_storm)
    res2 = predictor.predict_severity(test_storm)
    assert res1['severity'] == res2['severity']
    assert res1['confidence'] == res2['confidence']
