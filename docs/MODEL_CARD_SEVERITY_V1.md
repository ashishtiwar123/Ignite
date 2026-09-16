# Model Card — Severity Intelligence Engine V1
**Project**: Ignite (PS20)  
**Model Name**: Severity Intelligence Engine V1 (`severity_v1`)  
**Document**: `docs/MODEL_CARD_SEVERITY_V1.md`  
**Date**: 2026-09-16  

---

## 1. Model Overview & Intended Use

- **Purpose**: Evaluates multi-hazard physical intensity features at event initiation ($T_0$) to predict impact severity score and ordinal severity class (Low, Moderate, High, Critical) with calibrated confidence.
- **Intended Use**: Integration into Situation Intelligence and Assessment Engines for disaster response prioritization.
- **Prohibited Use**: Real-time automated physical logistics dispatch without human review; unsupported hazard predictions (Flood, Wildfire, Landslide, Drought).

---

## 2. Training Data & Hazard Coverage

- **Training Dataset**: [`ml/data/processed/v4/event_level_training.parquet`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet)
- **Sample Size**: 336 verified rows (0 synthetic placeholders).
- **Supported Hazards**: `EARTHQUAKE` (USGS GeoJSON telemetry) and `STORM` / `CYCLONE` (NOAA IBTrACS best-track telemetry).
- **Unsupported Hazards**: `FLOOD`, `WILDFIRE`, `LANDSLIDE`, `DROUGHT`, `EPIDEMIC`, `EXTREME TEMPERATURE`.

---

## 3. Disclaimers & Limitations

> [!WARNING]  
> "This model is currently trained only on the verified earthquake and tropical cyclone subset of V4 and should not be represented as a validated general multi-hazard model."
