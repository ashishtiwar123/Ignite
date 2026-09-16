# Phase 2E: Incident Verification

**Objective:**
Take `IncidentCandidate` records output from Phase 2D and rigorously evaluate them against independent structured evidence to determine if they meet the criteria to be considered `VERIFIED`.

**Scope & Non-Goals:**
This phase implements the deterministic Verification Engine. It explicitly excludes:
- Any modification to existing Phase 2C Severity ML models (V1, V2, V5).
- LLMs deciding whether an incident is true or false.
- Live API integration for testing (runs purely on offline deterministic fixtures).

## Architecture

1. **Evidence Model (`VerificationEvidence`)**:
   A structured representation of a `Report` mapped to a specific candidate, extracting only the fields necessary for verification (source, coordinates, timestamp, hazard, attributes).
   
2. **Assessment Model (`VerificationAssessment`)**:
   The final output summarizing the candidate's status (`VERIFIED`, `NEEDS_VERIFICATION`, `REJECTED`, or `CANDIDATE`). It explicitly contains sub-scores, contradiction maps, and explainable text strings detailing the operational policy application.

3. **Verification Policy (`verification_policy.py`)**:
   A purely operational, deterministic policy defining:
   - *Source Reliability Weights*: E.g., USGS (1.0), GDACS (1.0), NEWS (0.5).
   - *Spatial/Temporal Thresholds*: Hazard-aware maximum bounds (e.g., Earthquakes must be within 100km and 2 hours; Cyclones within 500km and 48 hours).
   
4. **Verification Engine (`verification.py`)**:
   Scores candidates on independent source corroboration, spatial/temporal/hazard consistency, and applies conflict penalties.

## Scoring Methodology

The score is composed of:
1. **Source Reliability**: Sum of reliability weights of supporting evidence.
2. **Independent Corroboration**: Logarithmic/linear bonus based on `independent_source_count`. Duplicate sources (e.g., two USGS records) are deduplicated.
3. **Consistency Scores (Spatial, Temporal, Hazard, Attribute)**: If evidence falls within defined operational thresholds, a positive baseline is awarded. Any deviations result in negative penalties explicitly tracked as `conflicts`.

> [!CAUTION]
> **Not Empirically Validated**
> The `verification_score` is an Operational Verification Policy metric. It does NOT represent a scientifically calibrated probability that an incident occurred. It simply represents the degree of structured agreement across multiple independent sources.

## Verification Thresholds and Status Decision

A status of `VERIFIED` requires:
- `verification_score` >= `VERIFIED_MIN_SCORE` (Configured to 4.5).
- `independent_source_count` >= `VERIFIED_MIN_INDEPENDENT_SOURCES` (Configured to 2).
- **NO CRITICAL PENALTIES**: Any spatial, temporal, hazard, or attribute penalty immediately caps the status at `NEEDS_VERIFICATION`.
- **NO MISSING DATA**: Missing spatial or temporal data on the candidate explicitly caps the status at `NEEDS_VERIFICATION`. We do not fabricate missing data.

## Conflict Handling and Explainability

Conflicts (e.g., magnitude 6.2 vs 8.5) are never averaged away. They are tracked as an array of structured conflicts. 
Every Assessment generates a human-readable `explanation` list detailing exactly why the status was assigned (e.g., "Spatial conflicts detected (0.5 penalty)", "Status set to NEEDS_VERIFICATION. Score is insufficient.").

## Provenance
No evidence is discarded. The Assessment retains arrays of `supporting_evidence_ids`, ensuring full traceback to the original `Report` objects and their underlying JSON schemas.

## Test Coverage
The suite (`test_verification_pipeline.py`) uses 10 offline JSON fixtures testing:
- Strongly corroborated setups
- Single-source insufficiency
- Geographic/temporal mismatches
- Duplicate inflation prevention
- Explicit conflict propagation

## Known Limitations
- The source reliability weights are operational heuristics, not based on backtested precision/recall of the sources.
- The spatial/temporal bounds (e.g., 100km for EQ) are operational approximations.
- `NEEDS_VERIFICATION` statuses currently require manual/human intervention or advanced rules engines in later phases to resolve.

## Handoff to Phase 2F
The system successfully graduates candidates to `VERIFIED` status without corrupting the original data, paving the way for Phase 2F (Risk / Trajectory Intelligence) to utilize these verified incidents.
