# Comprehensive Target Strategy & Outcome Review

**Project**: Ignite (PS20)  
**Document**: `docs/TARGET_STRATEGY_REVIEW.md`  
**Phase**: Phase 2B Dataset Construction  
**Status**: APPROVED & FROZEN  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Paradigm Shift

### Shift to Direct Observed Historical Outcomes `[VERIFIED]`
Phase 2B officially transitions Project Ignite from synthetic composite target scoring to **Direct Observed Historical Impact Outcomes** ($Y$) sourced from official disaster-loss repositories (EM-DAT and DesInventar).

> [!IMPORTANT]
> **Legacy Target Designation**: The `Derived_Impact_Severity_Index` (`DISI`) formula is reclassified as an **EXPERIMENTAL / LEGACY TARGET**. Models in Phase 2C will train on real observed impact targets (fatalities, displaced persons, damaged structures) or ordinal severity derived directly from observed impact metrics.

---

## 2. Evaluation Matrix of Target Options

`[EMPIRICAL]` Target options evaluated against 9 core technical criteria:

| Target Option | Observability | Reproducibility | Leakage Control | Interpretability | Cross-Hazard Comparability | Coverage | Temporal Validity | Usefulness to Responders | Evaluation Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Option A: Direct Observed Impact Targets** | High | High | High | High | Medium | Medium | High | High | **RECOMMENDED (Primary Multi-Output Target)** |
| **Option B: Ordinal Severity derived from Observed Impact** | High | High | High | High | High | Medium | High | High | **RECOMMENDED (Classification Target)** |
| **Option C: Experimental Composite DISI Score** | Medium | Medium | Medium | Medium | High | High | Medium | Medium | **RETAINED AS LEGACY BASELINE** |
| **Option D: Raw Single Variable (Fatalities Only)** | High | High | High | High | Low | High | High | Low | **REJECTED (Fails for Floods/Droughts)** |
| **Option E: Economic Loss USD Target** | Low | Low | Low | Medium | Low | Low | Low | Low | **REJECTED (Severe Reporting Delays)** |

---

## 3. Approved Outcome Target Vector Specifications `[VERIFIED]`

For every canonical incident $i$, the target outcome vector $\mathbf{y}_i = [y_{i,1}, y_{i,2}, y_{i,3}, y_{i,4}]$ represents future observed impact occurring post-prediction timestamp $T_0$:

1. **Observed Mortality Target ($y_{\text{deaths}}$)**: Total verified direct deaths count.
2. **Observed Displacement Target ($y_{\text{displaced}}$)**: Total displaced individuals count.
3. **Observed Affected Population Target ($y_{\text{affected}}$)**: Total population directly affected.
4. **Observed Structural Damage Target ($y_{\text{damage}}$)**: Destroyed/damaged housing units count.
