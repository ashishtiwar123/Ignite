# Project Ignite (PS20) — Project Scope & System Boundaries

**Project**: Ignite (PS20)  
**Document**: `docs/00_PROJECT_SCOPE.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED & FROZEN  
**Last Updated**: 2026-09-16  

---

## 1. Problem Statement Alignment

### 1.1 What PS20 IS `[VERIFIED]`
**Project Ignite (PS20)** is an enterprise **Disaster & Emergency Response Intelligence & Resource Allocation System**. It provides multi-hazard situation intelligence, impact severity assessment, risk trajectory forecasting, Sphere-based humanitarian needs translation, and constrained resource allocation planning to support emergency responders, humanitarian agencies, and disaster management authorities.

### 1.2 What PS20 IS NOT `[VERIFIED]`
- PS20 is **NOT** exclusively a conflict or political violence analytics platform.
- PS20 is **NOT** a tactical battlefield or military command-and-control software.
- PS20 is **NOT** a direct automated logistics execution engine (it generates optimal allocation plans; human logisticians execute physical shipments).
- PS20 is **NOT** an unstructured social media scraper operating without data validation.

---

## 2. Supported Hazard & Disaster Categories `[VERIFIED]`

The system architecture is designed to support the following multi-hazard categories as defined in international disaster management taxonomies (UNDRR / EM-DAT / IASC):

| Disaster Category | Primary Physical Signals | Data Sources | Impact Characteristics |
| :--- | :--- | :--- | :--- |
| **Flood** | Precipitation, river discharge, inundation extent | Satellite (Copernicus/MODIS), Weather APIs, EM-DAT | Sudden onset, displacement, WASH contamination |
| **Cyclone / Hurricane** | Wind speed, pressure, storm surge, rainfall | Meteorological APIs, NOAA/GDACS, EM-DAT | Massive structural damage, power loss, evacuation |
| **Earthquake** | Seismic magnitude, peak ground acceleration (PGA) | USGS, EMSC API, EM-DAT | Instantaneous destruction, trauma casualties, structural collapse |
| **Wildfire** | Thermal anomalies (MODIS/VIIRS), humidity, wind | NASA FIRMS, Land Cover APIs | Rapid displacement, respiratory crisis, cropland loss |
| **Landslide** | Rainfall accumulation, slope stability, soil moisture | Hydro-meteorological APIs, GDACS | localized complete destruction, road blockades |
| **Drought** | SPI/SPEI indices, vegetation health (NDVI), soil moisture | CHIRPS, FEWS NET, IPC | Slow onset, crop failure, food insecurity, famine |
| **Extreme Weather** | Temperature extremes, heatwaves, freeze events | Global weather reanalysis | Health surge, energy grid disruption |
| **Conflict & Unrest** | Violent events, civilian targeted actions, fatal incidents | ACLED, GDELT | Secondary crisis driver, humanitarian access blockage |

---

## 3. MVP Scope vs. Future Extensions

### 3.1 MVP Scope (Phase 2 & Phase 3 Target) `[VERIFIED]`
1. **Multi-hazard Incident Data Ingestion**: Standardized ingestion of incident reports and hazard indicators.
2. **Derived Impact Severity Engine**: Multi-hazard 0–5 severity scoring based on empirical impact indicators (deaths, injuries, displacement, structural damage).
3. **Subnational Risk Trajectory Forecasting**: ADM2-level risk escalation predictions over 1, 3, and 6-month horizons.
4. **Deterministic Sphere Needs Engine**: Automatic calculation of WASH (water), food rations, and shelter requirements based on predicted affected populations.
5. **Constrained Resource Allocation**: Priority scoring and allocation planning for disaster response logistics.

### 3.2 Out of Scope for Initial MVP `[VERIFIED]`
- Real-time video/drone feed processing.
- Direct automated physical warehouse integration.
- Custom satellite imagery ML model training (uses pre-processed satellite index layers instead).
- Micro-level individual survivor tracking.

### 3.3 Future Extensions `[VERIFIED]`
- High-resolution H3 spatial grid index modeling.
- Real-time supply chain sensor telemetry (GPS vehicle tracking).
- Multi-agency collaborative federated learning.

---

## 4. System Boundaries & Layer Responsibilities

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PROJECT IGNITE BOUNDARIES                     │
├────────────────────────────────────────────────────────────────────────┤
│ 1. AI / LLM Layer      : Report Parsing & Natural Language Explanation │
│ 2. ML Layer            : Severity, Trajectory & Exposure Prediction    │
│ 3. Deterministic Rules : Sphere Standard Needs Calculations             │
│ 4. Optimization Engine : Resource Allocation (OR-Tools)               │
│ 5. Backend (FastAPI)   : API Interface, Persistence, Auth & Workflow     │
│ 6. Frontend UI         : Response Dashboard & Situation Map            │
└────────────────────────────────────────────────────────────────────────┘
```
