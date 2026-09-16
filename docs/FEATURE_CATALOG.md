# Ignite Candidate Feature Catalog

**Project**: Ignite (PS20)  
**Document**: `docs/FEATURE_CATALOG.md`  
**Phase**: Phase 2A Data Foundation  
**Status**: APPROVED & FROZEN FEATURE CATALOG  
**Last Updated**: 2026-09-16  

---

## 1. Overview
This catalog details all 25 candidate features evaluated during Phase 2A, categorized by feature type, latency, unit, spatial level, and Phase 2B model approval status.

---

## 2. Feature Classification Table

| Feature Name | Description | Source | Unit | Spatial Level | Availability Latency | Leakage Risk | Approval Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `seismic_magnitude_max_30d` | Max earthquake magnitude in 30d | USGS API | Moment Mag (Mw) | ADM2 / Point | Tier 0 (< 1 Hour) | None | `TRAINING-CANDIDATE` |
| `seismic_depth_min_km` | Shallowest earthquake depth in 30d | USGS API | Kilometers | ADM2 / Point | Tier 0 (< 1 Hour) | None | `TRAINING-CANDIDATE` |
| `seismic_pga_max_g` | Peak ground acceleration | USGS API | Gravity (g) | Grid / Point | Tier 0 (< 1 Hour) | None | `TRAINING-CANDIDATE` |
| `precip_accum_7d_mm` | 7-day accumulated rainfall | GDACS / Copernicus | mm | ADM2 / Point | Tier 1 (< 24 Hours) | None | `TRAINING-CANDIDATE` |
| `inundated_area_km2` | Satellite flood inundation area | GDACS / Copernicus | sq km | ADM2 / Polygon | Tier 1 (< 24 Hours) | Low | `TRAINING-CANDIDATE` |
| `wildfire_thermal_anomalies_count`| Active thermal hot-spot count | GDACS / FIRMS | Count | ADM2 / Grid | Tier 1 (< 12 Hours) | None | `TRAINING-CANDIDATE` |
| `cyclone_max_wind_speed_knots` | Max tropical cyclone wind speed | GDACS / NOAA | Knots | ADM2 / Polygon | Tier 1 (< 6 Hours) | None | `TRAINING-CANDIDATE` |
| `conflict_events_count_1m` | Conflict event count in 1m | ACLED API | Count | ADM2 | Tier 2 (14-Day Lag) | Medium | `TRAINING-CANDIDATE` |
| `conflict_fatalities_sum_3m` | Rolling 3m conflict fatalities | ACLED API | Count | ADM2 | Tier 2 (14-Day Lag) | Medium | `TRAINING-CANDIDATE` |
| `ipc_phase_baseline` | Baseline food security phase | IPC / FEWS NET | Phase (1-5) | ADM1 / ADM2 | Tier 3 (30-90 Days) | High | `CONTEXT-ONLY` |
| `inform_country_risk_score` | Country composite risk score | INFORM Index | Score (0-10) | ADM0 (Country) | Tier 4 (Annual) | None | `CONTEXT-ONLY` |
| `population_density_sqkm` | Subnational population density | WorldPop / GPWv4 | People / sq km | ADM2 | Static Annual | None | `CONTEXT-ONLY` |
| `post_hoc_damage_usd` | Post-disaster structural damage | Post-Event Surveys | USD | ADM2 | Post-Event | **CRITICAL** | `REJECTED` |
| `post_hoc_total_mortality` | Total disaster death count | Emergency Response | Count | ADM2 | Post-Event | **CRITICAL** | `REJECTED` |
