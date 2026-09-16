# Feature Engineering Specification (Severity Engine V1)
**Project Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System**  
**Document**: `docs/FEATURE_ENGINEERING_SPEC.md`  
**Phase**: Phase 2C  
**Status**: APPROVED & FROZEN  
**Date**: 2026-09-16  

---

## 1. Feature Engineering Principles & Leakage Rules

1. **Strict Temporal Boundary**: All predictor features $X$ must derive from physical telemetry observed before or at event initiation timestamp $T_0$.
2. **Zero Outcome Contamination**: No outcome variable ($Y_{deaths}, Y_{injured}, Y_{affected}, Y_{damage}$) or post-event assessment variable is permitted in feature engineering.
3. **No Placeholders**: Missing values in hazard features remain strictly missing (`np.nan`). No hard-coded scalar constants or global defaults are inserted.

---

## 2. Engineered Predictor Features

| Feature Name | Source Features | Formula / Transformation | Availability Time ($T_0$) | Leakage Status | Purpose |
|---|---|---|---|---|---|
| `seismic_magnitude` | USGS `mag` | Direct sensor observation | $T_0$ | `PRE_EVENT` / `AT_EVENT` | Seismic energy intensity |
| `seismic_depth_km` | USGS `depth_km` | Direct depth in km | $T_0$ | `PRE_EVENT` / `AT_EVENT` | Focal depth (shallower = higher surface damage) |
| `cyclone_max_wind_knots` | NOAA IBTrACS `max_wind_speed_knots` | Direct wind speed in knots | $T_0$ | `PRE_EVENT` / `AT_EVENT` | Storm kinetic intensity |
| `cyclone_min_pressure_mb` | NOAA IBTrACS `min_pressure_mb` | Direct central pressure in mb | $T_0$ | `PRE_EVENT` / `AT_EVENT` | Storm pressure deficit |
| `hazard_intensity_index` | `seismic_magnitude`, `cyclone_max_wind_knots` | Hazard-normalized intensity index | $T_0$ | `PRE_EVENT` / `AT_EVENT` | Cross-hazard intensity representation |

---

## 3. Target Formulation ($\text{Impact Index } Y_{impact}$)

$$\text{Impact Index } Y_{impact} = \log1p(Y_{deaths}) + 0.5 \cdot \log1p(Y_{injured}) + 0.1 \cdot \log1p(Y_{affected}) + 0.2 \cdot \log1p(Y_{damage\_usd\_thousands})$$

### Ordinal Severity Class Thresholds:
- **Low (0)**: $Y_{impact} < 3.0$
- **Moderate (1)**: $3.0 \le Y_{impact} < 7.0$
- **High (2)**: $7.0 \le Y_{impact} < 11.0$
- **Critical (3)**: $Y_{impact} \ge 11.0$
