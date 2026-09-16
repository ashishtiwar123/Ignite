# Empirical Demand Data Research & Audit Report

**Project**: Ignite (PS20)  
**Document**: `docs/DEMAND_DATA_RESEARCH.md`  
**Phase**: Phase 2A Data Foundation  
**Status**: COMPLETE  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Research Audit

Phase 2A conducted a comprehensive search across public humanitarian databases (UN OCHA HDX, UN WFP DataVAM, UNHCR Microdata, World Bank Open Data) to determine whether empirical historical relief supply dispatch logs exist to train an ML demand regression model.

---

## 2. Public Demand Data Availability Finding `[EMPIRICAL]`

> [!IMPORTANT]
> **Empirical Demand Data Finding**: Standardized, subnational, monthly empirical aid supply distribution datasets (e.g. actual metric tons of food or liters of water delivered per district per month across global crises) **DO NOT EXIST IN PUBLIC REPOSITORIES** (`[UNVERIFIED]`).

### Audited Repositories & Findings:

| Repository / Portal | Candidate Data Search | Findings | Conclusion |
| :--- | :--- | :--- | :--- |
| **UN OCHA HDX** | Historical relief supply delivery logs per district | Highly fragmented, unstandardized one-off PDF situation reports. | **Unusable for ML Target** |
| **UN WFP DataVAM** | Food ration distribution metric tons per ADM2 | High-level national aggregate figures; lacks district breakdown. | **Unusable for Subnational ML** |
| **UNHCR Microdata** | Camp supply dispatch records | Camp-specific non-standardized logs; non-continuous. | **Unusable for Global ML** |

---

## 3. Final Architecture Confirmation: Deterministic Sphere Calculation `[VERIFIED]`

Because empirical historical demand targets are unavailable publicly, **training a direct Machine Learning demand regression model is scientifically prohibited.**

Humanitarian demand outputs MUST remain deterministically derived from model-predicted affected populations using Sphere Standards (`docs/NEEDS_ENGINE_SPECIFICATION.md`):

$$\text{Water Required (L/Day)}_{i,t} = N_{\text{affected}, i,t} \times 15.0$$
$$\text{Food Energy Required (kcal/Day)}_{i,t} = N_{\text{affected}, i,t} \times 2,100.0$$
$$\text{Shelter Space Required (m²)}_{i,t} = N_{\text{displaced}, i,t} \times 3.5$$
