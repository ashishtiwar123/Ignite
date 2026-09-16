# Source-Specific Temporal Data & Latency Policy

**Project**: Ignite (PS20)  
**Document**: `docs/TEMPORAL_DATA_POLICY.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED & FROZEN (Supersedes DEC-004 Universal 14-Day Lag)  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Policy Shift

### Superseding Statement `[VERIFIED]`
> [!IMPORTANT]
> **DEC-004 (Universal 14-Day Reporting Lag) IS SUPERSEDED.**  
> Applying a blanket 14-day delay across all input streams artificially degrades near-real-time emergency response capabilities (e.g. seismic or flood telemetry). Project Ignite replaces the universal lag rule with a **Source-Specific Data Availability & Latency Policy**.

---

## 2. Temporal Timestamp Standard Definitions

To eliminate timestamp ambiguity across data streams, every ingested data point must record six discrete temporal attributes:

```
[A. Event Occurrence Time] ──► [B. Data Observation Time] ──► [C. Data Publication Time]
                                                                      │
[F. Feature Cutoff / Pred Time] ◄── [E. System Ingestion Time] ◄──────┴──► [D. Data Revision Time]
```

1. **Event Occurrence Time ($T_{\text{occur}}$)**: Actual physical timestamp when the hazard or incident occurred.
2. **Data Observation Time ($T_{\text{obs}}$)**: Sensor or field observer recording timestamp.
3. **Data Publication Time ($T_{\text{pub}}$)**: Official release timestamp by the data provider API.
4. **Data Revision Time ($T_{\text{rev}}$)**: Timestamp of retroactive edits or field verification updates.
5. **System Ingestion Time ($T_{\text{ingest}}$)**: Local timestamp when Ignite ingests the data record into memory/storage.
6. **Feature Cutoff / Prediction Time ($T_{\text{pred}}$)**: Snapshot timestamp at which the ML model generates predictions.

---

## 3. Source-Specific Data Availability Matrix

`[OFFICIAL DOCUMENTATION]` Input data streams are categorized into four distinct latency Tiers:

| Data Source | Domain | Target Latency Tier | Typical Provider Release Delay ($\delta_{\text{pub}}$) | Mandatory Feature Cutoff Guardrail | Ingestion Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **USGS / EMSC** | Seismic Events | **Tier 0: Real-Time** | < 15 Minutes | $T_{\text{occur}} \le T_{\text{pred}} - 1\text{ Hour}$ | Ingest continuously via websocket/polling. |
| **Copernicus / GDACS** | Flood & Cyclone Telemetry | **Tier 1: Near Real-Time** | 3 to 24 Hours | $T_{\text{occur}} \le T_{\text{pred}} - 24\text{ Hours}$ | Daily automated batch ingestion. |
| **NASA FIRMS** | Thermal Wildfire Anomalies | **Tier 1: Near Real-Time** | 3 to 12 Hours | $T_{\text{occur}} \le T_{\text{pred}} - 12\text{ Hours}$ | 6-hour polling cycle. |
| **ACLED** | Conflict & Political Violence | **Tier 2: Weekly Lagged** | 7 to 14 Days | $T_{\text{pub}} \le T_{\text{pred}} - 14\text{ Days}$ | Weekly batch run with retroactive revision handling. |
| **IPC / FEWS NET** | Food Security Assessments | **Tier 3: Seasonal / Periodic** | 30 to 90 Days | Ingest published valid surveys at $T_{\text{pred}}$ | Forward-fill valid survey state until next update. |
| **INFORM Index** | Country Composite Risk | **Tier 4: Static Annual** | Annual (January Release) | Ingest latest annual edition | Annual baseline update. |

---

## 4. Multi-Horizon Temporal Aggregation Framework

`[VERIFIED]` The system separates temporal aggregation windows based on operational task requirements:

1. **Emergency Operational Mode (Rapid Response)**:
   - **Temporal Step**: 24-Hour / Daily rolling steps.
   - **Inputs**: Tier 0 and Tier 1 near-real-time streams exclusively.
   - **Horizon**: Immediate 1-day to 7-day impact forecasting.

2. **Strategic Crisis Monitoring Mode (Early Warning)**:
   - **Temporal Step**: Monthly calendar windows (`YYYY-MM`).
   - **Inputs**: Harmonized multi-tier streams (Tier 0 through Tier 4).
   - **Horizon**: Multi-horizon 1, 3, and 6-month risk trajectory forecasting (\(\Delta \text{Severity}_{t+h}\)).

---

## 5. Temporal Leakage Audit Rule

> [!CAUTION]
> **Leakage Prevention Assertion**: Under no circumstances may an input feature computed for snapshot date $T_{\text{pred}}$ ingest a data record where $T_{\text{pub}} > T_{\text{pred}}$. In backtesting and validation split generation, feature generation code MUST simulate point-in-time database snapshots using $T_{\text{pub}}$ metadata to prevent future-data contamination.
