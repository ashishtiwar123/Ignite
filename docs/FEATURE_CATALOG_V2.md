# Feature Catalog V2.0 (Severity Engine Expansion)
**Project**: Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System  
**Document**: `docs/FEATURE_CATALOG_V2.md`  
**Phase**: Phase 2C.2  
**Status**: APPROVED & FROZEN  
**Date**: 2026-09-16  

---

## 1. Complete Feature Group Classification

| Feature Name | Feature Group | Source Dataset | Formula / Definition | Unit | Temporal Class | Allowed Hazards |
|---|---|---|---|---|---|---|
| `seismic_magnitude` | `HAZARD` | USGS GeoJSON API | Direct moment magnitude ($Mw$) | $Mw$ | `AT_EVENT` ($T_0$) | Earthquake |
| `seismic_depth_km` | `HAZARD` | USGS GeoJSON API | Focal depth in km | km | `AT_EVENT` ($T_0$) | Earthquake |
| `cyclone_max_wind_knots` | `HAZARD` | NOAA IBTrACS | Max sustained wind speed | knots | `AT_EVENT` ($T_0$) | Storm / Cyclone |
| `cyclone_min_pressure_mb` | `HAZARD` | NOAA IBTrACS | Central barometric pressure | mb | `AT_EVENT` ($T_0$) | Storm / Cyclone |
| `country_population` | `EXPOSURE` | World Bank API (`SP.POP.TOTL`) | Country historical total population | Persons | `PRE_EVENT` ($Y_{event}$) | All Hazards |
| `population_density_sqkm` | `EXPOSURE` | World Bank API (`EN.POP.DNST`) | Historical population density | Persons / $\text{km}^2$ | `PRE_EVENT` ($Y_{event}$) | All Hazards |
| `urban_population_pct` | `EXPOSURE` | World Bank API (`SP.URB.TOTL.IN.ZS`) | Percentage of population in urban areas | % | `PRE_EVENT` ($Y_{event}$) | All Hazards |
| `poverty_headcount_pct` | `VULNERABILITY` | World Bank API (`SI.POV.NAHC`) | National poverty headcount ratio | % | `PRE_EVENT` ($Y_{event}$) | All Hazards |
| `log_population_exposure` | `DERIVED_EXPOSURE` | Engine Derived | $\log1p(\text{country\_population})$ | Log Persons | `PRE_EVENT` | All Hazards |
| `hazard_intensity_index` | `DERIVED_HAZARD` | Engine Derived | Mag or Wind-normalized intensity | Index | `AT_EVENT` | All Hazards |
| `hazard_x_exposure_interaction` | `DERIVED_CONTEXT` | Engine Derived | $\text{intensity} \times \log1p(\text{density})$ | Interaction Index | `AT_EVENT` | All Hazards |
