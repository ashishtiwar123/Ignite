import pytest
from ml.src.severity.engine import UnifiedSeverityEngine
from ml.src.severity.policies import FloodPolicyV1, WildfirePolicyV1, HeavyRainfallPolicyV1

@pytest.fixture
def engine():
    return UnifiedSeverityEngine()

def test_earthquake_routing_preserves_ml(engine):
    event = {
        "disaster_type": "Earthquake",
        "incident_id": "INC-EQ-TEST",
        "predictor_features_x": {
            "seismic_magnitude": 7.8,
            "seismic_depth_km": 10.0,
            "country_population": 85000000.0,
            "population_density_sqkm": 110.0
        }
    }
    res = engine.predict_severity(event)
    assert res.get("status") == "success"
    assert res.get("assessment_method") == "ML"
    assert res.get("model_version") == "severity_v2"
    assert res.get("confidence") is not None
    assert res.get("probabilities") is not None
    assert 0.0 <= res.get("severity_score") <= 10.0

def test_cyclone_routing_preserves_ml(engine):
    event = {
        "disaster_type": "Cyclone",
        "incident_id": "INC-CYC-TEST",
        "predictor_features_x": {
            "cyclone_max_wind_knots": 120.0,
            "cyclone_min_pressure_mb": 940.0,
            "country_population": 50000000.0,
            "population_density_sqkm": 200.0
        }
    }
    res = engine.predict_severity(event)
    assert res.get("status") == "success"
    assert res.get("assessment_method") == "ML"
    assert res.get("model_version") == "severity_v2"
    assert res.get("confidence") is not None

def test_flood_policy_routing(engine):
    event = {
        "disaster_type": "Flood",
        "incident_id": "INC-FLOOD-TEST",
        "trajectory": "ESCALATING",
        "predictor_features_x": {
            "affected_population": 50000,
            "displaced_population": 12000,
            "population_density_sqkm": 350.0,
            "damage_estimate": 1000000.0
        }
    }
    res = engine.predict_severity(event)
    assert res.get("status") == "success"
    assert res.get("assessment_method") == "POLICY"
    assert res.get("policy_version") == "FLOOD_POLICY_V1"
    assert res.get("confidence") is None
    assert res.get("probabilities") is None
    assert 0.0 <= res.get("severity_score") <= 10.0
    assert res.get("severity_class") in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert res.get("evidence_coverage")["available_factors_count"] == 5

def test_flood_policy_missing_data_retained(engine):
    event = {
        "disaster_type": "Flood",
        "incident_id": "INC-FLOOD-MISSING",
        "predictor_features_x": {
            "affected_population": 1000
            # missing displaced_population, population_density_sqkm, damage_estimate
        }
    }
    res = engine.predict_severity(event)
    assert res.get("status") == "success"
    assert res.get("assessment_method") == "POLICY"
    cov = res.get("evidence_coverage")
    assert cov["available_factors_count"] == 1
    assert "displaced_population" in cov["missing_factors"]
    assert "damage_estimate" in cov["missing_factors"]

def test_wildfire_policy_routing(engine):
    event = {
        "disaster_type": "Wildfire",
        "incident_id": "INC-FIRE-TEST",
        "predictor_features_x": {
            "affected_population": 8000,
            "displaced_population": 3000,
            "population_density_sqkm": 80.0
        }
    }
    res = engine.predict_severity(event)
    assert res.get("status") == "success"
    assert res.get("assessment_method") == "POLICY"
    assert res.get("policy_version") == "WILDFIRE_POLICY_V1"
    assert res.get("confidence") is None
    assert res.get("probabilities") is None

def test_heavy_rainfall_policy_routing(engine):
    event = {
        "disaster_type": "Heavy Rainfall",
        "incident_id": "INC-RAIN-TEST",
        "predictor_features_x": {
            "affected_population": 15000,
            "wind_speed": 45.0,
            "pressure": 985.0
        }
    }
    res = engine.predict_severity(event)
    assert res.get("status") == "success"
    assert res.get("assessment_method") == "POLICY"
    assert res.get("policy_version") == "HEAVY_RAINFALL_POLICY_V1"
    assert res.get("confidence") is None
    assert res.get("probabilities") is None

def test_heavy_rainfall_distinct_factors(engine):
    policy = HeavyRainfallPolicyV1()
    res = policy.evaluate({
        "disaster_type": "Heavy Rainfall",
        "predictor_features_x": {
            "wind_speed": 40.0,
            "pressure": 990.0
        }
    })
    factors = [f["factor"] for f in res.contributing_factors]
    assert "wind_speed" in factors
    assert "pressure" in factors
    assert res.confidence is None
    assert res.probabilities is None

def test_unsupported_hazard_handling(engine):
    event = {
        "disaster_type": "Solar Flare",
        "incident_id": "INC-SOLAR-TEST"
    }
    res = engine.predict_severity(event)
    assert res.get("status") == "unsupported_hazard"
    assert res.get("assessment_method") == "UNSUPPORTED"
