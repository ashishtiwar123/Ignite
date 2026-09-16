# V5 Dataset Card — Event-Level Feature-Enriched Dataset
**Project**: Ignite (PS20)  
**Dataset Version**: `v5.0-exposure-enriched`  
**Document**: `docs/V5_DATASET_CARD.md`  
**Date**: 2026-09-16  

---

## 1. Overview & Provenance Classification

- **Dataset File**: [`ml/data/processed/v5/event_level_features.parquet`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v5/event_level_features.parquet)
- **Total Records**: **336 verified disaster events** (Earthquake: 66, Storm: 270).
- **Physical Hazard Source**: USGS GeoJSON API (`[VERIFIED API RETRIEVAL]`) & NOAA IBTrACS (`[STATIC DATA]`).
- **Exposure / Context Source**: Official World Bank API Indicators 2000–2025 (`[VERIFIED API RETRIEVAL]`).
- **Target Source**: Official Public EM-DAT Export (`[VERIFIED MANUAL DOWNLOAD]`).

---

## 2. Feature Completeness Metrics

- **Physical Hazard Features**: 100% genuine sensor telemetry for 336 rows.
- **Historical Population (`country_population`)**: **336 rows (100.0% coverage)**
- **Historical Population Density (`population_density_sqkm`)**: **336 rows (100.0% coverage)**
- **Historical Urban Population % (`urban_population_pct`)**: **336 rows (100.0% coverage)**
- **Historical Poverty Headcount % (`poverty_headcount_pct`)**: **195 rows (58.04% coverage)**
- **Synthetic Placeholders / Hard-coded Defaults**: **0% (100% Purged)**

---

## 3. Disclaimers & Intended Usage

This dataset represents a feature-enriched event-level dataset for Severity Engine V2. It is **NOT** a synthetic dataset. Missing poverty values remain strictly missing (`np.nan`).
