# Phase 2C.1 — V1 Error Analysis & Failure Pattern Report
**Project**: Ignite (PS20)  
**Document**: `docs/V1_ERROR_ANALYSIS.md`  
**Phase**: Phase 2C.1 Audit  
**Date**: 2026-09-16  

---

## 1. Error Matrix Summary

Out of 336 test predictions:
- **Correct Predictions**: 129 (38.39% Accuracy)
- **Severe Underpredictions (High/Critical predicted as Low/Moderate)**: **100 events (29.76% of all data)**
- **Severe Overpredictions (Low/Moderate predicted as High/Critical)**: 7 events

---

## 2. Confusion Matrix

```
               Predicted Class
Actual Class   Low (0)  Moderate (1)  High (2)  Critical (3)
Low (0)           21         77           0           2
Moderate (1)      22        103           1           5
High (2)           4         65           0           0
Critical (3)       2         29           0           5
```

---

## 3. Core Failure Mechanism

The model exhibits severe collapse toward **Class 1 (Moderate)**. Out of 105 actual High/Critical incidents (Classes 2 and 3), **94 events (89.5%) were misclassified as Moderate**.

### **Root Cause**:
Because $X$ contains only physical hazard intensity (wind/magnitude) without population exposure, building vulnerability, or regional infrastructure metrics, the model cannot distinguish between a high-magnitude event in an uninhabited area (low impact) and a moderate event in a densely populated region (critical impact).
