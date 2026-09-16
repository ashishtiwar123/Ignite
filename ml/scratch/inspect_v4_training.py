import pandas as pd
import json

v4_parquet = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
df = pd.read_parquet(v4_parquet)

print("--- V4 EVENT LEVEL TRAINING DATASET INSPECTION ---")
print(f"Total Rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

print("\nDisaster Types:")
print(df['disaster_type'].value_counts())

print("\nHazard Sources:")
print(df['hazard_source'].value_counts())

print("\nMatch Confidence:")
print(df['match_confidence'].value_counts())

# Inspect predictor features X structure
features_sample = df['predictor_features_x'].iloc[0]
print("\nSample Predictor Features X (Earthquake):", features_sample)

cyclone_sample = df[df['hazard_source'] == 'NOAA_IBTrACS']['predictor_features_x'].iloc[0]
print("Sample Predictor Features X (Cyclone):", cyclone_sample)

# Inspect observed outcomes Y
outcomes_df = pd.DataFrame(list(df['observed_outcomes_y']))
print("\nObserved Outcomes Y Non-Null Counts & Describe:")
print(outcomes_df.describe().T[['count', 'min', 'mean', '50%', 'max']])

# Save feature inventory
inv = {
    "total_training_rows": len(df),
    "columns": list(df.columns),
    "disaster_types": df['disaster_type'].value_counts().to_dict(),
    "hazard_sources": df['hazard_source'].value_counts().to_dict(),
    "target_stats": outcomes_df.describe().T[['count', 'min', 'mean', '50%', 'max']].to_dict()
}
with open("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/v4_feature_inventory.json", "w") as f:
    json.dump(inv, f, indent=2, default=str)
print("\nSaved v4_feature_inventory.json")
