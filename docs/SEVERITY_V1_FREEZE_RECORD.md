# Severity Engine V1 — Freeze Record & State Register
**Project**: Ignite (PS20)  
**Document**: `docs/SEVERITY_V1_FREEZE_RECORD.md`  
**Phase**: Phase 2C.1 Freeze  
**Status**: IMMUTABLE & FROZEN  
**Date**: 2026-09-16  

---

## 1. Frozen Model & Data Checksums

| Artifact Name | File Path | SHA256 Checksum | Size (Bytes) |
|---|---|---|---|
| **Training Dataset V4** | `ml/data/processed/v4/event_level_training.parquet` | `952a61c2affcebb71583bf0ce1c707798ee3f38121cccbfaf9cdd8ac9d6f9d7a` | 62418 |
| **Model Binary Artifact** | `ml/models/severity_v1/severity_model.joblib` | `b78579adaa4478918a345b1e23876a2740ff035f8e87a79cd196265c5bd2423d` | 130592 |
| **Model Metadata JSON** | `ml/models/severity_v1/model_metadata.json` | `465888aeda89cb677431a2833e79b8b8a60bd5b35cf6b379d292777031fef6df` | 834 |

---

## 2. Frozen Configuration Summary

- **Model Version**: `severity_v1`
- **Selected Model**: `HistGradientBoosting_Classifier`
- **Training Rows**: `336`
- **Earthquake Count**: `66`
- **Cyclone Count**: `270`
- **Primary Metric (Macro F1)**: `0.2497`
- **Random Seed**: `42`
- **Feature List**: `['disaster_type_code', 'seismic_magnitude', 'seismic_depth_km', 'cyclone_max_wind_knots', 'cyclone_min_pressure_mb', 'hazard_intensity_index']`
