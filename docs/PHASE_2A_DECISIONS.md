# Phase 2A Decision Log & Architectural Updates

**Project**: Ignite (PS20)  
**Document**: `docs/PHASE_2A_DECISIONS.md`  
**Phase**: Phase 2A Data Foundation  
**Status**: APPROVED  
**Last Updated**: 2026-09-16  

---

## 1. Governance Overview
Every decision in Phase 2A adheres to the 6-part framework (*Decision, Evidence, Reason, Alternatives, Consequences, Limitations*).

---

## 2. Phase 2A Decision Records

### DEC-009: Empirical Validation of USGS & GDACS Open APIs `[EMPIRICAL]`
- **Decision**: Authorize USGS Seismic API and GDACS Alert API as primary Tier 0 and Tier 1 live physical hazard telemetry sources.
- **Evidence**: Ingestion execution fetched 500 seismic events and 246 multi-hazard alerts with 0.0% missing coordinates/magnitudes.
- **Reason**: Guarantees real-time physical hazard signal access without API credential barriers.
- **Alternatives Considered**: Commercial satellite APIs. Rejected due to cost and access limitations.
- **Consequences**: Ingestion scripts (`ml/src/ingestion/`) must poll USGS and GDACS endpoints daily.
- **Limitations**: GDACS country assignment requires 0.81% null imputation.

### DEC-010: Prohibition of Direct ML Demand Regression `[EMPIRICAL]`
- **Decision**: Enforce deterministic Sphere Standards calculation for humanitarian demand outputs; prohibit direct ML regression on non-existent empirical demand targets.
- **Evidence**: Search across UN OCHA HDX, WFP DataVAM, and UNHCR microdata confirmed no standardized global subnational demand delivery targets exist (`docs/DEMAND_DATA_RESEARCH.md`).
- **Reason**: Prevents training ML models on fabricated or non-existent ground truth targets.
- **Alternatives Considered**: Training ML model on synthetic demand data. Rejected as scientifically invalid.
- **Consequences**: Phase 2B ML modeling is strictly confined to predicting affected population counts, Derived Impact Severity (`DISI`), and Risk Trajectory.
- **Limitations**: Needs calculation relies directly on affected population model accuracy.
