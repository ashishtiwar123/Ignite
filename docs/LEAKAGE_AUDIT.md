# Phase 2A Feature-Target Leakage Audit Report

**Project**: Ignite (PS20)  
**Document**: `docs/LEAKAGE_AUDIT.md`  
**Phase**: Phase 2A Data Foundation  
**Status**: COMPLETE  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Leakage Principles

This document audits candidate features against target components to guarantee zero data leakage during model training and offline backtesting.

---

## 2. Feature-Target Boundary Audit Matrix

| Target Component | Candidate Feature | Availability at $T_{\text{pred}}$ | Candidate Feature Overlap | Leakage Risk Level | Decision / Isolation Guardrail |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `target_mortality` | `historical_fatalities_sum_3m` | Historical ($T \le T_{\text{pred}} - 14\text{d}$) | Partial | Low | **APPROVED**: Historical mortality baseline prior to forecast snapshot is legitimate predictor signal. |
| `target_mortality` | `event_mortality_current_month` | Future ($T > T_{\text{pred}}$) | Direct | **CRITICAL** | **REJECTED**: Post-hoc mortality assessment from target period is strictly prohibited from feature matrix. |
| `target_displacement` | `historical_idp_baseline` | Historical ($T \le T_{\text{pred}} - 30\text{d}$) | Partial | Low | **APPROVED**: Pre-disaster displaced baseline is legitimate context. |
| `target_damage` | `satellite_post_disaster_damage_usd`| Future ($T > T_{\text{pred}}$) | Direct | **CRITICAL** | **REJECTED**: Damage assessments published after event conclusion are target components, not predictor features. |
| `target_disi_score` | `seismic_magnitude_mw` | Real-time ($T_{\text{occur}} \le T_{\text{pred}} - 1\text{h}$) | Independent | None | **APPROVED**: Physical hazard input (PGA/Magnitude) is independent physical signal. |
