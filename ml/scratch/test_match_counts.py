import pandas as pd
import json

emdat_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/interim/emdat/emdat_normalized.parquet"
usgs_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/usgs/usgs_historical_earthquakes.json"
ibtracs_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/ibtracs/raw_ibtracs.json"

df_em = pd.read_parquet(emdat_path)
print("EM-DAT Disaster Types Breakdown:")
print(df_em['disaster_type'].value_counts())

with open(usgs_path, "r", encoding="utf-8") as f:
    usgs_data = json.load(f)

usgs_feats = usgs_data.get("features", [])
print(f"\nTotal USGS Earthquakes: {len(usgs_feats)}")

with open(ibtracs_path, "r", encoding="utf-8") as f:
    ibtracs_data = json.load(f)
print(f"Total IBTrACS Storms: {len(ibtracs_data)}")
