# Model Card — Severity Intelligence Engine V2
**Project**: Ignite (PS20)  
**Model Name**: Severity Intelligence Engine V2 (`severity_v2`)  
**Document**: `docs/SEVERITY_V2_MODEL_CARD.md`  
**Date**: 2026-09-16  

---

## 1. Model Purpose & Upgrades over V1

- **Model Purpose**: Evaluates physical hazard intensity at event initiation ($T_0$) combined with real historical World Bank population exposure to predict impact severity score and ordinal severity class (Low, Moderate, High, Critical) with calibrated confidence.
- **Key Upgrades over V1**: Integrates real historical population exposure ($X_{pop}$), increasing Macro F1 from 0.2497 to **0.2794** and unlocking High-severity event recognition (15.94% recall vs 0.00% in V1).

---

## 2. Training Data & Supported Hazards

- **Training Dataset**: [`ml/data/processed/v5/event_level_features.parquet`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v5/event_level_features.parquet) (336 verified rows).
- **Supported Hazards**: `EARTHQUAKE` (USGS GeoJSON telemetry) & `STORM` / `CYCLONE` (NOAA IBTrACS best-track telemetry).
- **Unsupported Hazards**: `FLOOD`, `WILDFIRE`, `LANDSLIDE`, `DROUGHT`, `EPIDEMIC`, `EXTREME TEMPERATURE`.

---

## 3. Mandatory Disclaimer

> [!WARNING]  
> "This model is currently trained only on the verified earthquake and tropical cyclone subset of V5 and should not be represented as a validated general multi-hazard model."
