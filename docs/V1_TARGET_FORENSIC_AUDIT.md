# Phase 2C.1 — V1 Target Forensic Audit & Mathematical Specification
**Project**: Ignite (PS20)  
**Document**: `docs/V1_TARGET_FORENSIC_AUDIT.md`  
**Phase**: Phase 2C.1 Audit  
**Date**: 2026-09-16  

---

## 1. Mathematical Target Formulation

Continuous Impact Score $Y_{impact}$ is derived directly from real observed EM-DAT outcomes:
$$Y_{impact} = \log1p(Y_{deaths}) + 0.5 \cdot \log1p(Y_{injured}) + 0.1 \cdot \log1p(Y_{affected}) + 0.2 \cdot \log1p(Y_{damage\_usd\_thousands})$$

Ordinal severity classes are defined by static log-impact boundaries:
- **Class 0 (Low)**: $Y_{impact} < 3.0$
- **Class 1 (Moderate)**: $3.0 \le Y_{impact} < 7.0$
- **Class 2 (High)**: $7.0 \le Y_{impact} < 11.0$
- **Class 3 (Critical)**: $Y_{impact} \ge 11.0$

---

## 2. Target Class Imbalance Analysis

| Class Index | Severity Label | Row Count | Percentage (%) | Baseline Role |
|---|---|---|---|---|
| **0** | **Low** | 100 | 29.76% | Minority Class 2 |
| **1** | **Moderate** | **131** | **38.99%** | **Majority Class (Baseline Target)** |
| **2** | **High** | 69 | 20.54% | Minority Class 3 |
| **3** | **Critical** | 36 | 10.71% | Minority Class 4 (Extreme Impact) |

### **Key Audit Finding on Baseline Performance**:
- **Majority-Class Dummy Baseline Accuracy**: **`38.99%`** (Always predicting Moderate).
- **Current Model Accuracy**: **`38.39%`**.
- **Conclusion**: The model's 38.39% accuracy is **essentially identical to a trivial majority-class dummy predictor**.
