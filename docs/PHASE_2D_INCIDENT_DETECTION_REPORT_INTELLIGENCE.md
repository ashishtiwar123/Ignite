# Phase 2D: Incident Detection & Report Intelligence

**Objective:**
Build an operational intelligence layer that turns raw disaster reports and alerts into normalized, deduplicated, and traceable incident candidates, without claiming immediate verified ground truth. 

**Scope & Non-Goals:**
This phase covers the pipeline from Report ingestion to Incident clustering. It explicitly excludes:
- Live API usage for testing (offline tests only)
- Real-time agent orchestration (LangGraph)
- Resource Allocation or Needs Assessment (OR-Tools)
- Any modification to existing Severity ML Models (V1/V2/V5)

## Architecture

1. **Report Definition:**
   A standard observation from a single source (`Report`). Retains raw JSON provenance, location bounds, timestamps, and extracted attributes. Missing fields are explicitly `null` rather than `0`.

2. **IncidentCandidate Definition:**
   A synthesized event representation grouping one or more `Report` objects. Captures matched reasons, overall confidence, and conflict occurrences explicitly.

3. **Source Adapters (`ml/src/ingestion/adapters.py`):**
   Parses structure from sources (USGS, GDACS). Does not ping live APIs, allowing static fixture injection. 

4. **Extraction (`ml/src/incident/extraction.py`):**
   Stub interface (`LLMExtractor`) returning structured metadata and confidence from raw text.

5. **Normalization (`ml/src/incident/normalization.py`):**
   Maps local aliases ("Hurricane") to canonical definitions ("Cyclone"). Standardizes datetimes to UTC.

6. **Validation (`ml/src/incident/validation.py`):**
   Deterministically validates numeric bounds like Lat/Lon degrees and magnitude plausibility. Records errors securely.

7. **Deduplication (`ml/src/incident/deduplication.py`):**
   Matches `source` and `source_record_id` to strictly prune duplicate transmission errors.

8. **Matching & Clustering (`ml/src/incident/matching.py` & `clustering.py`):**
   Uses `haversine_distance` for great-circle kilometer spatial boundaries and strict timestamp deltas to score alignment. Produces `MATCH`, `POSSIBLE_MATCH`, or `NO_MATCH` with recorded rationale.
   
9. **Confidence, Provenance, and Conflict Handling:**
   Sources disagreeing on magnitude or location create explicit conflict arrays rather than being silenced. The entire pipeline retains original `raw_payload_reference`.

## Fixture Strategy & Testing
Deterministic payloads (`reports.json`) inject exact scenarios representing:
- Duplicate occurrences
- Missing data checks (like population/latitude)
- Spatial overlap bounds (100km EQ rules vs. 500km broader hazards)
- Timed decay (2 hours vs. 48 hours bounds)

Tests operate 100% offline via pytest. 

## Limitations
- **Not Connected to Severity ML:** Candidates currently stop at the Intelligence boundary and are not yet feeding predictions.
- **Stubbed Extraction:** True LLM information parsing is mock-implemented.
- **Limited Adapters:** FIRMS and NOAA live adapter stubs are planned but not strictly functional with live parsing logic yet.

## Phase 2E Handoff
The output is an array of `IncidentCandidate` objects marked as `CANDIDATE` or `NEEDS_VERIFICATION`. Phase 2E will build the `Incident Verification` ruleset to advance these candidates into the `VERIFIED` state ready for ML Assessment.
