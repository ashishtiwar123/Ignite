# Phase 2C.2 — Exposure & Vulnerability Historical Temporal Alignment Specification
**Project**: Ignite (PS20) — Multi-Hazard Disaster & Emergency Response System  
**Document**: `docs/EXPOSURE_TEMPORAL_ALIGNMENT.md`  
**Phase**: Phase 2C.2  
**Status**: APPROVED & FROZEN  
**Date**: 2026-09-16  

---

## 1. Temporal Matching Guardrails

To prevent future temporal leakage:
$$\text{Timestamp}(\text{Feature } X) \le T_0 < \text{Timestamp}(\text{Disaster Outcome } Y)$$

For any historical disaster event occurring in year $Y_{event}$:
- **Exact Historical Match**: Exposure metrics ($X_{pop}, X_{density}, X_{urban}$) are queried for year $Y_{event}$.
- **Backward Temporal Fallback**: If $Y_{event}$ metrics are missing, the closest preceding available year $Y_{pre} \le Y_{event}$ is selected.
- **Strict Leakage Prohibition**: Post-event years ($Y_{post} > Y_{event}$) are strictly forbidden to prevent post-event population/economic shifts from contaminating prediction-time features.

---

## 2. Temporal Metadata Audit Schema

Every V5 record attaches explicit temporal lineage:
- `event_start_year`: Year of disaster initiation ($T_0$).
- `population_source_year`: Exact year of matched World Bank indicator.
- `temporal_alignment_status`: `EXACT_MATCH` (if year equal) or `HISTORICAL_NEAREST_PRECEDING`.
