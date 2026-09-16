# Training Dataset v2.0 Statistics & Quality Report

**Project**: Ignite (PS20)  
**Document**: `docs/TRAINING_DATASET_V2_REPORT.md`  
**Phase**: Phase 2B.5 Data Expansion  
**Status**: COMPLETE  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Build Metadata

`[EMPIRICAL]` Dataset v2.0 was built and validated under [`ml/data/processed/training_dataset_candidate_v2.json`](file:///c:/Users/Ashish%20Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v2.json).

- **Dataset Version**: `v2.0-historical-expanded`
- **Total Independent Canonical Incidents**: **608**
- **Total Training Rows**: **608**
- **Ground-Truth Outcome Coverage**: **35 records**
- **Predictor Feature Coverage**: **608 records (100%)**

---

## 2. Hazard & Temporal Breakdown

### Hazard Distribution (`[EMPIRICAL]` Metadata):
- **EARTHQUAKE**: 571 incidents (93.9%)
- **CYCLONE**: 16 incidents (2.6%)
- **FLOOD**: 8 incidents (1.3%)
- **LANDSLIDE**: 5 incidents (0.8%)
- **WILDFIRE**: 3 incidents (0.5%)
- **DROUGHT**: 2 incidents (0.3%)
- **FLASH FLOOD / DEBRIS FLOW**: 3 incidents (0.5%)

### Temporal Distribution (2011–2026):
- 2023: 165 incidents | 2025: 145 incidents | 2026: 99 incidents | 2024: 104 incidents | 2022: 80 incidents | 2018-2021: 15 incidents.

---

## 3. Target Missingness & Zero Preservation Table `[EMPIRICAL]`

| Observed Target Variable | Non-Null Count | Observed Zero (`0`) Count | Un-Reported (`null`) Count | Target Coverage % |
| :--- | :---: | :---: | :---: | :---: |
| `deaths` | 35 | 3 | 573 | 100% of Loss Sources |
| `injured` | 32 | 4 | 576 | 91.4% of Loss Sources |
| `displaced` | 28 | 5 | 580 | 80.0% of Loss Sources |
| `total_affected` | 22 | 2 | 586 | 62.8% of Loss Sources |
| `total_damage_usd` | 20 | 1 | 588 | 57.1% of Loss Sources |
