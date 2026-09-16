# Phase 2G: Needs Assessment Engine

**Objective:**
Build a deterministic Needs Assessment Engine that converts a `VerifiedIncident`, severity, trajectory, and exposed population into structured `ResourceRequirement` records based on authoritative humanitarian standards.

## 1. Scope & Core Principles
The Needs Assessment Engine purely identifies the *humanitarian demand* (e.g., "This incident requires X metric tons of food"). 
It explicitly **DOES NOT**:
- Allocate resources.
- Select warehouses or vehicles.
- Solve routing or fleet constraints (which belongs to Phase 2I / OR-Tools).
- Use probabilistic ML models to guess resource needs.

All quantitative logic is strictly deterministic and rooted in documented humanitarian standards. 

## 2. Architecture & Contracts
- **`NeedsAssessmentInput`**: The canonical input schema encapsulating the verified incident ID, hazard type, severity score, trajectory, and critically, the `affected_population` and `displaced_population`.
- **`ResourceRequirement`**: The canonical output schema returning the resource category, standard unit, computed quantity, urgency, generation provenance, and a plain-text `explanation`.

## 3. Humanitarian Standards & Rules
The engine incorporates the following quantitative rules as **AUTHORITATIVE STANDARDS** derived from the Sphere Handbook 2018 (`docs/NEEDS_ENGINE_SPECIFICATION.md`):

1. **Water Requirements (`WATER`)**: 
   - 15.0 Liters per person per day.
   - *Operational Policy*: Scaled by a 1.1x multiplier if the ML Severity Engine scored the incident $\ge 4.0$.
2. **Food Security (`FOOD`)**: 
   - 450g Cereal, 50g Pulses, 25g Veg Oil, 5g Salt per person per day. (Currently outputs Cereal required in Metric Tons).
3. **Shelter Requirements (`SHELTER`)**:
   - 3.5 m² per person, translated to 2 Family Tarpaulins per 5 persons (household).

## 4. Qualitative Demand (Operational Heuristics)
Because there are no globally applicable deterministic formulas for predicting exact quantities of medical kits or rescue vehicles based solely on population, the engine applies the following **OPERATIONAL POLICIES** to output qualitative urgency:

1. **Medical Support (`MEDICAL`)**: 
   - Classifies demand urgency (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) based on a matrix of severity and the current trajectory (worsening conditions elevate urgency).
2. **Search and Rescue (`RESCUE`)**: 
   - Highly hazard-dependent. Earthquakes and Landslides with high severity trigger `CRITICAL` or `HIGH` urgency, whereas Cyclones or Floods trigger `MODERATE` unless extremely severe.

## 5. Missing Data & Silent Defaults
The engine enforces a strict policy against silent defaults:
- If `affected_population` is missing, `WATER` and `FOOD` requirements are safely generated but their status is explicitly marked as `INSUFFICIENT_DATA`, with no fabricated quantity.
- If `displaced_population` is missing, `SHELTER` is marked `INSUFFICIENT_DATA`.
- A provided value of `0` is respected (calculating 0 requirement).

## 6. Known Limitations & Future Improvements
- Food calculation is currently abstracted to Cereal tonnage. A full dry-ration basket expansion could be implemented.
- Duration is not fully integrated into multiplying total requirements yet; all outputs currently specify a `per_day` or `immediate` time window, which is safer than assuming a 7-day or 30-day operation without evidence.
- Medical and Rescue rules remain qualitative heuristics.

## 7. Handoff
With Needs Assessment completed deterministically, the system is now ready to hand off to **Phase 2H — Priority Engine**.
