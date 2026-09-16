import pandas as pd
import numpy as np

DATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
PRED_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity/test_predictions.csv"

df = pd.read_parquet(DATA_PATH)
df_p = pd.read_csv(PRED_PATH)

print("--- ERROR ANALYSIS ---")
df_p['is_correct'] = df_p['severity_class'] == df_p['predicted_class']
df_p['error'] = df_p['predicted_class'] - df_p['severity_class']

print("Accuracy:", df_p['is_correct'].mean())
print("\nConfusion Matrix:")
print(pd.crosstab(df_p['severity_class'], df_p['predicted_class'], rownames=['Actual'], colnames=['Predicted']))

# Top severe events predicted as Low or Moderate
severe_underpredicted = df_p[(df_p['severity_class'] >= 2) & (df_p['predicted_class'] <= 1)]
print(f"\nSevere Events (High/Critical) Underpredicted as Low/Moderate: {len(severe_underpredicted)}")

err_rows = []
for _, row in df_p.iterrows():
    err_rows.append({
        "incident_id": row['incident_id'],
        "hazard_type": row['hazard_type'],
        "country": row['country'],
        "actual_impact_score": row['impact_score'],
        "actual_class": row['severity_class'],
        "predicted_class": row['predicted_class'],
        "error_magnitude": abs(row['error']),
        "is_correct": row['is_correct'],
        "prob_correct_class": row[f"prob_{['low', 'moderate', 'high', 'critical'][row['severity_class']]}"]
    })

df_err = pd.DataFrame(err_rows)
df_err.to_csv("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/v1_error_analysis.csv", index=False)
print("Saved v1_error_analysis.csv successfully.")
