import pandas as pd
import json
import numpy as np

canonical_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents_v3.parquet"
outcomes_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes_v3.parquet"
features_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/features_v3.parquet"
dataset_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v3.parquet"

df_can = pd.read_parquet(canonical_path)
df_out = pd.read_parquet(outcomes_path)
df_feat = pd.read_parquet(features_path)
df_ds = pd.read_parquet(dataset_path)

print("--- 1. FILE & ROW COUNTS ---")
print(f"Canonical incidents v3: {len(df_can)} rows, {df_can['incident_id'].nunique()} unique IDs")
print(f"Observed outcomes v3:  {len(df_out)} rows, {df_out['incident_id'].nunique()} unique IDs")
print(f"Features v3:           {len(df_feat)} rows, {df_feat['incident_id'].nunique()} unique IDs")
print(f"Dataset candidate v3:  {len(df_ds)} rows, {df_ds['incident_id'].nunique()} unique IDs")

print("\n--- 2. CANONICAL INCIDENT SOURCE BREAKDOWN ---")
# Count by matching_method and source
print(df_can['matching_method'].value_counts())
print("\nReconciliation Status:")
print(df_can['reconciliation_status'].value_counts())

# Single vs multi source
def get_source_name(rec_list):
    if len(rec_list) == 0:
        return "NONE"
    return rec_list[0].get('source')

df_can['primary_source'] = df_can['source_records'].apply(get_source_name)
print("\nPrimary Source Distribution in Canonical:")
print(df_can['primary_source'].value_counts())

print("\n--- 3. FEATURE VALUE AUDIT (DEFAULT / PLACEHOLDER DETECTION) ---")
with open("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/features_v3.json", "r") as f:
    feat_json = json.load(f)

df_fx = pd.DataFrame([r['predictor_features_x'] for r in feat_json])
df_fx['hazard_category'] = [r['hazard_category'] for r in feat_json]

for col in df_fx.columns:
    if col == 'hazard_category':
        continue
    ser = df_fx[col]
    n_total = len(ser)
    n_null = ser.isna().sum()
    null_pct = (n_null / n_total) * 100
    vc = ser.value_counts(dropna=False)
    most_common_val = vc.index[0] if len(vc) > 0 else None
    most_common_freq = vc.iloc[0] if len(vc) > 0 else 0
    most_common_pct = (most_common_freq / n_total) * 100
    print(f"Feature: {col:<30} | Missing: {null_pct:5.1f}% | Top Val: {str(most_common_val):<10} ({most_common_pct:5.1f}%) | Unique: {ser.nunique()}")

print("\n--- 4. TARGET VALUE AUDIT (OBSERVED VS DERIVED/IMPUTED/SYNTHETIC) ---")
with open("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes_v3.json", "r") as f:
    out_json = json.load(f)

df_y = pd.DataFrame([r['observed_outcomes'] for r in out_json])
for col in df_y.columns:
    ser = df_y[col]
    n_total = len(ser)
    n_non_null = ser.notna().sum()
    pct = (n_non_null / n_total) * 100
    print(f"Target: {col:<28} | Observed Non-Null: {n_non_null:5d} ({pct:5.1f}%) | Missing: {n_total - n_non_null:5d}")

print("\n--- 5. TRAINING ELIGIBILITY CLASSIFICATION RE-EVALUATION ---")
with open("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v3.json", "r") as f:
    ds_json = json.load(f)

df_elig = pd.DataFrame(ds_json)
print(df_elig['training_eligibility'].value_counts())

