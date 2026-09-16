import pandas as pd
import numpy as np
import json

DATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
df = pd.read_parquet(DATA_PATH)

target_rows = []
for _, row in df.iterrows():
    y = row['observed_outcomes_y']
    deaths = y.get('deaths') if pd.notna(y.get('deaths')) else 0.0
    injured = y.get('injured') if pd.notna(y.get('injured')) else 0.0
    affected = y.get('total_affected') if pd.notna(y.get('total_affected')) else (y.get('affected') if pd.notna(y.get('affected')) else 0.0)
    damage = y.get('damage_usd_thousands') if pd.notna(y.get('damage_usd_thousands')) else 0.0
    
    impact_score = np.log1p(deaths) + 0.5 * np.log1p(injured) + 0.1 * np.log1p(affected) + 0.2 * np.log1p(damage)
    
    if impact_score < 3.0:
        sev_class = "Low (0)"
        class_idx = 0
    elif impact_score < 7.0:
        sev_class = "Moderate (1)"
        class_idx = 1
    elif impact_score < 11.0:
        sev_class = "High (2)"
        class_idx = 2
    else:
        sev_class = "Critical (3)"
        class_idx = 3
        
    target_rows.append({
        "incident_id": row['incident_id'],
        "disaster_type": row['disaster_type'],
        "country": row['country'],
        "deaths": deaths,
        "injured": injured,
        "affected": affected,
        "damage_usd_thousands": damage,
        "impact_score": round(float(impact_score), 4),
        "severity_class": sev_class,
        "class_idx": class_idx
    })

df_t = pd.DataFrame(target_rows)
df_t.to_csv("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/v1_target_distribution.csv", index=False)
print("Saved v1_target_distribution.csv")

print("\n--- TARGET CLASS DISTRIBUTION ---")
vc = df_t['severity_class'].value_counts().sort_index()
for cls, cnt in vc.items():
    pct = (cnt / len(df_t)) * 100
    print(f"Class: {cls:<15} | Count: {cnt:4d} | Pct: {pct:5.2f}%")

majority_cnt = vc.max()
majority_acc = (majority_cnt / len(df_t)) * 100
print(f"\nMajority Class Baseline Accuracy (Moderate): {majority_acc:.2f}%")
print(f"Random Guessing Accuracy (4 classes): 25.00%")
