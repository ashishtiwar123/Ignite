import pytest
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/src/targets"))
from compute_disi_target import calculate_disi_score

def test_disi_target_bounds():
    res = calculate_disi_score(deaths=0, injured=0, displaced=0, damaged_structures=0)
    assert res["disi_score"] == 0.0
    assert res["severity_class"] == 0
    
    res_max = calculate_disi_score(deaths=10000, injured=50000, displaced=500000, damaged_structures=100000)
    assert res_max["disi_score"] <= 5.0
    assert res_max["severity_class"] <= 5

def test_temporal_leakage_guardrail():
    prediction_time = datetime(2026, 9, 16, 0, 0, 0)
    acled_lag_days = 14
    max_allowed_pub_date = datetime(2026, 9, 2, 0, 0, 0)
    
    # Feature published after cutoff must be rejected
    invalid_pub_date = datetime(2026, 9, 10, 0, 0, 0)
    assert invalid_pub_date > max_allowed_pub_date, "Feature published after lag cutoff violates temporal leakage guardrail"

def test_pcode_format_regex():
    import re
    pcode_pattern = re.compile(r"^[A-Z]{3}[0-9]{6}$")
    assert pcode_pattern.match("SDN001002") is not None
    assert pcode_pattern.match("INVALID_PCODE") is None
