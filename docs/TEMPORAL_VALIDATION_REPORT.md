# Empirical Temporal Validation & Latency Report

**Project**: Ignite (PS20)  
**Document**: `docs/TEMPORAL_VALIDATION_REPORT.md`  
**Phase**: Phase 2A Data Foundation  
**Status**: COMPLETE  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Latency Validation

Temporal integrity in Project Ignite requires enforcing source-specific publication latency cutoffs to prevent future-data contamination during model training and offline backtesting.

---

## 2. Source-Specific Publication Latency Analysis

| Data Source | Operational Latency Tier | Provider Release Delay ($\delta_{\text{pub}}$) | Tested Feature Cutoff Rule | Temporal Leakage Risk | Status Tag |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **USGS Seismic API** | Tier 0: Real-Time | < 15 Minutes | $T_{\text{occur}} \le T_{\text{pred}} - 1\text{ Hour}$ | None | `[EMPIRICAL]` Validated |
| **GDACS Alert API** | Tier 1: Near Real-Time | 3 to 24 Hours | $T_{\text{occur}} \le T_{\text{pred}} - 24\text{ Hours}$ | Low | `[EMPIRICAL]` Validated |
| **ACLED Conflict API** | Tier 2: Weekly Lagged | 7 to 14 Days | $T_{\text{pub}} \le T_{\text{pred}} - 14\text{ Days}$ | High (Retroactive edits) | `[OFFICIAL DOCUMENTATION]` |
| **IPC Food Insecurity** | Tier 3: Seasonal | 30 to 90 Days | Ingest published valid survey at $T_{\text{pred}}$ | High (Survey publish delay) | `[OFFICIAL DOCUMENTATION]` |

---

## 3. Automated Temporal Leakage Verification `[EMPIRICAL]`

`[EMPIRICAL]` Unit test `test_temporal_leakage_guardrail` in `ml/tests/test_schemas.py` was executed:
- **Test Condition**: Asserts that features published at $T_{\text{pub}} > T_{\text{pred}} - 14\text{ days}$ are strictly rejected during point-in-time snapshot generation.
- **Result**: **PASSED (100%)**.
