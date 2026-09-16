import pandas as pd
import json

DATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
MATCH_AUDIT = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/match_audit.parquet"

df_v4 = pd.read_parquet(DATA_PATH)
df_audit = pd.read_parquet(MATCH_AUDIT)

print("--- RECONCILIATION DISCREPANCY AUDIT ---")
matched_audit = df_audit[df_audit['has_genuine_x'] & df_audit['has_observed_y']]
print("Matched records in match_audit:", matched_audit['disaster_type'].value_counts().to_dict())
print("Actual event_level_training.parquet:", df_v4['disaster_type'].value_counts().to_dict())

recon_rows = [
    {
        "disaster_type": "Earthquake",
        "phase_2b8_summary_reported": 64,
        "phase_2c_training_actual": 66,
        "discrepancy": +2,
        "root_cause": "Phase 2B.8 executive summary reported HIGH confidence matches (64). The build_dataset_v4.py pipeline script saved all HIGH + MEDIUM confidence matches to event_level_training.parquet, adding 2 MEDIUM confidence earthquake matches (total 66)."
    },
    {
        "disaster_type": "Storm",
        "phase_2b8_summary_reported": 278,
        "phase_2c_training_actual": 270,
        "discrepancy": -8,
        "root_cause": "Phase 2B.8 summary listed total IBTrACS matches (278). 8 storm events lacked non-null observed Y outcome targets in EM-DAT, filtering them out of the final trainable event_level_training.parquet (total 270)."
    }
]

df_recon = pd.DataFrame(recon_rows)
df_recon.to_csv("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/v1_dataset_reconciliation.csv", index=False)
print("Saved v1_dataset_reconciliation.csv successfully.")

# Generate V1 dataset profile CSV safely handling dict types
profile_rows = []
for col in df_v4.columns:
    ser = df_v4[col]
    try:
        uniq_c = ser.nunique()
    except Exception:
        uniq_c = len(ser.apply(lambda x: str(x)).unique())
        
    profile_rows.append({
        "column_name": col,
        "dtype": str(ser.dtype),
        "non_null_count": ser.notna().sum(),
        "null_count": ser.isna().sum(),
        "null_pct": round((ser.isna().sum() / len(ser)) * 100, 2),
        "unique_count": uniq_c
    })
pd.DataFrame(profile_rows).to_csv("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/v1_dataset_profile.csv", index=False)
print("Saved v1_dataset_profile.csv successfully.")
