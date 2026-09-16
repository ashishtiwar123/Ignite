import pandas as pd
import json

DATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v5/event_level_features.parquet"
PRED_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity_v2/v2_test_predictions.csv"

df_v5 = pd.read_parquet(DATA_PATH)
df_p = pd.read_csv(PRED_PATH)

df_p['is_correct'] = df_p['severity_class'] == df_p['predicted_class']
df_p['error'] = df_p['predicted_class'] - df_p['severity_class']

print("--- SEVERITY V2 CONFUSION MATRIX ---")
cm = pd.crosstab(df_p['severity_class'], df_p['predicted_class'], rownames=['Actual'], colnames=['Predicted'])
print(cm)

print("\nSevere Events Underpredicted (Actual High/Critical predicted as Low/Moderate):")
underpred = df_p[(df_p['severity_class'] >= 2) & (df_p['predicted_class'] <= 1)]
print(f"V2 Underpredicted Severe Count: {len(underpred)} out of 105 (vs V1 was 100 out of 105)")

err_rows = []
for _, row in df_p.iterrows():
    err_rows.append({
        "incident_id": row['incident_id'],
        "disaster_type": row['disaster_type'],
        "country": row['country'],
        "actual_class": row['severity_class'],
        "predicted_class": row['predicted_class'],
        "error_magnitude": abs(row['error']),
        "is_correct": row['is_correct']
    })

pd.DataFrame(err_rows).to_csv("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity_v2/v2_error_analysis.csv", index=False)
print("Saved v2_error_analysis.csv successfully.")
