# Ignite Architectural & Technical Decision Log

**Project**: Ignite (PS20)  
**Document**: `docs/DECISION_LOG.md`  
**Phase**: Phase 2B Dataset Construction  
**Status**: APPROVED & FROZEN  
**Last Updated**: 2026-09-16  

---

## 1. Governance Overview
Every technical decision in Project Ignite is recorded using the mandatory 6-part framework (*Decision, Evidence, Reason, Alternatives Considered, Consequences, Limitations*). Architectural history is strictly preserved; superseded decisions are retained and explicitly marked as `SUPERSEDED`.

---

## 2. Decision Records

### DEC-001: P-Code Based Spatial Harmonization Standard `[VERIFIED]`
- **Status**: ACTIVE & APPROVED
- **Decision**: Standardize all subnational joins strictly on UN OCHA COD-AB `ADM2_PCODE` keys rather than district string names.
- **Evidence**: String matching district names across multi-provider datasets produces high failure rates due to spelling variants.
- **Reason**: Guarantees deterministic spatial joins across crisis datasets without data corruption or orphan records.
- **Alternatives Considered**: Fuzzy string matching (Levenshtein/Jaro-Winkler). Rejected due to runtime latency and false-positive spatial assignments.
- **Consequences**: Data sources lacking P-codes must undergo spatial point-in-polygon lookup against OCHA shapefiles.
- **Limitations**: Historical boundary changes require maintaining canonical P-code version crosswalk tables.

---

### DEC-002: Pure Monthly Spatio-Temporal Feature Windowing `[VERIFIED]`
- **Status**: SUPERSEDED by DEC-005

---

### DEC-003: Deterministic Sphere Humanitarian Demand Translation `[VERIFIED]`
- **Status**: ACTIVE & APPROVED
- **Decision**: Derive humanitarian supply demands (WASH water, food rations, shelter) deterministically from predicted affected populations using Sphere Standards.
- **Evidence**: Empirical historical supply dispatch logs are unstandardized and unavailable in public repositories (`[UNVERIFIED]`).
- **Reason**: Guarantees 100% adherence to recognized international standards (Sphere / IASC) while providing transparent, reproducible outputs.

---

### DEC-004: Mandatory Universal 14-Day Reporting Lag `[VERIFIED]`
- **Status**: SUPERSEDED by DEC-006

---

### DEC-005: Multi-Resolution Spatial & Temporal Architecture `[VERIFIED]`
- **Status**: ACTIVE & APPROVED (Supersedes DEC-002)

---

### DEC-006: Source-Specific Data Availability & Latency Policy `[VERIFIED]`
- **Status**: ACTIVE & APPROVED (Supersedes DEC-004)

---

### DEC-007: Multi-Hazard Derived Impact Severity Target `[VERIFIED]`
- **Status**: SUPERSEDED BY DEC-011 FOR MODEL TRAINING
- **Decision**: Reclassified as EXPERIMENTAL / LEGACY target for baseline comparisons. Ground-truth ML training targets will use real observed impact metrics ($Y$).

---

### DEC-008: Strict Segregation of ML, Rules, and Optimization Layers `[VERIFIED]`
- **Status**: ACTIVE & APPROVED

---

### DEC-011: Direct Observed Outcome Target Architecture `[VERIFIED]`
- **Status**: ACTIVE & APPROVED (Supersedes DEC-007 for model training)
- **Decision**: Train ML models directly on real historical observed impact outcomes ($Y$: direct deaths, injured, displaced, total affected, damaged structures) sourced from EM-DAT and DesInventar.
- **Evidence**: Grounding targets in real observed losses provides scientifically defensible, verifiable outcome labels that avoid synthetic target artifacts.
- **Reason**: Guarantees model predictions map directly to real-world humanitarian impact variables.
- **Alternatives Considered**: Training on synthetic composite score (DISI). Reclassified as legacy baseline.
- **Consequences**: Observed outcomes preserve `null` vs `0` distinction to avoid false zero imputation.
- **Limitations**: Target availability is bounded by official disaster reporting timelines.
