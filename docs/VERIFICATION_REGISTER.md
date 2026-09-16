# Ignite Verification Register & Claim Audit

**Project**: Ignite (PS20)  
**Document**: `docs/VERIFICATION_REGISTER.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Last Updated**: 2026-09-16  

---

## 1. Governance Overview
Every technical claim in Project Ignite documentation must undergo explicit audit. Claims are tagged according to strict evidence standards:

- `[VERIFIED]`: Genuine empirical measurement within local workspace or confirmed official protocol.
- `[DERIVED FROM DATA]`: Mathematical or structural property extracted from data schemas.
- `[OFFICIAL DOCUMENTATION]`: Verified via official public API documentation / open standard specs.
- `[INFERENCE]`: Deductive reasoning based on domain principles.
- `[ASSUMED]`: Working operational assumption without direct empirical proof.
- `[UNVERIFIED]`: Claim lacking local empirical validation or live access confirmation.

---

## 2. Comprehensive Claim Audit Table

| Claim ID | Original Claim Text | Previous Tag | Supporting Evidence | Evidence Type | Corrected Status | Required Correction / Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CLM-001** | Project Ignite workspace contains 0 MB raw data files | `[VERIFIED]` | Local filesystem audit of `Ignite/` root directory | EMPIRICAL | `[VERIFIED]` | Validated directly via workspace filesystem search. |
| **CLM-002** | ACLED API endpoint is `https://api.acleddata.com/acled/read` | `[VERIFIED]` | Official ACLED API User Guide documentation | OFFICIAL DOCUMENTATION | `[VERIFIED]` | Supported by official published API documentation. |
| **CLM-003** | ACLED Point-in-Polygon spatial join yields 96.4% match rate | `[VERIFIED]` | None (Estimated estimate from prior literature) | INFERENCE | `[UNVERIFIED]` | Downgraded to `[UNVERIFIED]` until empirical spatial join execution on raw boundary datasets. |
| **CLM-004** | ACLED to INFORM ISO3 join yields 99.1% match rate | `[VERIFIED]` | Standard ISO 3166-1 alpha-3 code specs | DERIVED FROM DATA | `[INFERRED]` | Reclassified as `[INFERRED]`; match rate depends on specific country availability. |
| **CLM-005** | Over 70% of ADM2 units globally record 0 violent events monthly | `[VERIFIED]` | Published domain studies on ACLED global distribution | OFFICIAL DOCUMENTATION | `[INFERRED]` | Reclassified as `[INFERRED]`; pending local empirical calculation on ingested dataset. |
| **CLM-006** | IPC to HDX P-code direct string match yields 82.5% match rate | `[VERIFIED]` | None (Literature estimate) | INFERENCE | `[UNVERIFIED]` | Downgraded to `[UNVERIFIED]` until crosswalk table is executed. |
| **CLM-007** | Sphere WASH standard requires 15 Liters / person / day | `[VERIFIED]` | Sphere Humanitarian Charter Handbook (2018 Edition) | OFFICIAL DOCUMENTATION | `[VERIFIED]` | Verified against official published Sphere Standards. |
| **CLM-008** | Sphere Food standard requires 2,100 kcal / person / day | `[VERIFIED]` | Sphere Humanitarian Charter Handbook / UN WFP Guidelines | OFFICIAL DOCUMENTATION | `[VERIFIED]` | Verified against official humanitarian food security guidelines. |
| **CLM-009** | ACLED experiences a 7 to 14-day publication lag | `[VERIFIED]` | ACLED Data Methodology and Release Schedule Docs | OFFICIAL DOCUMENTATION | `[VERIFIED]` | Confirmed by official ACLED weekly release schedule documentation. |
| **CLM-010** | Empirical historical aid demand logs are unavailable in public datasets | `[VERIFIED]` | Search of UN OCHA HDX and public data portals | EMPIRICAL | `[VERIFIED]` | Confirmed search yields no standardized district-level public delivery datasets. |
| **CLM-011** | District string name matching produces 27.4% failure rate | `[VERIFIED]` | Literature benchmarks on subnational fuzzy matching | INFERENCE | `[UNVERIFIED]` | Downgraded to `[UNVERIFIED]` until empirical string match experiment is run on raw datasets. |
| **CLM-012** | Severity target formula \(\alpha \log(1+D) + \beta E + \gamma IPC\) is ground truth | `[VERIFIED]` | Synthetic composite index proposal | ASSUMPTION | `[ASSUMED]` | Downgraded to `[ASSUMED]`; derived composite target cannot be called ground truth without expert panel calibration. |
