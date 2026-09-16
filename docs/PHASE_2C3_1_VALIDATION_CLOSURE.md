# Phase 2C.3.1 — Severity V2 Scientific Validation Closure Report

**Project**: Ignite (PS20) — Agentic Disaster Relief & Emergency Resource Coordinator  
**Phase**: Phase 2C.3.1 Scientific Validation Closure  
**Date**: 2026-09-16  
**Status**: VALIDATION PARTIALLY CLOSED — MATERIAL LIMITATIONS REMAIN  

---

## 1. Existing V2 Status & Artifact Integrity (Frozen)

The existing production Severity V2 model and artifacts are **frozen and immutable**.

| Artifact Name | File Path | SHA-256 Hash | Status |
| :--- | :--- | :--- | :--- |
| **V2 Model Binary** | `ml/models/severity_v2/severity_model.joblib` | `854f82ab818dd47e1da06a8de3def2702ec05575a4855eae117cbb2cd7b92545` | **FROZEN / UNTOUCHED** |
| **V2 Metadata** | `ml/models/severity_v2/model_metadata.json` | `52db31ee0dc0e1084ce9bdc67394e379b98cc6b6931fcff32d2fa833aa357093` | **FROZEN / UNTOUCHED** |
| **V5 Dataset** | `ml/data/processed/v5/event_level_features.parquet` | `41ef998fa5c5f02afc0318d4027d95cfed2976f5c76585d38afb46509b45e654` | **FROZEN / UNTOUCHED** |
| **V1 Model Binary** | `ml/models/severity_v1/severity_model.joblib` | `b78579adaa4478918a345b1e23876a2740ff035f8e87a79cd196265c5bd2423d` | **FROZEN / UNTOUCHED** |
| **V1 Metadata** | `ml/models/severity_v1/model_metadata.json` | `465888aeda89cb677431a2833e79b8b8a60bd5b35cf6b379d292777031fef6df` | **FROZEN / UNTOUCHED** |

---

## 2. Paired Statistical Significance Analysis

A paired bootstrap resampling procedure was executed across the identical 336 evaluation incidents using 10,000 bootstrap iterations (`random_seed=42`).

- **Artifact Report**: [`ml/reports/severity_v2/statistical_significance.csv`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity_v2/statistical_significance.csv)
- **Documentation**: [`docs/SEVERITY_V2_STATISTICAL_SIGNIFICANCE.md`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/docs/SEVERITY_V2_STATISTICAL_SIGNIFICANCE.md)

| Metric | V1 Observed | V2 Observed | Observed Difference | 95% Confidence Interval | Statistical Significance Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `macro_f1` | 0.2497 | 0.2794 | +0.0297 | [-0.0269, +0.0859] | **NOT DEMONSTRATED** |
| `weighted_f1` | 0.3045 | 0.3139 | +0.0093 | [-0.0447, +0.0642] | **NOT DEMONSTRATED** |
| `high_recall` | 0.0000 | 0.1594 | +0.1594 | [+0.0758, +0.2500] | **SUPPORTED BY THIS TEST** |
| `critical_recall` | 0.1389 | 0.1389 | +0.0000 | [-0.1143, +0.1111] | **NOT DEMONSTRATED** |
| `brier` | 0.7115 | 0.7316 | +0.0201 | [-0.0066, +0.0469] | **NOT DEMONSTRATED** |

> [!IMPORTANT]
> The overall macro F1 score gain (+0.0297) is an **observed improvement**, but is **NOT statistically significant** at the 95% confidence level due to the sample size constraint (N=336). High-severity recall improvement (+0.1594) is statistically supported.

---

## 3. Probability Calibration Evaluation

Probability outputs were evaluated for out-of-fold calibration using 5-fold Stratified CV. Calibration models were fitted strictly out-of-fold to prevent target leakage.

- **Calibration Model Artifact**: [`ml/models/severity_v2/calibration/v2_calibrator.joblib`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v2/calibration/v2_calibrator.joblib)
- **Calibration Metadata**: [`ml/models/severity_v2/calibration/calibration_metadata.json`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v2/calibration/calibration_metadata.json)
- **Report**: [`docs/SEVERITY_V2_CALIBRATION_REPORT.md`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/docs/SEVERITY_V2_CALIBRATION_REPORT.md)

| Calibration Pipeline | Brier Score (Lower is better) | Multiclass Log Loss | Method Rationale |
| :--- | :---: | :---: | :--- |
| **RAW V2 (Uncalibrated)** | 0.7316 | 1.3225 | Baseline raw model predictions |
| **CALIBRATED V2 (Sigmoid / Platt)** | **0.6959** | **1.2631** | **SELECTED** (Smooth, non-overfitting scaling on small sample size) |
| **CALIBRATED V2 (Isotonic)** | 0.7027 | 1.2854 | Evaluated |

**Calibration Safety Verification**:
- Zero target leakage: Calibration parameters fitted strictly on training folds.
- Model immutability preserved: Production `severity_model.joblib` binary remains untouched.

---

## 4. SHAP / Model Explainability Implementation

Model explainability has been implemented for frozen V2 in [`ml/src/models/severity_v2/explainer_v2.py`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/src/models/severity_v2/explainer_v2.py).

- **Structured Output**: Exposes `severity_class`, `severity_label`, `probabilities`, and `top_contributing_features` (feature name, value, contribution, direction, rank).
- **Safety Checks**: Verified deterministic outputs, target variable non-leakage, and explicit fail-safe errors for unsupported hazards.
- **Example Artifact**: [`ml/reports/severity_v2/example_explanations.json`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity_v2/example_explanations.json)

---

## 5. Candidate Model Benchmark Audit

A secondary baseline model audit was conducted across identical 5-fold CV splits on Dataset V5 (N=336).

- **Report**: [`ml/reports/severity_v2/candidate_benchmark.csv`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity_v2/candidate_benchmark.csv)

| Candidate Model | Macro F1 | Weighted F1 | Accuracy | Brier Score | Production Replacement |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **HistGradientBoosting (V2 Production)** | 0.2794 | 0.3139 | 32.44% | 0.7316 | **RETAINED** |
| **XGBoost** | 0.3175 | 0.3551 | 36.90% | 0.7657 | NO (Higher Brier score, marginal difference) |
| **RandomForest** | 0.2335 | 0.3051 | 34.23% | 0.7228 | NO |
| **ExtraTrees** | 0.2036 | 0.2762 | 34.52% | 0.7203 | NO |

---

## 6. Remaining Limitations & Hazards Scope

1. **Dataset Size Constraint**: Total dataset size is small (N=336), limiting statistical power for macro classification F1 significance testing.
2. **Hazard Scope**: Genuine supported hazard scope remains strictly **Earthquake** and **Storm/Cyclone**.
3. **Country-Level Context Terminology**: World Bank national metrics (`country_population`, `population_density_sqkm`) reflect **country-level demographic context**, NOT high-resolution physical hazard footprint exposure.
4. **Generalization**: Unseen disaster categories (floods, wildfires, landslides) cannot be predicted with this model.

---

## 7. Final Operational Decision

**FINAL DECISION**:
### **B. VALIDATION PARTIALLY CLOSED — MATERIAL LIMITATIONS REMAIN**

---

## 8. Final Summary Table

```
V2 MODEL:               FROZEN
STATISTICAL SIGNIFICANCE: NOT SUPPORTED (FOR MACRO F1) / SUPPORTED (FOR HIGH RECALL)
CALIBRATION:            ADEQUATE
EXPLAINABILITY:         PASS
MODEL BENCHMARK:        COMPLETE
LEAKAGE:                PASS
SYNTHETIC DATA:         NONE
V1 PRESERVED:           YES
TESTS:                  ALL PASSED
SUPPORTED HAZARDS:      [Earthquake, Storm]
REMAINING LIMITATIONS:  [Small sample size N=336, Country-level demographic context proxy, Limited 2-hazard scope]
FINAL DECISION:         B
NEXT RECOMMENDED PHASE: High-resolution spatial hazard footprint integration (Phase 2C.4) and real flood/landslide telemetry data expansion.
```
