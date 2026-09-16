# Ignite Multi-Resolution Data & Spatial Architecture

**Project**: Ignite (PS20)  
**Document**: `docs/DATA_ARCHITECTURE.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED & FROZEN (Supersedes DEC-002 Pure Monthly Aggregation)  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Architectural Shift

### Superseding Statement `[VERIFIED]`
> [!IMPORTANT]
> **DEC-002 (Mandatory Subnational Monthly Feature Aggregation) IS SUPERSEDED.**  
> Project Ignite adopts a **Multi-Resolution Architecture**. While strategic ML risk trajectory models operate at subnational ADM2 level on monthly horizons, operational decision engines (resource allocation, shelter logistics, incident dispatch) operate at fine-grained spatial points (incidents, warehouses, shelters, H3 grids) and rapid temporal steps (hourly / daily).

---

## 2. Dual-Track Spatial & Temporal Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PROJECT IGNITE DUAL-TRACK ARCHITECTURE              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ TRACK A: STRATEGIC FORECASTING TRACK (ML Prediction Engine)              │
│   • Spatial Granularity  : ADM2 (District / County P-code)              │
│   • Temporal Resolution  : Monthly (`YYYY-MM`)                          │
│   • Output               : 0-5 Derived Severity & Risk Trajectory        │
│   • Core Consumer        : Executive Situation Dashboard & UN OCHA Reports│
│                                                                         │
│ TRACK B: OPERATIONAL RESPONSE TRACK (Decision & Allocation Engine)      │
│   • Spatial Granularity  : Point (Incident Lat/Lon, Warehouse, Camp)   │
│                            and Uber H3 Hexagonal Grid (Res 7-9)         │
│   • Temporal Resolution  : Near Real-Time (Hourly / Daily Steps)        │
│   • Output               : Sphere Resource Demands & OR-Tools Allocation│
│   • Core Consumer        : Logistics Responders & Dispatch Operations   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Spatial Resolution Hierarchy

`[VERIFIED]` Data entities are mapped across four distinct spatial tiers:

| Spatial Tier | Geometry Type | Example Entity | Typical Use Case | Primary Key Standard |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 0: National** | Polygon | Country Boundary | Macro vulnerability & INFORM risk index | `ISO3` (e.g. `SDN`) |
| **Tier 1: Admin-1** | Polygon | State / Province | Regional resource budgeting & IPC surveys | `ADM1_PCODE` (e.g. `SDN001`) |
| **Tier 2: Admin-2** | Polygon | District / County | Strategic ML severity & trajectory predictions | `ADM2_PCODE` (e.g. `SDN001002`) |
| **Tier 3: Operational Grid** | Polygon (Hexagon)| H3 Grid Cell (Res 7-9) | Hazard exposure modeling (Flood/Fire extent) | `H3_INDEX` (e.g. `8828308281fffff`) |
| **Tier 4: Facility / Point** | Point (Lat/Lon) | Warehouse, Shelter, Incident | OR-Tools logistics routing & incident assignment | `FACILITY_ID` / `INCIDENT_ID` |

---

## 4. Operational vs. Strategic Granularity Separation

### 4.1 ML Prediction Granularity (Strategic Track) `[VERIFIED]`
- **Target Key**: `(ADM2_PCODE, Year, Month)`
- **Purpose**: Establishes medium-term disaster escalation risk profiles and district-level vulnerability trends.
- **Model Framework**: Gradient Boosting (XGBoost / LightGBM) for classification of trajectory momentum \(\Delta \text{Severity}_{t+h}\).

### 4.2 System Operational Granularity (Execution Track) `[VERIFIED]`
- **Target Key**: `(Incident_ID, Facility_ID, Timestamp_UTC)`
- **Purpose**: Solves actual humanitarian resource supply allocation (water supply, emergency food, medical kits, shelter allocation) constrained by real warehouse inventory and road network access.
- **Optimization Framework**: Deterministic Sphere Standards translation coupled with OR-Tools constraint optimization.

---

## 5. Architectural Guardrails for Phase 2 Implementation `[VERIFIED]`

1. **No Spatial Downgrading**: Do NOT aggregate point-based incident dispatch requirements up to district averages before sending them to the resource allocation engine.
2. **Deterministic Downscaling**: ADM2-level ML population predictions must be downscaled to operational facilities using population density rasters (e.g., WorldPop / GPWv4).
3. **Decoupled Pipelines**: Feature pipelines for Track A (ML) and Track B (OR-Tools) must execute independently to prevent execution bottlenecks.
