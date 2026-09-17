# Phase 6F — Multi-Hazard Severity Engine Documentation

## 1. Architectural Summary & Scope

Phase 6F extends PS20's severity assessment capability to support multiple natural disaster hazards while preserving the existing, validated ML severity predictor (`SeverityPredictorV2`) for Earthquake and Cyclone/Storm incidents.

The `UnifiedSeverityEngine` acts as a central router that delegates incoming incidents to either:
1. **Machine Learning Predictor (`SeverityPredictorV2`)**: Used for `EARTHQUAKE`, `CYCLONE`, and `STORM` hazards.
2. **Deterministic Operational Policies (`BaseSeverityPolicy`)**:
   - `FloodPolicyV1`: Evaluates water depth, current speed, area submerged, structural damage, trapped persons, and contamination risk.
   - `WildfirePolicyV1`: Evaluates fire front distance, rate of spread, wind speed, air quality index (AQI), structure/containment risk, and evacuation status.
   - `HeavyRainfallPolicyV1`: Evaluates 24-hour rainfall mm, rain rate mm/hr, flash flood warning status, soil saturation index, wind speed, pressure, displacement, and population.

---

## 2. Hazard Routing Strategy

| Hazard Type | Routing Destination | Strategy Type | Notes |
| :--- | :--- | :--- | :--- |
| `EARTHQUAKE` | `SeverityPredictorV2` | Machine Learning | XGBoost classification across 4 severity levels |
| `CYCLONE` / `STORM` | `SeverityPredictorV2` | Machine Learning | Maps `"CYCLONE"` to `"Storm"` for `PredictorV2` while preserving `"Cyclone"` in returned output |
| `FLOOD` | `FloodPolicyV1` | Deterministic Policy | Rule-based factor accumulation, bounded score 0–10 |
| `WILDFIRE` / `FIRE` | `WildfirePolicyV1` | Deterministic Policy | Rule-based factor accumulation, bounded score 0–10 |
| `HEAVY_RAINFALL` | `HeavyRainfallPolicyV1` | Deterministic Policy | Rule-based factor accumulation, bounded score 0–10 |
| *Other / Unknown* | Fallback | Policy / Status | Returns `status="unsupported_hazard"` with `severity_score=None` |

---

## 3. Policy Equations & Attribute Mappings

### 3.1 Flood Policy (`FLOOD_POLICY_V1`)
- **Water Depth Factor (Max +2.5)**: $\min(2.5, \text{water\_depth\_m} \times 0.833)$
- **Current Speed Factor (Max +1.5)**: $\min(1.5, \text{current\_speed\_m\_s} \times 0.5)$
- **Submerged Area Factor (Max +1.5)**: $\min(1.5, \text{submerged\_area\_sq\_km} \times 0.15)$
- **Structural Damage Factor (Max +1.5)**: Structural damage ratio $\times 1.5$
- **Trapped Persons Factor (Max +2.0)**: $\min(2.0, \log_{10}(\text{trapped\_count} + 1) \times 1.0)$
- **Contamination / Utility Factor (Max +1.0)**: Critical infrastructure / toxic contamination presence $\times 1.0$

### 3.2 Wildfire Policy (`WILDFIRE_POLICY_V1`)
- **Fire Front Distance Factor (Max +2.5)**: Exponential proximity score $\max(0, 2.5 - (\text{dist\_km} \times 0.5))$
- **Rate of Spread Factor (Max +1.5)**: $\min(1.5, \text{ros\_km\_h} \times 0.3)$
- **Wind Speed Factor (Max +1.0)**: $\min(1.0, \text{wind\_km\_h} \times 0.02)$
- **Air Quality / AQI Factor (Max +1.0)**: $\min(1.0, \max(0, \text{aqi} - 100) \times 0.0033)$
- **Structure Risk & Containment Factor (Max +2.0)**: Containment % inverted + structural threat
- **Evacuation Factor (Max +2.0)**: Order active, trapped count, and road blockages

### 3.3 Heavy Rainfall Policy (`HEAVY_RAINFALL_POLICY_V1`)
- **24h Rainfall Factor (Max +3.0)**: $\min(3.0, \text{rainfall\_24h\_mm} \times 0.015)$
- **Hourly Rain Rate Factor (Max +2.0)**: $\min(2.0, \text{rain\_rate\_mm\_hr} \times 0.04)$
- **Flash Flood Warning Factor (Max +1.5)**: Warning level $\times 1.5$
- **Soil Saturation Factor (Max +1.0)**: $\min(1.0, \text{soil\_saturation\_pct} \times 0.01)$
- **Wind / Storm Factor (Max +0.5)**: $\min(0.5, \text{wind\_speed\_kmh} \times 0.0083)$
- **Pressure / Low System Factor (Max +0.5)**: Pressure drop $\le 1000\text{ hPa} \implies +0.5$
- **Displacement / Population Factor (Max +1.5)**: Population density & displacement numbers

---

## 4. Operational Boundaries & Evidence Coverage

- Policy assessments compute an **Evidence Coverage Ratio**:
  $$\text{Evidence Coverage} = \frac{\text{Available Policy Factors}}{\text{Total Policy Factors}}$$
- Missing inputs are tracked explicitly; missing values are **never converted to zero or fabricated**.
- Policy outputs set `confidence = None` and `probabilities = None` to maintain strict distinction from statistical ML models.

---

## 5. Verification & Governance Integration

- The `situation_assessment_node` invokes `UnifiedSeverityEngine` only for verified incidents (`VERIFIED` or `PARTIALLY_VERIFIED`).
- Human-in-the-loop (HITL) approval gates and read-only governance endpoints remain completely untouched and fully authoritative.
