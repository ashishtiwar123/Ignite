import pandas as pd
import json

V5_PARQUET = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v5/event_level_features.parquet"
df = pd.read_parquet(V5_PARQUET)

suspicious_rows = []

for col in ["country_population", "population_density_sqkm", "urban_population_pct", "poverty_headcount_pct"]:
    vals = [r.get(col) for r in df['predictor_features_x'] if r.get(col) is not None]
    ser = pd.Series(vals)
    n_total = len(ser)
    vc = ser.value_counts()
    top_val = vc.index[0] if len(vc) > 0 else None
    top_freq = vc.iloc[0] if len(vc) > 0 else 0
    top_pct = round((top_freq / n_total) * 100, 2) if n_total > 0 else 0
    
    suspicious_rows.append({
        "feature": col,
        "total_non_null": n_total,
        "unique_values": ser.nunique(),
        "most_frequent_value": top_val,
        "most_frequent_count": top_freq,
        "most_frequent_pct": top_pct,
        "is_suspicious_constant": top_pct > 30.0 # Flag if >30% identical values
    })

df_susp = pd.DataFrame(suspicious_rows)
df_susp.to_csv("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/v5_suspicious_feature_values.csv", index=False)
print("Saved v5_suspicious_feature_values.csv successfully.")
print(df_susp)
