# Phase 2C.1 — V1 Dataset Reconciliation & Discrepancy Audit
**Project**: Ignite (PS20)  
**Document**: `docs/V1_DATASET_RECONCILIATION.md`  
**Phase**: Phase 2C.1 Audit  
**Date**: 2026-09-16  

---

## 1. Executive Summary of Row Discrepancy

- **Phase 2B.8 Report**: 64 Earthquakes (HIGH confidence) + 278 Cyclones (MEDIUM confidence) = 342 total matched events.
- **Phase 2C Training Dataset (`event_level_training.parquet`)**: 66 Earthquakes + 270 Cyclones = **336 total rows**.

### **Audit Findings & Root Cause Analysis**:
1. **Earthquake Count (+2 Discrepancy)**: Phase 2B.8 executive summary reported 64 HIGH-confidence seismic matches. The dataset builder `build_dataset_v4.py` retained 64 HIGH + 2 MEDIUM confidence matches ($Mw \ge 6.0$), bringing total earthquake rows to **66**.
2. **Cyclone Count (-8 Discrepancy)**: Phase 2B.8 summary reported 278 total IBTrACS cyclone matches. 8 of these matched storm events lacked non-null observed outcome targets ($Y_{deaths}, Y_{injured}, Y_{affected}, Y_{damage}$) in EM-DAT. These 8 un-labeled events were correctly filtered out, resulting in **270 valid trainable storm rows**.
