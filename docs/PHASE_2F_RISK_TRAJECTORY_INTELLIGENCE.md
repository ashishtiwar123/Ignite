# Phase 2F: Risk / Trajectory Intelligence

**Objective:**
Build the Risk / Trajectory Intelligence layer to answer "How is the incident evolving?" strictly based on structured temporal evidence, assigning it a trajectory of `IMPROVING`, `STABLE`, `WORSENING`, `RAPIDLY_WORSENING`, or `INSUFFICIENT_EVIDENCE`.

## 1. Scientific Data Audit & ML Justification
A thorough audit of the underlying historical training data (EM-DAT, V2 datasets) revealed a critical limitation: the historical datasets contain a single static row per incident reflecting the final total impact (e.g., total deaths, total damages). 
There is **no genuine temporal observation sequence** of the *same* incident mapped to known trajectory outcomes in the available training data.
Attempting to train an ML trajectory model on this data would necessitate fabricating synthetic time sequences or randomly sampling unrelated rows as a time series, which introduces severe target leakage and violates the strict scientific principles of this repository.

**Decision:** ML NOT JUSTIFIED. 
**Implementation:** A Deterministic Operational Trajectory Engine.

## 2. Architecture & Schemas
- **`RiskObservation`**: An input schema representing a verified footprint at a single point in time `T`. It contains canonical `intensity_features` (e.g., magnitude, wind_speed) mapped to the verified hazard type.
- **`TrajectoryAssessment`**: The output schema predicting the trajectory delta across the observation window, alongside `evidence_strength`, `trend_strength`, and explicit `explanation` text.

## 3. Trajectory Definitions & Operational Policy
Since the deterministic thresholds are not empirically validated by historical probability models, they are explicitly designated as **Operational Trajectory Policy v1**.

Trajectories are assessed by computing the delta in a primary intensity feature (e.g. `magnitude` for Earthquakes, `wind_speed` for Cyclones, `water_level` for Floods) over the chronological observation window `t0` to `tN`.

- **RAPIDLY_WORSENING**: The delta exceeds a high threshold (e.g. Cyclone wind speed increases by > 30 km/h).
- **WORSENING**: The delta exceeds a moderate positive threshold (e.g. Cyclone wind speed increases by > 10 km/h).
- **IMPROVING**: The delta decreases by more than the moderate threshold (e.g. Flood water level drops by > 0.5m).
- **STABLE**: The delta fluctuates within the boundaries of `+/- worsening_min`.
- **INSUFFICIENT_EVIDENCE**: Assigned if fewer than 2 chronological observations exist, or if the primary intensity keys are missing from the observations. 

> [!CAUTION]
> **Absence of Evidence is Not Stability**
> A single observation is fundamentally a point, not a line. It has no trajectory. If only 1 observation is available, the engine returns `INSUFFICIENT_EVIDENCE`, not `STABLE`.

## 4. Reassessment Compatibility
The input expects an array of `RiskObservation` objects. In a live system, the orchestration layer will append a new `RiskObservation` to the candidate's history and call this engine, allowing real-time trajectory reassessment as new data arrives.

## 5. Explainability & Provenance
The assessment outputs an explicit `explanation` string defining exactly why a trajectory was chosen.
*Example: "RAPIDLY_WORSENING because wind_speed increased by 40.0 (>= 30.0) over 12.0 hours across 2 observations."*
The schema records the specific observation IDs used, linking back to the verified provenance.

## 6. Known Limitations
- The Delta thresholds are deterministic heuristics ("Operational Policy"). They lack the empirical nuance of a calibrated statistical model.
- The Engine currently computes the delta from the *oldest* valid observation to the *newest*, which may smooth over highly volatile intermediate spikes.
- Trajectory is solely based on intensity features right now, as exposure/impact changes are highly lagging indicators.

## 7. Handoff
With trajectory intelligence complete, the system is ready to hand off to **Phase 2G — Needs Assessment**.
