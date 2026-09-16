# Phase 2C Model Development Handoff Specification

**Project**: Ignite (PS20 — Multi-Hazard Disaster & Emergency Response System)  
**Document**: `docs/PHASE_2C_MODEL_DEVELOPMENT_HANDOFF.md`  
**Phase**: Phase 2B Dataset Construction $\rightarrow$ Phase 2C Model Development Handoff  
**Status**: APPROVED HANDOFF SPECIFICATION  
**Phase 2B Status**: **GO FOR PHASE 2C**  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Handoff Objectives

This document specifies the exact entry requirements, datasets, targets, feature tensors, and evaluation metrics for incoming engineers initiating **Phase 2C (Model Development)**.

---

## 2. Approved Candidate Training Dataset Specifications

`[VERIFIED]` The candidate dataset is stored at [`ml/data/processed/training_dataset_candidate.json`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate.json):
- **Total Rows**: 13 canonical incident records
- **Multi-Hazard Coverage**: Earthquakes, Floods, Cyclones, Droughts, Wildfires, Landslides
- **Predictor Features ($X \le T_0$)**: `seismic_magnitude`, `seismic_depth_km`, `rain_accum_7d_mm`, `alert_level`, `inform_country_risk_baseline`, `population_density_sqkm`
- **Observed Outcomes ($Y > T_0$)**: `deaths`, `injured`, `displaced`, `total_affected`, `total_damage_usd`, `houses_destroyed`
- **Prediction Timestamp ($T_0$)**: Recorded per incident; strictly precedes outcome observation dates.

---

## 3. Phase 2C Model Development Roadmap

1. **Task 2C-1: Baseline Model Training**: Train baseline LightGBM / XGBoost multi-output regressors predicting observed casualties ($y_{\text{deaths}}, y_{\text{displaced}}$) and ordinal severity class.
2. **Task 2C-2: Group K-Fold Temporal Cross-Validation**: Execute Group K-Fold temporal splits grouped by `iso3` and `year` to prevent spatial/temporal leakage.
3. **Task 2C-3: Evaluation Metrics**: Benchmark model predictions against MAE, Log-Loss, and Zero-Inflation recall scores.
4. **Task 2C-4: SHAP Feature Importance**: Generate global and local SHAP feature importance explanations for top predictors.
5. **Task 2C-5: Sphere Needs Translation Verification**: Wire model-predicted affected populations into the deterministic Sphere needs engine.
