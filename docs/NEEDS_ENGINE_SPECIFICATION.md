# Sphere Needs Engine & Calculation Specification

**Project**: Ignite (PS20)  
**Document**: `docs/NEEDS_ENGINE_SPECIFICATION.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED & FROZEN SPECIFICATION  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Separation of Responsibilities

This document defines the mathematical translation engine converting ML impact predictions into physical humanitarian resource requirements using international Sphere Standards.

```
┌───────────────────────────┐         ┌───────────────────────────┐         ┌───────────────────────────┐
│     ML ENGINE (Probabilistic)│ ──►   │ DETERMINISTIC NEEDS RULES │ ──►   │ OPTIMIZATION (OR-Tools)   │
├───────────────────────────┤         ├───────────────────────────┤         ├───────────────────────────┤
│ • Affected Pop Estimate   │         │ • WASH: 15 L / person / day│         │ • Warehouse Matching      │
│ • Severity Score (DISI)   │         │ • Food: 2,100 kcal / day  │         │ • Route Routing           │
│ • Trajectory Escalation   │         │ • Shelter: 3.5 m² / person│         │ • Fleet Constraint Solver │
└───────────────────────────┘         └───────────────────────────┘         └───────────────────────────┘
```

> [!CAUTION]
> **LLM Boundary Restriction**: Large Language Models (LLMs) are strictly **PROHIBITED** from calculating or outputting numerical supply quantities, water volumes, or food tonnage. All quantitative supply math MUST be executed by the deterministic rules engine.

---

## 2. Deterministic Sphere Needs Equations

### 2.1 Water, Sanitation, & Hygiene (WASH) Engine `[VERIFIED]`
- **Standard Reference**: Sphere Handbook 2018 (WASH Standard 2.1).
- **Minimum Threshold**: $15.0 \text{ Liters / person / day}$.

$$\text{Water Needed (Liters/Day)}_{i,t} = N_{\text{affected}, i,t} \times 15.0 \times \left( 1.0 + 0.10 \times \mathbb{I}(\text{Severity}_{i,t} \ge 4) \right)$$

- **Supply Packaging Translation**: 
  $$\text{Water Purification Tablets (Boxes)}_{i,t} = \left\lceil \frac{N_{\text{affected}, i,t} \times 30 \text{ Days}}{500 \text{ Tablets/Box}} \right\rceil$$

### 2.2 Food Security & Nutrition Engine `[VERIFIED]`
- **Standard Reference**: Sphere Handbook 2018 (Food Security Standard 2.1).
- **Minimum Energy Threshold**: $2,100 \text{ kcal / person / day}$.
- **Standard Dry Ration Basket**:
  - Cereal (Maize/Rice): $450 \text{ g/person/day}$
  - Pulses (Beans/Lentils): $50 \text{ g/person/day}$
  - Vegetable Oil: $25 \text{ g/person/day}$
  - Iodized Salt: $5 \text{ g/person/day}$

$$\text{Cereal Required (Metric Tons / Month)}_{i,t} = \frac{N_{\text{affected}, i,t} \times 0.450 \text{ kg} \times 30 \text{ Days}}{1000 \text{ kg/MT}}$$

### 2.3 Emergency Shelter & Settlement Engine `[VERIFIED]`
- **Standard Reference**: Sphere Handbook 2018 (Shelter Standard 3.1).
- **Minimum Covered Space**: $3.5 \text{ m² / person}$.

$$\text{Shelter Space Needed (m²)}_{i,t} = N_{\text{displaced}, i,t} \times 3.5$$
$$\text{Family Tarpaulins Required (Units)}_{i,t} = \left\lceil \frac{N_{\text{displaced}, i,t}}{5 \text{ Persons/Household}} \right\rceil \times 2$$

---

## 3. Needs Engine Integration Matrix

| Input Metric | Source Component | Validation Bounds | Output Needs Variable | Target Packaging SKU |
| :--- | :--- | :--- | :--- | :--- |
| `affected_pop_count` | ML Severity Engine | $\ge 0$ | Total Water & Food Volume | Liters / MT Grains |
| `displaced_pop_count` | ML Exposure Engine | $\ge 0$ | Covered Shelter Area & NFIs | Tarpaulins / Hygiene Kits |
| `disi_severity_score` | ML Assessment Engine | $[0.0, 5.0]$ | Emergency Urgency Scaling | Priority Weight Multiplier |
