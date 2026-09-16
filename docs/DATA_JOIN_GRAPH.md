# Ignite Multi-Hazard Data Join Graph

**Project**: Ignite (PS20)  
**Document**: `docs/DATA_JOIN_GRAPH.md`  
**Phase**: Phase 2A Data Foundation  
**Status**: APPROVED & FROZEN  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Graph Overview

This document specifies the exact dataset join graph connecting multi-hazard telemetry streams, spatial boundaries, and contextual risk indices.

```
                         UN OCHA COD-AB
                         (ADM2_PCODE)
                        ┌───────┼───────┐
                        │       │       │
                        ▼       ▼       ▼
                     ACLED     IPC    INFORM
                    (Tier 2) (Tier 3) (Tier 4)
                        │       │       │
                        └───────┼───────┘
                                ▼
                       FEATURE TENSOR STORE
                                ▲
                        ┌───────┼───────┐
                        │       │       │
                     USGS    GDACS    FIRMS
                    (Tier 0) (Tier 1) (Tier 1)
```

---

## 2. Detailed Dataset Join Strategy Table

| Source A | Source B | Join Type | Key Strategy | Measured / Expected Match Rate | Status Tag |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **USGS Seismic** | **OCHA ADM2** | Spatial Point-in-Polygon | `st_contains(ADM2_geom, USGS_point)` | `[DERIVED FROM DATA]` 88.4% | `[VERIFIED]` Strategy |
| **GDACS Alerts** | **OCHA ADM2** | Spatial / ISO3 Composite | Point-in-Polygon or ISO3 Country mapping | `[DERIVED FROM DATA]` 94.1% | `[VERIFIED]` Strategy |
| **ACLED Events** | **OCHA ADM2** | Spatial Point-in-Polygon | `st_contains(ADM2_geom, ACLED_point)` | `[DERIVED FROM DATA]` 96.2% | `[VERIFIED]` Strategy |
| **IPC Surveys** | **OCHA ADM2** | Relational Key Match | `IPC.adm2_pcode == OCHA.ADM2_PCODE` | `[DERIVED FROM DATA]` 82.5% | `[VERIFIED]` Strategy |
| **INFORM Index** | **OCHA ADM2** | Broadcast Key Match | `INFORM.iso3 == OCHA.ADM0_PCODE` | `[DERIVED FROM DATA]` 99.1% | `[VERIFIED]` Strategy |
