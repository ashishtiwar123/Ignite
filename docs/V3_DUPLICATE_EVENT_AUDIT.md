# Phase 2B.7.1 — Forensic Training Dataset Audit & Duplicate Event Analysis
**Project Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System**  
**Document**: `docs/V3_DUPLICATE_EVENT_AUDIT.md`  
**Phase**: Phase 2B.7.1 Audit  
**Status**: AUDITED & COMPLETED  
**Date**: 2026-09-16  

---

## 1. Executive Summary

A forensic cross-source duplicate analysis was conducted across the **17,354 canonical incidents** in Dataset v3.0.

- **Primary Source (EM-DAT)**: 16,764 unique records. All 16,764 possess unique `source_record_id` values (`DisNo.`). **0 internal EM-DAT duplicate IDs**.
- **Secondary Source (USGS)**: 565 seismic events ($Mw \ge 6.0$). All 565 possess unique USGS event IDs. **0 internal USGS duplicate IDs**.
- **DesInventar & IBTrACS**: 17 and 8 unique records respectively. **0 internal duplicates**.

---

## 2. Cross-Source Overlap & Matching Potential

While each dataset possesses zero internal duplicate record IDs, cross-source spatial/temporal matching reveals:

1. **EM-DAT $\leftrightarrow$ USGS (Earthquakes)**:
   - Out of 565 major USGS seismic events ($Mw \ge 6.0$), approximately **45 major earthquakes** coincide spatially (same country/region) and temporally ($\pm 3$ days) with EM-DAT earthquake records (e.g., Turkey Mw 7.8 Feb 2023, Japan Tohoku 2011).
   - In Dataset v3.0, these currently exist as separate canonical entities (`INC-EMDAT-...` holding real outcome $Y$, and `INC-USGS-...` holding real seismic $X$). They are **unmerged**.

2. **EM-DAT $\leftrightarrow$ IBTrACS (Tropical Cyclones)**:
   - 8 IBTrACS cyclone records (`INC-IBTRACS-...`) represent physical tracks of major cyclones recorded in EM-DAT (e.g., Cyclone Idai 2019). Currently unmerged.

---

## 3. Duplicate & Unmatched Status Summary

- **Confirmed Duplicate Record IDs**: **0**
- **Unmerged Cross-Source Spatial/Temporal Overlaps**: **~53 candidate pairs**
- **Independent Single-Source Incidents**: **17,301 incidents**
