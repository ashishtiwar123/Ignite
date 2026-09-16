# Phase 2B Engineering Handoff Specification (Model Development)

**Project**: Ignite (PS20)  
**Document**: `docs/PHASE_2B_HANDOFF.md`  
**Phase**: Phase 2A Data Foundation $\rightarrow$ Phase 2B Handoff  
**Status**: APPROVED HANDOFF SPECIFICATION  
**Phase 2A Status**: **GO WITH CONDITIONS**  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Handoff Objectives

This document specifies the exact engineering entry requirements, datasets, target formulas, feature sets, and model baselines for incoming developers initiating **Phase 2B (Model Development)**.

> [!IMPORTANT]
> **Strict Non-Deployment Boundary**: Phase 2B is strictly a model training and offline validation phase. Phase 2B developers must NOT deploy REST APIs, FastAPI web services, or production CI/CD pipelines.

---

## 2. Phase 2B Entry Dataset & Schema Specification

| Approved Dataset | Role | Primary Key | Latency Tier | Feature Status |
| :--- | :--- | :--- | :--- | :--- |
| **USGS Seismic API** | Physical Hazard Signal (Earthquake) | `id` | Tier 0 (< 1 Hour) | `TRAINING-CANDIDATE` |
| **GDACS Alert API** | Physical Hazard Telemetry (Flood, Cyclone, Wildfire, Drought) | `link` | Tier 1 (< 24 Hours) | `TRAINING-CANDIDATE` |
| **ACLED API** | Secondary Conflict Signal | `event_id_cntr` | Tier 2 (14-Day Lag) | `TRAINING-CANDIDATE` (Needs API Key) |
| **IPC / FEWS NET API** | Contextual Vulnerability | `adm2_pcode` | Tier 3 (30-90 Days) | `CONTEXT-ONLY` (Needs API Key) |
| **INFORM Index** | Country Baseline Risk | `iso3` | Tier 4 (Annual) | `CONTEXT-ONLY` |
| **OCHA COD-AB** | Spatial Boundary Backbone | `ADM2_PCODE` | Static Annual | `SPATIAL-BACKBONE` |

---

## 3. Final Target Definition & Formulation `[VERIFIED]`

### Continuous Target (`disi_score`):
$$\text{DISI} = \min \left( 5.0, \; 0.35 \cdot S_{\text{Mortality}} + 0.20 \cdot S_{\text{Morbidity}} + 0.25 \cdot S_{\text{Displacement}} + 0.20 \cdot S_{\text{Damage}} \right)$$

### Ordinal Target Class (`severity_class`):
- `0`: Baseline Normal ($\text{DISI} < 0.5$)
- `1`: Minor / Stressed ($0.5 \le \text{DISI} < 1.5$)
- `2`: Moderate Emergency ($1.5 \le \text{DISI} < 2.5$)
- `3`: Severe Disaster ($2.5 \le \text{DISI} < 3.5$)
- `4`: Extreme Crisis ($3.5 \le \text{DISI} < 4.5$)
- `5`: Catastrophic Emergency ($\text{DISI} \ge 4.5$)

### Risk Trajectory Target ($\Delta \text{Severity}_{t+h}$):
$$\Delta \text{Severity}_{i, t+h} = \text{Severity}_{i, t+h} - \text{Severity}_{i, t}$$
Target Horizons: $h \in \{1, 3, 6\}$ Months.

---

## 4. Phase 2B Task Roadmap

1. **Task 2B-1: Configure API Credentials**: Set `ACLED_API_KEY` and `IPC_API_KEY` in local environment settings.
2. **Task 2B-2: Ingest OCHA Shapefiles**: Load OCHA COD-AB Shapefiles into `ml/data/interim/` to execute Point-in-Polygon spatial joins.
3. **Task 2B-3: Build Feature Matrix**: Run feature engineering routines under `ml/src/temporal/` enforcing source-specific publication latency cutoffs ($T_{\text{pub}} \le T_{\text{pred}} - \delta_{\text{source\_lag}}$).
4. **Task 2B-4: Construct Training Splits**: Generate temporal group train/validation/test splits (e.g., Train: 2018–2023, Val: 2024, Test: 2025–2026).
5. **Task 2B-5: Train Baseline Models**: Train baseline LightGBM / XGBoost classification and regression models for `severity_class` and trajectory momentum $\Delta \text{Severity}_{t+h}$.
6. **Task 2B-6: Evaluate & Audit Errors**: Evaluate models on Macro F1-Score, Log-Loss, and MAE; perform error analysis across disaster categories.
