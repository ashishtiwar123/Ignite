# Phase 2H: Priority Engine

**Objective:**
Build a deterministic and explainable Priority Engine to identify which verified incidents require greater operational attention.

## 1. Scope & Core Principles
The Priority Engine converts a composite of incident factors into an operational priority score (0-100) and ranking. 

**Priority ≠ Severity.**
- **Severity** asks: "How physically destructive is this incident?"
- **Priority** asks: "How urgently should this incident receive operational attention relative to others in the queue?"

This engine explicitly **DOES NOT**:
- Predict or generate statistical probabilities of risk.
- Choose which warehouses to pull resources from.
- Solve logistics, routing, or allocation constraints (Phase 2I scope).
- Use machine learning models or LLMs to guess priority scores.

## 2. Architecture & Contracts
- **`PriorityEngineInput`**: Synthesizes verified incident status, Phase 2C Severity, Phase 2F Trajectory, and Phase 2G Needs Assessment data.
- **`PriorityAssessment`**: The canonical output returning a normalized `priority_score`, discrete `priority_level`, complete `factor_scores` matrix, list of `missing_factors`, and a human-readable `explanation`.

## 3. The Factor Model (`priority_policy_v1`)
The engine is driven by a purely deterministic, additive policy composed of the following weighted factors:

1. **Severity (Max 40 points)**
   - Derived from Phase 2C `severity_score` (multiplied by 8).
   - An extreme severity (5.0) yields the full 40 points.
2. **Trajectory (Max 20 points)**
   - Derived from Phase 2F momentum.
   - `RAPIDLY_WORSENING` (+20), `WORSENING` (+10), `STABLE` (0), `IMPROVING` (-10).
3. **Population Impact (Max 20 points)**
   - Calculated using a logarithmic band (`log10(population) * 3.2`) capped at 20 points.
   - *Rationale*: A logarithmic scale prevents massive population values from mathematically eclipsing severe physical destruction or urgent rescue needs.
4. **Urgency/Needs (Max 20 points)**
   - Derived from Phase 2G qualitative outputs.
   - `CRITICAL` rescue adds 15 points; `CRITICAL` medical adds 10 points.

### Missing Data & Gating
- **Unverified Incidents**: If an incident is marked `NEEDS_VERIFICATION`, it is explicitly gated and assigned a priority level of `PENDING_VERIFICATION` (Score: 0.0), bypassing the operational queue.
- **Silent Defaults Prohibited**: Missing trajectory is NOT assumed to be STABLE. Missing population is NOT assumed to be zero. Unavailable factors are explicitly marked in `missing_factors` and do not contribute to the score.
- **Unsupported Contexts**: `vulnerability` and `time_sensitivity` are currently unsupported by upstream data feeds and are explicitly tracked as unavailable.

## 4. Multi-Incident Ranking & Tie-Breaking
The engine supports multi-incident batch ranking. In the event of identical priority scores, tie-breaking is strictly deterministic in the following order:
1. `CRITICAL` Rescue Urgency (True > False).
2. `RAPIDLY_WORSENING` Trajectory (True > False).
3. Affected Population Size (Descending).
4. Incident ID (Alphanumeric sort fallback).

## 5. Explainability
Every assessment produces an explicit string tracing exactly how the score was calculated (e.g., "MEDIUM priority (48.2/100) because: severity 3.8 (+30.4 pts), affected population is 10000 (+12.8 pts), urgency (Rescue: MODERATE, Medical: MODERATE) (+5.0 pts)."). 

## 6. Known Limitations
- The logarithmic scaling of population impact may need operational tuning during Phase 3 field exercises to ensure urban disasters are not systematically under/over-represented.
- Priority relies heavily on the availability of accurate rescue/medical qualitative urgency from Phase 2G.

## 7. Handoff
With incidents now verified, severity-scored, and prioritized, the pipeline is ready to hand off to **Phase 2I — Resource Optimization / OR-Tools**.
