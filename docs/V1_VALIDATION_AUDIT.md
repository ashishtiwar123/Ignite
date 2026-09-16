# Phase 2C.1 — Validation Methodology & Geographic Concentration Audit
**Project**: Ignite (PS20)  
**Document**: `docs/V1_VALIDATION_AUDIT.md`  
**Phase**: Phase 2C.1 Audit  
**Date**: 2026-09-16  

---

## 1. Geographic Concentration Breakdown

The 336 training-eligible records span 65 countries, but exhibit heavy geographic clustering:

| Country | Record Count | Percentage (%) | Dominant Hazard |
|---|---|---|---|
| **Philippines** | 56 | 16.67% | Tropical Cyclone |
| **China** | 27 | 8.04% | Tropical Cyclone |
| **United States** | 21 | 6.25% | Tropical Cyclone |
| **Vietnam** | 16 | 4.76% | Tropical Cyclone |
| **Japan** | 15 | 4.46% | Cyclone / Earthquake |
| **Mexico** | 14 | 4.17% | Cyclone / Earthquake |
| **Others (59 countries)** | 187 | 55.65% | Multi-Hazard |

---

## 2. Validation Leakage Audit

Stratified 5-Fold Cross-Validation splits rows randomly across folds. Because 16.67% of all records come from the Philippines, **the exact same country appears simultaneously in training and validation folds**.

The model is effectively evaluated on countries it has already seen, masking true out-of-region generalization error.

---

## 3. Recommended Validation Strategy

Future iterations ($V2.0$) must evaluate using **GroupKFold by Country** or **GroupKFold by Physical Region** to measure genuine cross-border generalization capability.
