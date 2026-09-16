# Phase 2B.7.1 — Forensic Training Dataset Audit Report
**Project Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System**  
**Document**: `docs/PHASE_2B7_1_FORENSIC_TRAINING_DATA_AUDIT.md`  
**Phase**: Phase 2B.7.1  
**Status**: AUDITED & COMPLETED  
**Date**: 2026-09-16  

---

## 1. Executive Summary & Forensic Audit Verdict

A rigorous, line-by-line forensic audit was conducted on **Dataset Candidate v3.0** (`canonical_incidents_v3.parquet`, `observed_outcomes_v3.parquet`, `features_v3.parquet`, `training_dataset_candidate_v3.parquet`).

### **FINAL AUDIT DECISION**: `EVENT-LEVEL BASELINE POSSIBLE`

> [!WARNING]  
> **CRITICAL FORENSIC AUDIT FINDING**:  
> The previously claimed count of **13,959 training-eligible rows** is **NOT valid for Point-in-Time future-window ML modeling**.  
> While the **16,764 EM-DAT records contain genuinely real, observed historical disaster outcomes ($Y$)**, the physical predictor features ($X$) for these records were populated with **scalar default placeholders** (e.g., $175.0\text{ mm}$ for Floods, $110.0\text{ knots}$ for Cyclones, $5.8\text{ Mw}$ for Earthquakes, constant population density $280.0$).  
> Furthermore, EM-DAT provides **event-level cumulative totals**, not timestamped progression. Therefore, Dataset v3.0 is an **EVENT-LEVEL IMPACT DATASET**, not a Point-in-Time future prediction dataset.

---

## 2. Direct Answers to the 10 Mandatory Audit Questions

| # | Forensic Audit Question | Audit Finding / Verified Reality |
|---|---|---|
| **1** | **Is 13,959 genuinely valid training data?** | **NO for Point-in-Time ML**; **YES for Event-Level Impact Baseline**. |
| **2** | **How many rows contain real observed Y?** | **16,781 rows** (16,764 EM-DAT + 17 DesInventar). 0 synthetic or imputed outcomes. |
| **3** | **How many rows contain real observed X?** | **573 rows** (565 USGS real seismic magnitude/depth + 8 IBTrACS real wind speed). |
| **4** | **How many have genuine T0?** | **16,781 rows** (based on official EM-DAT disaster `Start Date`). |
| **5** | **How many have valid future Y?** | **0 rows** (EM-DAT records contain aggregate event outcomes, not sub-event time-series progression). |
| **6** | **How many contain placeholder/default X?** | **16,781 rows** (96.7% of feature vectors rely on static hazard/exposure defaults). |
| **7** | **How many contain temporal leakage?** | **0 rows** (Predictor features $X$ contain no outcome variables $Y$). |
| **8** | **How many are event-level vs future-window?** | **16,781 are EVENT-LEVEL IMPACT DATASET**; **0 are Point-in-Time Future-Window**. |
| **9** | **How many are independently labeled?** | **16,781 independent physical disaster events**. |
| **10** | **What is the TRUE final training count?** | **Population F (Point-in-Time ML): 0 rows**.<br>**Population B (Event-Level Baseline): 16,781 rows**. |

---

## 3. Dissecting the Population Breakdown (A through F)

```
========================================================================================
                          FORENSIC DATASET POPULATION METRICS
========================================================================================
Population A: All Canonical Incidents:                         17,354
Population B: Incidents with Real Observed Y:                  16,781  (16,764 EM-DAT + 17 DesInventar)
Population C: Incidents with Genuine Sensor X:                    573  (565 USGS + 8 IBTrACS)
Population D: Incidents with Genuine X + Observed Y:                0  (USGS/EM-DAT unmerged)
Population E: Valid Temporal Relationship (T0 defined):        16,781
Population F: Genuine X + Observed Y + Valid T0 + No Leakage:       0  [POINT-IN-TIME ML]
----------------------------------------------------------------------------------------
EVENT-LEVEL BASELINE TRAINABLE POPULATION:                     16,781  [EVENT-LEVEL BASELINE]
========================================================================================
```

---

## 4. Feature Value Audit: Default / Placeholder Detection

An inspection of `features_v3.parquet` revealed that missing sensor telemetry was replaced with scalar defaults in `build_features_v3.py`:

- **`inform_country_risk_baseline`**: 100% constant (`5.5`) across all 17,354 rows. `[DEFAULT_OR_PLACEHOLDER_FEATURE]`
- **`population_density_sqkm`**: 100% constant (`280.0`) across all 17,354 rows. `[DEFAULT_OR_PLACEHOLDER_FEATURE]`
- **`rain_accum_7d_mm`**: 100% constant (`175.0`) for all 4,250 Flood records; 75.5% missing across overall dataset. `[DEFAULT_OR_PLACEHOLDER_FEATURE]`
- **`cyclone_wind_speed_knots`**: 100% constant (`110.0`) for EM-DAT cyclones; 83.5% missing across overall dataset. `[DEFAULT_OR_PLACEHOLDER_FEATURE]`
- **`seismic_magnitude`**: 92.7% missing (real USGS values present in only 565 rows). `[PARTIALLY_GENUINE_SENSOR]`

---

## 5. Target Value Audit ($Y$)

All 16,781 outcome target vectors derive directly from official sources:
- **Observed Deaths ($Y_{deaths}$)**: 13,511 real observed values (77.9% coverage).
- **Observed Injured ($Y_{injured}$)**: 6,283 real observed values (36.2% coverage).
- **Observed Affected ($Y_{affected}$)**: 7,782 real observed values (44.8% coverage).
- **Observed Financial Damage ($Y_{damage\_usd}$)**: 3,343 real observed values (19.3% coverage).

**0 imputed, 0 derived, and 0 synthetic target values were found.** Missing targets remain strictly `None`/`NaN`.

---

## 6. Distinguishing Dataset Types

Dataset v3.0 MUST be classified as:
**A. EVENT-LEVEL IMPACT DATASET**

It MUST NOT be described as a *Point-in-Time Future-Prediction Dataset* because EM-DAT provides cumulative event totals rather than hourly/daily outcome snapshots after $T_0$.

---

## 7. Artifact Deliverables Created

1. [`docs/PHASE_2B7_1_FORENSIC_TRAINING_DATA_AUDIT.md`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/docs/PHASE_2B7_1_FORENSIC_TRAINING_DATA_AUDIT.md)
2. [`docs/V3_DUPLICATE_EVENT_AUDIT.md`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/docs/V3_DUPLICATE_EVENT_AUDIT.md)
3. [`ml/reports/v3_provenance_matrix.csv`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/reports/v3_provenance_matrix.csv)
