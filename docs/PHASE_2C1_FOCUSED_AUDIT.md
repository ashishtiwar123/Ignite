# Phase 2C.1 — Focused Forensic Audit Report (Severity Engine V1)
**Project**: Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System  
**Document**: `docs/PHASE_2C1_FOCUSED_AUDIT.md`  
**Phase**: Phase 2C.1 Forensic Audit  
**Status**: AUDITED & ROOT CAUSES IDENTIFIED  
**Date**: 2026-09-16  

---

## 1. Executive Summary & Diagnostic Findings

Phase 2C.1 performed a comprehensive forensic audit of **Severity Intelligence Engine V1** (`severity_v1`).

The reported Macro F1 of **0.2497** and accuracy of **38.39%** were empirically audited.

### **KEY FORENSIC FINDING**:
- The model's 38.39% accuracy is **no better than a trivial majority-class dummy predictor** (which achieves 38.99% by predicting Class 1 Moderate for all events).
- The primary cause is **MISSING EXPOSURE & VULNERABILITY FEATURES** combined with **HAZARD HETEROGENEITY**.

---

## 2. Quantitative Summary Metrics

- **Dataset**: `ml/data/processed/v4/event_level_training.parquet`
- **Total Training Rows**: 336
- **Earthquake Rows**: 66 (USGS matched)
- **Cyclone Rows**: 270 (IBTrACS matched)
- **Target**: Ordinal Severity Class (0: Low, 1: Moderate, 2: High, 3: Critical)
- **Classes**: 0 (100, 29.8%), 1 (131, 39.0%), 2 (69, 20.5%), 3 (36, 10.7%)
- **Model Selected**: `HistGradientBoosting_Classifier`
- **Validation**: Stratified 5-Fold Cross-Validation
- **Macro F1**: `0.2497`
- **Weighted F1**: `0.3045`
- **Accuracy**: `38.39%`
- **Majority-Class Baseline**: `38.99%`

---

## 3. Root Cause Classification (Ranked by Empirical Evidence)

1. **PRIMARY BOTTLENECK: MISSING EXPOSURE DATA (A & C)**  
   The model relies solely on physical hazard intensity ($X = [\text{mag}, \text{depth}, \text{wind}, \text{pressure}]$). Physical intensity alone without population exposure or vulnerability cannot predict human loss ($Y$).
2. **SECONDARY BOTTLENECK: HAZARD HETEROGENEITY (F)**  
   Earthquake ($n=66$) and Cyclone ($n=270$) operate on non-overlapping feature spaces. Combining them in a 336-row global tree model dilutes signal.
3. **TERTIARY BOTTLENECK: LIMITED SAMPLE SIZE (A)**  
   336 rows are insufficient to learn complex multi-hazard non-linear loss functions across 65 countries.

---

## 4. Real Predictive Signal Assessment

**REAL PREDICTIVE SIGNAL**: `WEAK`

Current empirical evidence proves that physical hazard intensity alone has weak predictive power ($r = -0.198$ for cyclone wind, $r = +0.076$ for earthquake mag) when predicting total EM-DAT human loss without population exposure metrics.

---

## 5. Recommended Next Technical Action

### **RECOMMENDED NEXT ACTION**: `OPTION G: COMBINATION (Acquire Exposure Data + Hazard-Specific Models)`

1. **Acquire Legitimate Population Exposure Data**: Integrate WorldPop or UN WPP country/subnational population density at event locations.
2. **Separate into Hazard-Specific Models**: Architect distinct `EarthquakeSeverityEngine` and `CycloneSeverityEngine` models once sample size permits.
3. **Maintain Strict Placeholder Ban**: Do not reintroduce synthetic defaults.
