import os
import pandas as pd
import json

DATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v5/event_level_features.parquet"
REPORTS_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity_v2/"
os.makedirs(REPORTS_DIR, exist_ok=True)

df = pd.read_parquet(DATA_PATH)

print("--- V5 PRE-TRAINING PROFILE ---")
print(f"Total Rows: {len(df)}")

fx_rows = list(df['predictor_features_x'])
df_fx = pd.DataFrame(fx_rows)

profile_rows = []
for col in df_fx.columns:
    ser = df_fx[col]
    non_null_c = ser.notna().sum()
    null_c = ser.isna().sum()
    null_pct = round((null_c / len(ser)) * 100, 2)
    profile_rows.append({
        "feature_name": col,
        "total_rows": len(df_fx),
        "non_null_count": non_null_c,
        "null_count": null_c,
        "null_pct": null_pct,
        "unique_count": ser.nunique()
    })

df_prof = pd.DataFrame(profile_rows)
df_prof.to_csv(os.path.join(REPORTS_DIR, "v5_pretraining_profile.csv"), index=False)
print("\nSaved ml/reports/severity_v2/v5_pretraining_profile.csv successfully.")
print(df_prof)
