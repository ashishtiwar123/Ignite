import pandas as pd
import json

with open("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v3.json", "r") as f:
    ds_json = json.load(f)

# Sample 100 rows across different sources and hazards
np_rnd = pd.Series(range(len(ds_json)))
sample_indices = list(range(0, 100)) # sample first 100 or stratified

samples = [ds_json[i] for i in range(0, min(100, len(ds_json)))]

matrix_rows = []
for s in ds_json:
    inc_id = s['incident_id']
    sources = s.get('source_records', [])
    src_dataset = sources[0]['source'] if sources else "UNKNOWN"
    src_rec_id = sources[0]['source_id'] if sources else "UNKNOWN"
    hazard = s['hazard_category']
    t0 = s['prediction_timestamp_t0']
    
    outcomes = s.get('observed_outcomes_y', {})
    has_y = s.get('data_quality', {}).get('has_observed_y', False)
    
    feats = s.get('predictor_features_x', {})
    # Check if features are genuine or synthetic default placeholders
    # In build_features_v3.py:
    # inform_country_risk_baseline is constant 5.5
    # population_density_sqkm is constant 280.0
    # rain_accum_7d_mm is constant 175.0 for FLOOD
    # cyclone_wind_speed_knots is constant 110.0 for CYCLONE
    # seismic_magnitude is 5.8 default for EARTHQUAKE if not from USGS
    
    is_emdat = src_dataset == "EM-DAT"
    is_usgs = src_dataset == "USGS"
    
    # Genuine X: Does it come from real telemetry sensor or real country lookup?
    x_genuine = is_usgs or src_dataset == "NOAA_IBTrACS"
    y_genuine = is_emdat or src_dataset == "DesInventar"
    
    # Temporal validity: EM-DAT event start date is T0, but EM-DAT outcome Y is aggregate event total!
    # Therefore, EM-DAT represents EVENT-LEVEL impact, NOT point-in-time future 24h prediction!
    temporal_valid = True if t0 else False
    is_event_level = is_emdat
    
    # Training eligible for point-in-time future ML?
    # NO! Because for EM-DAT rows, X features were artificially filled with scalar defaults (175.0, 110.0, 5.8) 
    # and Y is event-level aggregate total!
    pit_ml_ready = x_genuine and y_genuine and temporal_valid
    event_level_ready = y_genuine
    
    matrix_rows.append({
        "canonical_incident_id": inc_id,
        "outcome_source": src_dataset if y_genuine else "NONE",
        "outcome_source_id": src_rec_id if y_genuine else "NONE",
        "hazard_source": src_dataset if x_genuine else "FALLBACK_DEFAULT",
        "hazard_source_id": src_rec_id if x_genuine else "NONE",
        "exposure_source": "CONSTANT_PLACEHOLDER_280",
        "prediction_time": t0,
        "outcome_time": "EVENT_LEVEL_AGGREGATE",
        "X_verified": x_genuine,
        "Y_verified": y_genuine,
        "temporal_valid": temporal_valid,
        "leakage_free": True, # no Y in X
        "is_event_level_dataset": is_event_level,
        "point_in_time_ml_eligible": pit_ml_ready,
        "event_level_baseline_eligible": event_level_ready
    })

df_mat = pd.DataFrame(matrix_rows)
df_mat.to_csv("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/v3_provenance_matrix.csv", index=False)
print("Saved v3_provenance_matrix.csv successfully.")
print(f"Total rows: {len(df_mat)}")
print(f"Point-in-Time ML Eligible (Genuine X + Genuine Y): {df_mat['point_in_time_ml_eligible'].sum()}")
print(f"Event-Level Baseline Eligible (Real Observed Y): {df_mat['event_level_baseline_eligible'].sum()}")
