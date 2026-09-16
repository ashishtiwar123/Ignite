# Derived Impact Severity Target Specification

**Project**: Ignite (PS20)  
**Document**: `docs/SEVERITY_TARGET_SPECIFICATION.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED SPECIFICATION (Implementation Pending Phase 2)  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Target Nature

### Target Classification: `DERIVED IMPACT SEVERITY TARGET` `[VERIFIED]`
The target metric produced and forecast by Project Ignite is classified as a **Derived Impact Severity Target**. 

> [!IMPORTANT]
> **Scientific Defensibility Standard**: The target index is an empirically derived composite proxy representing humanitarian impact magnitude. It is **NOT** a raw ground-truth measurement (such as physical rainfall or seismic PGA), nor is it an arbitrary uncalibrated sum. It is a structured heuristic combination of validated impact dimensions.

---

## 2. Target Definition & Scale Specification

### 2.1 Scale Architecture `[VERIFIED]`
- **Target Name**: `Derived_Impact_Severity_Index` (`DISI`)
- **Target Type**: Continuous Score (\([0.00, 5.00]\)) & Ordinal Class (\(k \in \{0, 1, 2, 3, 4, 5\}\)).
- **Unit**: Standardized Impact Units (Dimensionless).

### 2.2 Ordinal Class Definitions

| Severity Level | Class Label | Qualitative Definition | Empirical Operational Thresholds (Per ADM2 Unit / Month) |
| :---: | :--- | :--- | :--- |
| **0** | **Normal / Baseline** | Baseline environmental & social state; zero disaster emergency declared. | Fatalities = 0; Displaced = 0; Damaged Structures = 0; Baseline food security. |
| **1** | **Minor / Stressed** | Localized disruption; manageable by local municipal emergency services. | Fatalities < 5; Displaced < 100; Minor localized crop/infrastructure damage. |
| **2** | **Moderate Emergency** | Subnational emergency; requires regional humanitarian mobilization. | Fatalities 5–25; Displaced 100–1,000; Moderate structural damage. |
| **3** | **Severe Disaster** | Major disaster event; requires national emergency intervention and international aid. | Fatalities 25–100; Displaced 1,000–10,000; Significant infrastructural destruction. |
| **4** | **Extreme Crisis** | Catastrophic regional impact; critical breakdown of essential services. | Fatalities 100–500; Displaced 10,000–50,000; Widespread collapse. |
| **5** | **Catastrophic Emergency** | Mass-casualty crisis / severe famine; overwhelming collapse of coping capacity. | Fatalities > 500; Displaced > 50,000; Complete destruction of ADM2 infrastructure. |

---

## 3. Mathematical Construction & Normalization

### 3.1 Multi-Hazard Impact Construction Framework `[INFERRED]`
The Derived Impact Severity Target for spatial unit \(i\) over time window \(t\) is constructed from four standardized core impact sub-indices:

$$\text{DISI}_{i,t} = \min \left( 5.0, \; w_D \cdot S_{\text{Mortality}} + w_I \cdot S_{\text{Morbidity}} + w_P \cdot S_{\text{Displacement}} + w_K \cdot S_{\text{Damage}} \right)$$

Where the sub-indices are log-normalized relative to population at risk \(N_{i,t}\):

1. **Mortality Sub-index ($S_{\text{Mortality}}$)**:
   $$S_{\text{Mortality}} = \min \left( 5.0, \; \log_{10} \left( 1 + \frac{\text{Deaths}_{i,t}}{N_{i,t}} \times 10^5 \right) \right)$$

2. **Morbidity Sub-index ($S_{\text{Morbidity}}$)**:
   $$S_{\text{Morbidity}} = \min \left( 5.0, \; \log_{10} \left( 1 + \frac{\text{Injured}_{i,t}}{N_{i,t}} \times 10^5 \right) \right)$$

3. **Displacement Sub-index ($S_{\text{Displacement}}$)**:
   $$S_{\text{Displacement}} = \min \left( 5.0, \; \log_{10} \left( 1 + \frac{\text{IDPs}_{i,t}}{N_{i,t}} \times 10^4 \right) \right)$$

4. **Structural Damage Sub-index ($S_{\text{Damage}}$)**:
   $$S_{\text{Damage}} = \min \left( 5.0, \; \log_{10} \left( 1 + \text{Damaged\_Buildings}_{i,t} \right) \right)$$

### 3.2 Weight Calibration Standard `[ASSUMED]`
Weights are initially set to equal component shares (\(w_D = 0.35, w_I = 0.20, w_P = 0.25, w_K = 0.20\)) and must be calibrated via empirical expert panel verification in Phase 2. **Arbitrary static scaling factors without empirical justification are strictly prohibited.**

---

## 4. Multi-Disaster Generalization

The target framework utilizes **Common Impact Features** across all hazards while incorporating **Disaster-Specific Physical Signals** as predictor features:

```
                  ┌─────────────────────────────────────────┐
                  │    MULTI-HAZARD IMPACT FRAMEWORK        │
                  └────────────────────┬────────────────────┘
                                       │
           ┌───────────────────────────┴───────────────────────────┐
           ▼                                                       ▼
┌──────────────────────────┐                             ┌──────────────────────────┐
│ COMMON IMPACT FEATURES   │                             │ DISASTER-SPECIFIC        │
│ (Target Component)       │                             │ PREDICTOR SIGNALS        │
├──────────────────────────┤                             ├──────────────────────────┤
│ • Direct Mortality       │                             │ • Flood: Precip, Inund   │
│ • Injured Population     │                             │ • Quake: PGA, Magnitude  │
│ • Displaced Persons IDPs │                             │ • Cyclone: Wind, Pressure│
│ • Structural Damage      │                             │ • Fire: Thermal Anomalies │
│ • Infrastructure Loss    │                             │ • Conflict: Event Count  │
└──────────────────────────┘                             └──────────────────────────┘
```

---

## 5. Temporal Boundaries & Leakage Control Protocols

### 5.1 Temporal Timestamps `[VERIFIED]`
- **Observation Window**: Period \([T_{\text{start}}, T_{\text{end}}]\) during which impact events occur.
- **Target Construction Timestamp ($T_{\text{target}}$)**: Timestamp \(T_{\text{end}} + \delta_{\text{audit}}\) when post-disaster impact verification reports are consolidated.
- **Prediction Timestamp ($T_{\text{pred}}$)**: Snapshot date \(T_{\text{pred}} \le T_{\text{start}}\) at which forecasts are generated.

### 5.2 Strict Prediction Boundary Rule `[VERIFIED]`
> [!CAUTION]
> All predictor features evaluated at timestamp \(T_{\text{pred}}\) **MUST ONLY** consume data with observation time \(\le T_{\text{pred}} - \delta_{\text{source\_lag}}\). Components of the target calculation (\(\text{Deaths}_{i,t}, \text{IDPs}_{i,t}\)) occurring within \([T_{\text{start}}, T_{\text{end}}]\) are strictly prohibited from entering the predictor feature matrix.

---

## 6. Target Limitations `[VERIFIED]`

1. **Reporting Delay Variance**: In rural or active conflict zones, casualty and displacement reports may take up to 30 days to stabilize.
2. **Proxy Nature**: The target measures physical and human impact; it does not measure psychological trauma or informal community coping mechanisms.
3. **Census Population Error**: Per-capita log transformations rely on subnational population statistics which may be outdated in refugee-hosting regions.
