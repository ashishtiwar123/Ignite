# Phase 2 Engineering Handoff Manual & Implementation Order

**Project**: Ignite (PS20)  
**Document**: `docs/PHASE_2_HANDOFF.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED & FROZEN HANDOFF MANUAL  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Core Directives

This document defines the authoritative entry manual for developers initiating **Phase 2**. 

> [!IMPORTANT]
> **Strict Sequence Directive**: Phase 2 implementation MUST follow the 14-step sequential roadmap below. Phase 2 does NOT begin with model training or FastAPI web serving. FastAPI, OR-Tools UI, and production deployment remain strictly outside Phase 2 scope.

---

## 2. Mandatory 14-Step Phase 2 Implementation Order

```
[1. Data Ingestion] ──► [2. Raw Preservation] ──► [3. Data Validation] ──► [4. Canonical Schema]
                                                                                │
[8. Feature Eng] ◄── [7. Temporal Policy] ◄── [6. Spatial Harmonize] ◄── [5. Dataset Profiling]
       │
       ▼
[9. Target Construction] ──► [10. Data Splits] ──► [11. Baseline Model] ──► [12. Evaluation]
                                                                                │
[14. Iterative Improvement] ◄──────────────────────────────────────────── [13. Error Analysis]
```

### Step 1: Data Ingestion Pipeline Setup (`[UNVERIFIED]` Ingestors)
Implement raw API fetcher scripts (`Ignite/ml/ingestion/`) for USGS seismic events, Copernicus/GDACS hydromet telemetry, and ACLED conflict logs. Store response payloads in immutable local raw landing storage.

### Step 2: Raw Data Preservation
Establish append-only raw storage (`Ignite/data/raw/`) preserving original JSON/CSV API payloads without modification.

### Step 3: Data Validation Engine
Implement Pydantic schema validation asserting data type integrity, coordinate range checks (Latitude \([-90, 90]\), Longitude \([-180, 180]\)), and missing value detection.

### Step 4: Canonical Schema Transformation
Map validated raw records into canonical internal schema contracts (`Ignite/docs/schemas/`).

### Step 5: Dataset Profiling & Anomaly Reporting
Execute automated data profiling scripts measuring empirical null rates, spatial coverage distributions, and temporal gap frequencies.

### Step 6: Spatial Harmonization
Implement spatial join routines mapping point coordinates and hazard rasters to standardized OCHA `ADM2_PCODE` polygons and Uber `H3_INDEX` grid cells.

### Step 7: Temporal Availability & Lag Enforcement
Implement source-specific latency filters enforcing mandatory publication cutoff rules ($T_{\text{pub}} \le T_{\text{pred}} - \delta_{\text{source\_lag}}$) per `docs/TEMPORAL_DATA_POLICY.md`.

### Step 8: Multi-Resolution Feature Engineering
Construct rolling temporal feature extractors (1-month, 3-month, 6-month rolling sums/means) for strategic Track A features, and daily window features for operational Track B.

### Step 9: Derived Impact Severity Target Construction
Implement the `Derived_Impact_Severity_Index` (`DISI`) calculation script synthesizing normalized mortality, morbidity, displacement, and structural damage metrics per `docs/SEVERITY_TARGET_SPECIFICATION.md`.

### Step 10: Leakage-Free Dataset Split Generation
Generate temporal train/validation/test splits (e.g., Train: 2015-2022, Val: 2023, Test: 2024-2025). Spatial group splits must ensure zero spatial contagion leakage between training and testing sets.

### Step 11: Baseline Model Implementation
Train simple, interpretable baseline models (e.g. Heuristic Rules, Linear/Logistic Regression, and baseline LightGBM/XGBoost) predicting severity class and 1/3/6-month trajectory escalation.

### Step 12: Rigorous Evaluation
Evaluate baseline models against standardized metrics: Macro F1-score, Log-Loss, Mean Absolute Error (MAE), and Zero-Inflation recall metrics.

### Step 13: Empirical Error Analysis
Inspect false positive and false negative prediction errors across disaster categories (Flood vs Earthquake vs Conflict) and log error sources.

### Step 14: Model Tuning & Iterative Improvement
Iterate on hyperparameter optimization, class re-weighting (Focal Loss), and feature selection.

---

## 3. Strict Prohibitions & Out of Scope for Phase 2 `[VERIFIED]`

Developers are strictly **PROHIBITED** from building:
- ❌ **FastAPI Backend Services**: No REST API routes or web servers in Phase 2.
- ❌ **OR-Tools Logistics Solvers**: No MILP routing code in Phase 2.
- ❌ **Frontend Dashboard UI**: No web interfaces or React/Vue code in Phase 2.
- ❌ **Synthetic Training Data**: No artificial data generators; model training must use real ingested data streams.
- ❌ **Automated Production Deployment**: No continuous retraining CI/CD pipelines.
