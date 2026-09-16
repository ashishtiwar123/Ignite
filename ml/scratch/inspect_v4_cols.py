import pandas as pd
import json

v4_parquet = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
df = pd.read_parquet(v4_parquet)

print("V4 Columns:", df.columns.tolist())
print("V4 Sample Row 0:")
sample = df.iloc[0].to_dict()
for k, v in sample.items():
    print(f"  {k}: {v}")
