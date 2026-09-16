# Phase 2B.8 — Feature Availability & Leakage Audit Report
**Project Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System**  
**Document**: `docs/FEATURE_AVAILABILITY_AUDIT.md`  
**Phase**: Phase 2B.8  
**Status**: VERIFIED & PASSED  
**Date**: 2026-09-16  

---

## 1. Feature Classification Matrix

| Feature | Source | Availability Timing | Classification | Allowed in X? | Reason |
|---|---|---|---|---|---|
| `seismic_magnitude` | USGS | At event initiation ($T_0$) | `PRE_EVENT` / `AT_EVENT` | **YES** | Physical telemetry available at initial trigger |
| `seismic_depth_km` | USGS | At event initiation ($T_0$) | `PRE_EVENT` / `AT_EVENT` | **YES** | Physical telemetry available at initial trigger |
| `cyclone_max_wind_knots` | NOAA IBTrACS | At event landfall ($T_0$) | `PRE_EVENT` / `AT_EVENT` | **YES** | Meteorological observation before/at landfall |
| `cyclone_min_pressure_mb` | NOAA IBTrACS | At event landfall ($T_0$) | `PRE_EVENT` / `AT_EVENT` | **YES** | Meteorological observation before/at landfall |
| `total_deaths` | EM-DAT | Cumulative post-event | `POST_EVENT` | **NO (TARGET Y ONLY)** | Disaster outcome |
| `total_injured` | EM-DAT | Cumulative post-event | `POST_EVENT` | **NO (TARGET Y ONLY)** | Disaster outcome |
| `total_affected` | EM-DAT | Cumulative post-event | `POST_EVENT` | **NO (TARGET Y ONLY)** | Disaster outcome |
| `total_damage_usd` | EM-DAT | Cumulative post-event | `POST_EVENT` | **NO (TARGET Y ONLY)** | Disaster outcome |
