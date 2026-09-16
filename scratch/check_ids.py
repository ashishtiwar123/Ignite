import pandas as pd

with open('ml/reports/severity/test_predictions.csv', 'r') as f:
    v1_lines = f.readlines()

with open('ml/reports/severity_v2/v2_test_predictions.csv', 'r') as f:
    v2_lines = f.readlines()

df_v1 = pd.read_csv('ml/reports/severity/test_predictions.csv')
df_v2 = pd.read_csv('ml/reports/severity_v2/v2_test_predictions.csv')

out = []
out.append(f"V1 raw line count (including header): {len(v1_lines)}")
out.append(f"V2 raw line count (including header): {len(v2_lines)}")
out.append(f"df_v1 shape: {df_v1.shape}")
out.append(f"df_v2 shape: {df_v2.shape}")

# Check if there are blank lines or extra lines at end of files
out.append(f"V1 last 3 raw lines: {repr(v1_lines[-3:])}")
out.append(f"V2 last 3 raw lines: {repr(v2_lines[-3:])}")

# Check V5 dataset parquet
df_v5 = pd.read_parquet('ml/data/processed/v5/event_level_features.parquet')
out.append(f"df_v5 shape: {df_v5.shape}")

with open('scratch/out.txt', 'w') as f:
    f.write('\n'.join(out))

print("Done writing scratch/out.txt")
