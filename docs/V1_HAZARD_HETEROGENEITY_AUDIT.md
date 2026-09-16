# Phase 2C.1 — Hazard Heterogeneity Audit
**Project**: Ignite (PS20)  
**Document**: `docs/V1_HAZARD_HETEROGENEITY_AUDIT.md`  
**Phase**: Phase 2C.1 Audit  
**Date**: 2026-09-16  

---

## 1. Physical Mechanism Disconnect

| Hazard Type | Sample Size | Primary Physical Feature $X$ | Pearson Correlation with $Y_{impact}$ | Spearman $\rho$ |
|---|---|---|---|---|
| **Earthquake** | 66 | `seismic_magnitude` ($Mw$) | $r = +0.0768$ ($p=0.54$) | $\rho = +0.1121$ ($p=0.37$) |
| **Storm / Cyclone** | 270 | `cyclone_max_wind_knots` | $r = -0.1983$ ($p=0.001$) | $\rho = -0.2076$ ($p=0.0006$) |

---

## 2. Key Forensic Findings

1. **Incompatible Feature Spaces**: Seismic magnitude and depth are strictly `NaN` for storms; cyclone wind and pressure are strictly `NaN` for earthquakes. The global model is forced to split on an un-shared feature space.
2. **Counter-Intuitive Storm Wind Correlation**: In the 270 matched IBTrACS storm records, `cyclone_max_wind_knots` exhibits a **negative correlation with impact** ($r = -0.1983$). Why? Because storm impact in EM-DAT is heavily driven by **rainfall/flooding and local vulnerability** (e.g., in low-income developing nations), whereas peak wind speed alone fails to capture total flood surge without precipitation telemetry.
3. **Conclusion**: Combining Earthquakes and Cyclones into a single global model with only 6 physical features creates severe hazard heterogeneity that degrades learning.
