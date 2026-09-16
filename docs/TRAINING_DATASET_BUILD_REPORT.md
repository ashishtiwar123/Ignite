# Training Dataset Construction & Quality Report

**Project**: Ignite (PS20)  
**Document**: `docs/TRAINING_DATASET_BUILD_REPORT.md`  
**Phase**: Phase 2B Dataset Construction  
**Status**: COMPLETE  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Build Overview

Phase 2B successfully constructed the candidate historical multi-source training dataset combining **Predictor Features** ($X \le T_0$) with **Observed Future Impact Outcomes** ($Y > T_0$).

---

## 2. Dataset Construction Metrics & Metadata

`[EMPIRICAL]` Output extracted from `ml/reports/training_dataset_metadata.json`:

```json
{
  "dataset_version": "v2.0-candidate-historical",
  "created_at_utc": "2026-09-16T07:27:06.497281",
  "total_records": 13,
  "total_features_count": 6,
  "total_outcomes_count": 6,
  "hazard_counts": {
    "EARTHQUAKE": 6,
    "FLOOD": 2,
    "LANDSLIDE": 2,
    "CYCLONE": 1,
    "DROUGHT": 1,
    "WILDFIRE": 1
  },
  "sources_integrated": ["EM-DAT", "DesInventar", "USGS", "GDACS"],
  "schema_version": "v2.0",
  "prediction_boundary": "STRICT_T0_GUARDRAIL"
}
```

---

## 3. Event Matching & Reconciliation Statistics

`[EMPIRICAL]` Multi-source incident reconciliation results (`ml/src/reconciliation/reconcile_events.py`):
- **Total Canonical Incidents**: 13
- **Direct EM-DAT Matches**: 5 events (38.5%)
- **Subnational DesInventar Matches**: 3 events (23.1%)
- **Seismic Telemetry USGS Matches**: 5 events (38.5%)
- **Matching Confidence Average**: 0.95 (High Confidence)
- **Uncontrolled Fuzzy Matches**: 0 (Strict deterministic IDs and P-codes used)

---

## 4. Null vs. Zero Preservation Analysis `[EMPIRICAL]`

`[EMPIRICAL]` Unit test `test_null_vs_zero_preservation` in `ml/tests/test_dataset_construction.py` was executed:
- **Test Condition**: Asserts that un-reported impact fields (e.g. `injured` in Somalia Drought record) remain strictly set to `null/None` and are **NOT** artificially zero-imputed.
- **Result**: **PASSED (100%)**. Observed zero (`0`) indicates confirmed zero casualties; `null` indicates un-reported data.
