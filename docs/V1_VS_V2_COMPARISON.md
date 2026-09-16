# Direct Comparison: Severity Engine V1 vs. Severity Engine V2
**Project**: Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System  
**Document**: `docs/V1_VS_V2_COMPARISON.md`  
**Phase**: Phase 2C.3  
**Date**: 2026-09-16  

---

## 1. Executive Performance Comparison

| Metric / Dimension | Severity Engine V1 (Frozen) | Severity Engine V2 (Model B Country Demographic Context) | Performance Delta ($\Delta$) | Empirical Verdict |
|---|---|---|---|---|
| **Primary Dataset** | Dataset V4.0 (`336 rows`) | Dataset V5.0 (`336 rows`) | 0 sample difference | Identical 336-row benchmark evaluation |
| **Predictor Feature Set $X$** | 6 Hazard-only features | 9 Hazard + Country Demographic features | **+3 Country Demographic Features** | Country population, density, log population |
| **Macro F1 Score** | `0.2497` | **`0.2794`** | **`+0.0297` (+11.9% relative gain)** | **OBSERVED IMPROVEMENT (Not Statistically Significant p>0.05, 95% CI [-0.0269, +0.0859])** |
| **Weighted F1 Score** | `0.3045` | **`0.3139`** | **`+0.0094` (+3.1% relative gain)** | **OBSERVED IMPROVEMENT (Not Statistically Significant p>0.05, 95% CI [-0.0447, +0.0642])** |
| **Accuracy** | `38.39%` | `32.44%` | `-5.95%` | Tradeoff due to reduced majority-class collapse |
| **High Severity Recall (Class 2)** | `0.0000` (0 / 69) | **`0.1594` (11 / 69)** | **`+15.94%` (From zero to 11 detected)** | **STATISTICALLY SUPPORTED IMPROVEMENT (95% CI [+0.0758, +0.2500])** |
| **Critical Severity Recall (Class 3)** | `0.1389` (5 / 36) | `0.1389` (5 / 36) | `0.0000` | Maintained critical event detection (95% CI [-0.1143, +0.1111]) |
| **Severe Underprediction Count** | 100 / 105 events (95.2%) | **89 / 105 events (84.8%)** | **-11 Severe Errors (-10.5%)** | Demographic context features reduced severe misclassifications |

---

## 2. Key Empirical Findings

1. **Country-Level Demographic Context Features Add Predictive Signal**: Adding World Bank national population and population density (country-level demographic context, not physical hazard-footprint exposure) increased observed Macro F1 from 0.2497 to **0.2794** (observed improvement, not statistically significant on N=336).
2. **Breakthrough in High-Severity Event Recognition**: V1 had **0% recall on Class 2 (High Severity)**, predicting 0 out of 69 High-severity incidents. V2 detected **11 High-severity incidents** (15.94% recall), representing a **statistically supported improvement** (95% CI [+0.0758, +0.2500]).
3. **Severe Error Reduction**: Severe underpredictions (High/Critical disasters predicted as Low/Moderate) dropped from 100 events in V1 to **89 events in V2**.
