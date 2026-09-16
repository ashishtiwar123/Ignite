# Phase 2C — Severity Engine V1 Experiment Report
**Project Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System**  
**Document**: `docs/SEVERITY_MODEL_EXPERIMENT_REPORT.md`  
**Phase**: Phase 2C  
**Status**: EXPERIMENT COMPLETED & MODEL SELECTED  
**Date**: 2026-09-16  

---

## 1. Executive Summary

Phase 2C constructed the **Severity Intelligence Engine V1** trained strictly on the verified **336 $V4.0$ event-level records** (`event_level_training.parquet`) consisting of 66 Earthquake events (USGS matched) and 270 Storm/Cyclone events (NOAA IBTrACS matched).

```
========================================================================================
                          SEVERITY ENGINE V1 MODEL COMPARISON SUMMARY
========================================================================================
TRAINING DATASET:                             336 Verified Rows (V4.0 Purged Data)
HAZARD COVERAGE:                              Earthquake (66) & Tropical Cyclone (270)
VALIDATION METHODOLOGY:                       Stratified 5-Fold Cross-Validation
TARGET FORMULATION:                           Ordinal Severity Class (0: Low to 3: Critical)
PRIMARY EVALUATION METRIC:                    Macro F1 Score (Accounting for Class Imbalance)
----------------------------------------------------------------------------------------
MODEL COMPARISON RESULTS:
  - HistGradientBoosting Classifier:           Macro F1 = 0.2497 | Weighted F1 = 0.3045 | Acc = 38.39%
  - XGBoost Classifier:                        Macro F1 = 0.2398 | Weighted F1 = 0.2995 | Acc = 39.29%
  - Random Forest Classifier:                  Macro F1 = 0.2111 | Weighted F1 = 0.2806 | Acc = 37.50%
  - ExtraTrees Classifier:                     Macro F1 = 0.1665 | Weighted F1 = 0.2476 | Acc = 37.80%
----------------------------------------------------------------------------------------
SELECTED PRODUCTION MODEL:                    HistGradientBoosting_Classifier
========================================================================================
```

---

## 2. Selection Criterion & Rationale

- **Primary Criterion**: **Macro F1 Score** across 4 ordinal severity classes (Low, Moderate, High, Critical) under 5-Fold Stratified Cross-Validation.
- **Selection**: **HistGradientBoostingClassifier** achieved the highest Macro F1 score ($0.2497$), outperforming XGBoost ($0.2398$) and Random Forest ($0.2111$).

---

## 3. Artifact Locations

- Production Model Binary: [`ml/models/severity_v1/severity_model.joblib`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v1/severity_model.joblib)
- Metadata & Feature List: [`ml/models/severity_v1/model_metadata.json`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v1/model_metadata.json)
- Comparison Table: [`ml/reports/severity/model_comparison.csv`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity/model_comparison.csv)
- Test Predictions: [`ml/reports/severity/test_predictions.csv`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity/test_predictions.csv)
