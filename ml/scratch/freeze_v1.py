import os
import json
import hashlib
import pandas as pd

MODEL_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v1/"
DATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
FREEZE_DOC = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/docs/SEVERITY_V1_FREEZE_RECORD.md"

def get_file_sha256(filepath):
    if not os.path.exists(filepath):
        return "N/A"
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

model_sha256 = get_file_sha256(os.path.join(MODEL_DIR, "severity_model.joblib"))
meta_sha256 = get_file_sha256(os.path.join(MODEL_DIR, "model_metadata.json"))
data_sha256 = get_file_sha256(DATA_PATH)

df_v4 = pd.read_parquet(DATA_PATH)
with open(os.path.join(MODEL_DIR, "model_metadata.json"), "r") as f:
    meta = json.load(f)

freeze_content = f"""# Severity Engine V1 — Freeze Record & State Register
**Project**: Ignite (PS20)  
**Document**: `docs/SEVERITY_V1_FREEZE_RECORD.md`  
**Phase**: Phase 2C.1 Freeze  
**Status**: IMMUTABLE & FROZEN  
**Date**: 2026-09-16  

---

## 1. Frozen Model & Data Checksums

| Artifact Name | File Path | SHA256 Checksum | Size (Bytes) |
|---|---|---|---|
| **Training Dataset V4** | `ml/data/processed/v4/event_level_training.parquet` | `{data_sha256}` | {os.path.getsize(DATA_PATH)} |
| **Model Binary Artifact** | `ml/models/severity_v1/severity_model.joblib` | `{model_sha256}` | {os.path.getsize(os.path.join(MODEL_DIR, "severity_model.joblib"))} |
| **Model Metadata JSON** | `ml/models/severity_v1/model_metadata.json` | `{meta_sha256}` | {os.path.getsize(os.path.join(MODEL_DIR, "model_metadata.json"))} |

---

## 2. Frozen Configuration Summary

- **Model Version**: `severity_v1`
- **Selected Model**: `{meta.get('selected_model')}`
- **Training Rows**: `{len(df_v4)}`
- **Earthquake Count**: `{len(df_v4[df_v4['disaster_type'] == 'Earthquake'])}`
- **Cyclone Count**: `{len(df_v4[df_v4['disaster_type'] == 'Storm'])}`
- **Primary Metric (Macro F1)**: `{meta.get('primary_metric_value')}`
- **Random Seed**: `42`
- **Feature List**: `{meta.get('feature_list')}`
"""

with open(FREEZE_DOC, "w") as f:
    f.write(freeze_content)

print(f"Created {FREEZE_DOC} successfully.")
print(f"Data SHA256: {data_sha256}")
print(f"Model SHA256: {model_sha256}")
