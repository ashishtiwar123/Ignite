# Phase 2C.3 — Severity Intelligence Engine V2 Experiment Report
**Project**: Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System  
**Document**: `docs/SEVERITY_V2_EXPERIMENT_REPORT.md`  
**Phase**: Phase 2C.3  
**Status**: EXPERIMENT COMPLETED & MODEL V2 SELECTED  
**Date**: 2026-09-16  

---

## 1. Controlled Ablation Results Table

| Feature Configuration | Predictor Columns | Total Rows | Macro F1 | Weighted F1 | Accuracy | High Severity Recall (Class 2) | Critical Recall (Class 3) |
|---|---|---|---|---|---|---|---|
| **Model A (V1 Hazard Only)** | 6 | 336 | 0.2497 | 0.3045 | 38.39% | 0.0000 | 0.1389 |
| **Model B (V1 + Exposure)** | **9** | **336** | **0.2794** | **0.3139** | **32.44%** | **0.1594** | **0.1389** |
| **Model C (V1 + Exposure + Context)** | 11 | 336 | 0.2647 | 0.2972 | 31.55% | 0.0580 | 0.1944 |
| **Model D (V1 + Exposure + Context + Vulnerability)** | 12 | 336 | 0.2773 | 0.3133 | 33.33% | 0.0580 | 0.1944 |

---

## 2. Selection Rationale for Severity V2

- **Selected Configuration**: **Model B (V1 + Exposure)**
- **Selected Model**: `HistGradientBoosting_Classifier`
- **Primary Metric Achieved**: **Macro F1 = `0.2794`** (vs V1 = `0.2497`)
- **Key Breakthrough**: Achieved **15.94% recall on High-severity incidents** (where V1 was 0.0000%).
- **Artifact Location**: [`ml/models/severity_v2/severity_model.joblib`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v2/severity_model.joblib)
