# Derived Impact Severity Target Validation Report

**Project**: Ignite (PS20)  
**Document**: `docs/SEVERITY_TARGET_VALIDATION_REPORT.md`  
**Phase**: Phase 2A Data Foundation  
**Status**: COMPLETE  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Target Validation

The Derived Impact Severity Target (`DISI`) was empirically tested via `ml/src/targets/compute_disi_target.py` across simulated multi-hazard impact scenarios.

---

## 2. Empirical Target Formulation & Benchmark Results

`[EMPIRICAL]` Target construction formula:
$$\text{DISI} = \min \left( 5.0, \; 0.35 \cdot S_{\text{Mortality}} + 0.20 \cdot S_{\text{Morbidity}} + 0.25 \cdot S_{\text{Displacement}} + 0.20 \cdot S_{\text{Damage}} \right)$$

### Benchmark Scenario Test Output (`[EMPIRICAL]` Execution):

| Scenario Description | Deaths | Injured | Displaced | Damaged Buildings | DISI Score | Class | Class Label |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Baseline Normal** | 0 | 0 | 0 | 0 | **0.00** | **0** | Baseline / Normal |
| **Minor Local Incident** | 2 | 5 | 50 | 2 | **0.58** | **1** | Minor / Stressed |
| **Moderate Emergency** | 15 | 50 | 500 | 20 | **1.56** | **2** | Moderate Emergency |
| **Severe Disaster** | 80 | 300 | 5,000 | 150 | **2.74** | **3** | Severe Disaster |
| **Extreme Regional Crisis** | 300 | 1,200 | 25,000 | 500 | **3.56** | **4** | Extreme Crisis |
| **Catastrophic Famine/Quake**| 2,000 | 10,000 | 150,000 | 5,000 | **4.78** | **5** | Catastrophic Emergency |

---

## 3. Alternative Target Formulations Trade-off Matrix

| Target Option | Observability | Temporal Validity | Leakage Control | Multi-Hazard Comparability | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Option A: Continuous 0-5 DISI Score** | High | High | High (Lagged post-hoc components) | High | **RECOMMENDED (Primary Target)** |
| **Option B: Ordinal 0-5 Severity Classes** | High | High | High | High | **RECOMMENDED (Classification Baseline)** |
| **Option C: Pure Fatality Count Regressor** | Medium | Medium | Medium | Low (Fails on floods/droughts) | REJECTED |
| **Option D: Direct Economic Loss USD** | Low | Low (Delayed) | Low | Low | REJECTED |
