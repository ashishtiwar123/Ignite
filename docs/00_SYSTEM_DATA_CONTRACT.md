# Ignite End-to-End System Data Contract & Lifecycle Specification

**Project**: Ignite (PS20)  
**Document**: `docs/00_SYSTEM_DATA_CONTRACT.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED & FROZEN  
**Last Updated**: 2026-09-16  

---

## 1. Executive Summary & Pipeline Overview

This document specifies the authoritative **End-to-End System Data Lifecycle** for Project Ignite. It governs data transformations across 15 discrete pipeline stages from initial unverified raw field report ingestion down to continuous reassessment feedback.

---

## 2. Comprehensive 15-Stage Data Lifecycle Specification

```
RAW REPORT ──► STRUCTURED REPORT ──► VERIFIED INCIDENT ──► SITUATION INTELLIGENCE
                                                                 │
REASSESSMENT ◄── FEEDBACK ◄── EXECUTION ◄── ALLOCATION PLAN ◄───┴──► SEVERITY / RISK / EXPOSURE
    │                                                                   │
    └───────────────────── TASK ASSIGNMENT ◄── OPTIMIZATION ◄── NEEDS / RESOURCE REQUIREMENTS
```

---

### STAGE 1: RAW REPORT `[VERIFIED]`
- **Stage Owner**: Ingestion Gateway Service
- **Input**: Raw unstructured incident messages, SMS alerts, field worker entries, RSS feeds, emergency calls.
- **Input Source**: Emergency hotline APIs, field worker mobile app, partner webhooks.
- **Data Format**: Raw String / Unstructured JSON / Audio transcript.
- **Validation Rules**: Non-empty payload check; rate-limiting sanity check.
- **Processing Step**: Ingest payload, attach UTC reception metadata, assign `raw_report_id`.
- **Output**: Envelope-wrapped raw report object.
- **Output Format**: JSON (`RawReportEnvelope`).
- **Persistence Mechanism**: Append-only raw event stream.
- **Storage Location**: Storage Lake / Blob Store (`s3://ignite-raw-reports/`).
- **Consumer**: AI / LLM Structuring Service.
- **Failure Behavior**: DLQ (Dead Letter Queue) routing after 3 retries; log error.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Preserve raw source text unmodified for legal compliance.

---

### STAGE 2: STRUCTURED REPORT `[VERIFIED]`
- **Stage Owner**: LLM Extraction Service
- **Input**: `RawReportEnvelope` (unstructured text).
- **Input Source**: STAGE 1 Output.
- **Data Format**: JSON.
- **Validation Rules**: Schema validation against Pydantic model (`StructuredReport`).
- **Processing Step**: Extract hazard category, location mentions, affected counts, and urgency metrics using LLM parsing.
- **Output**: Canonical structured report object.
- **Output Format**: JSON (`StructuredReport`).
- **Persistence Mechanism**: Relational DB insert.
- **Storage Location**: PostgreSQL (`table: structured_reports`).
- **Consumer**: Verification & Deduplication Engine.
- **Failure Behavior**: Flag for manual human operator triage review.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Include raw text source snippets as evidence keys for extracted entities.

---

### STAGE 3: VERIFIED INCIDENT `[VERIFIED]`
- **Stage Owner**: Incident Verification Engine
- **Input**: `StructuredReport` + Spatial Boundary P-codes + External Telemetry.
- **Input Source**: STAGE 2 Output + USGS/Copernicus/GDACS APIs.
- **Data Format**: JSON / GeoJSON.
- **Validation Rules**: Geofence containment check against OCHA P-codes; confidence score \(\ge 0.65\).
- **Processing Step**: Deduplicate reports, cross-reference physical sensor telemetry, resolve spatial `ADM2_PCODE`.
- **Output**: Verified Incident Record (`VerifiedIncident`).
- **Output Format**: GeoJSON / JSON.
- **Persistence Mechanism**: Spatial Relational DB.
- **Storage Location**: PostGIS (`table: verified_incidents`).
- **Consumer**: Situation Intelligence Engine & ML Feature Pipelines.
- **Failure Behavior**: Retain in `unverified_incidents` queue pending additional signals.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Log matching rules and physical sensor correlation scores.

---

### STAGE 4: SITUATION INTELLIGENCE `[VERIFIED]`
- **Stage Owner**: Intelligence Fusion Service
- **Input**: `VerifiedIncident` records + Historical context (INFORM, IPC).
- **Input Source**: STAGE 3 Output + Feature Lake.
- **Data Format**: Multi-dimensional Feature Tensor (Parquet / JSON).
- **Validation Rules**: Check feature completeness; zero nulls in spatial P-code or date keys.
- **Processing Step**: Aggregate incident metrics into spatial (ADM2/H3) and temporal (daily/monthly) feature vectors.
- **Output**: Unified Situation Intelligence Snapshot (`SituationIntelligence`).
- **Output Format**: Parquet / JSON.
- **Persistence Mechanism**: Feature Store.
- **Storage Location**: Feature Lake (`s3://ignite-feature-store/`).
- **Consumer**: ML Assessment Engine.
- **Failure Behavior**: Fall back to historical baseline average if current stream is delayed.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Store feature lineage and source dataset release timestamps.

---

### STAGE 5: SEVERITY / RISK / EXPOSURE ASSESSMENT `[VERIFIED]`
- **Stage Owner**: ML Assessment Engine
- **Input**: `SituationIntelligence` feature snapshot.
- **Input Source**: STAGE 4 Output.
- **Data Format**: Numerical Tensor / JSON.
- **Validation Rules**: Output score range check (\([0.0, 5.0]\)); probability sum equals 1.0.
- **Processing Step**: Run ML models to predict Derived Impact Severity Score, Exposure Level, and Risk Escalation Trajectory (\(\Delta \text{Severity}_{t+h}\)).
- **Output**: Assessment Record (`SeverityAssessment`).
- **Output Format**: JSON (`SeverityAssessment`).
- **Persistence Mechanism**: Relational DB.
- **Storage Location**: PostgreSQL (`table: severity_assessments`).
- **Consumer**: Needs Engine & Executive Situation Map.
- **Failure Behavior**: Fall back to rule-based heuristic score if ML service times out (>2000ms).
- **Versioning Strategy**: Model Version ID tagged (e.g., `model_v1.2.0`).
- **Explainability Requirements**: Generate SHAP feature importance values for top 5 score drivers.

---

### STAGE 6: NEEDS ASSESSMENT `[VERIFIED]`
- **Stage Owner**: Deterministic Needs Engine
- **Input**: `SeverityAssessment` + Population Density Estimates.
- **Input Source**: STAGE 5 Output + WorldPop Raster.
- **Data Format**: JSON.
- **Validation Rules**: Non-negative population and requirement values.
- **Processing Step**: Apply Sphere Standards (15L water/person/day, 2,100 kcal/person/day, 3.5m² shelter/person) to affected population estimates.
- **Output**: Humanitarian Needs Profile (`NeedsAssessment`).
- **Output Format**: JSON (`NeedsAssessment`).
- **Persistence Mechanism**: Relational DB.
- **Storage Location**: PostgreSQL (`table: needs_assessments`).
- **Consumer**: Resource Requirement Engine.
- **Failure Behavior**: Log alert and raise error if affected population is undefined.
- **Versioning Strategy**: v1.0 (Sphere 2018 Standard Edition).
- **Explainability Requirements**: Explicitly expose deterministic math formulas used in calculation.

---

### STAGE 7: RESOURCE REQUIREMENTS `[VERIFIED]`
- **Stage Owner**: Needs Engine / Supply Translator
- **Input**: `NeedsAssessment`.
- **Input Source**: STAGE 6 Output.
- **Data Format**: Itemized Supply Matrix (JSON).
- **Validation Rules**: Item SKUs must match canonical inventory catalog codes.
- **Processing Step**: Translate raw needs (water liters, food calories) into physical supply packages (Water Purification Kits, Grain Metric Tons, Emergency Tents).
- **Output**: Itemized Resource Requirement Object (`ResourceRequirement`).
- **Output Format**: JSON.
- **Persistence Mechanism**: Relational DB.
- **Storage Location**: PostgreSQL (`table: resource_requirements`).
- **Consumer**: Priority & Optimization Engine.
- **Failure Behavior**: Flag unmapped item SKUs for administrator configuration.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Document unit translation multipliers (e.g. 1 kit = 5 persons / month).

---

### STAGE 8: INVENTORY STATE `[VERIFIED]`
- **Stage Owner**: Warehouse Integration Adapter
- **Input**: Warehouse stock levels, facility coordinates, available transport fleet capacity.
- **Input Source**: Partner ERP / Logistics API / Manual Inventory Logs.
- **Data Format**: JSON.
- **Validation Rules**: Quantity \(\ge 0\); valid warehouse `FACILITY_ID`.
- **Processing Step**: Ingest, normalize, and index real-time available relief inventory.
- **Output**: Inventory Snapshot (`InventoryState`).
- **Output Format**: JSON.
- **Persistence Mechanism**: Cache / Relational DB.
- **Storage Location**: Redis Cache + PostgreSQL (`table: inventory_state`).
- **Consumer**: Optimization Engine.
- **Failure Behavior**: Use last known cached inventory state; flag as stale if >12 hours old.
- **Versioning Strategy**: Snapshot Timestamp.
- **Explainability Requirements**: Display exact warehouse locations and timestamp of stock audit.

---

### STAGE 9: PRIORITY ASSESSMENT `[VERIFIED]`
- **Stage Owner**: Priority Engine
- **Input**: `SeverityAssessment` + `NeedsAssessment` + Vulnerability Scores.
- **Input Source**: STAGE 5 + STAGE 6 Outputs.
- **Data Format**: Ranked Priority Queue (JSON).
- **Validation Rules**: Priority rank must be strictly ordered without duplicate rank ties.
- **Processing Step**: Calculate Urgency Index based on trajectory escalation speed and population vulnerability.
- **Output**: Ranked Location Priority List (`PriorityAssessment`).
- **Output Format**: JSON.
- **Persistence Mechanism**: Relational DB.
- **Storage Location**: PostgreSQL (`table: priority_assessments`).
- **Consumer**: Optimization Engine.
- **Failure Behavior**: Fall back to pure Severity Score ordering.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Show weighting composition of Priority Score.

---

### STAGE 10: OPTIMIZATION PLAN `[VERIFIED]`
- **Stage Owner**: Resource Optimization Engine (OR-Tools)
- **Input**: `ResourceRequirement` + `InventoryState` + `PriorityAssessment` + Road Network Matrix.
- **Input Source**: STAGE 7 + STAGE 8 + STAGE 9 Outputs.
- **Data Format**: Optimization Problem Definition (JSON).
- **Validation Rules**: Solvability check; valid distance matrix.
- **Processing Step**: Solve constrained Mixed Integer Linear Programming (MILP) problem maximizing supply delivery under transport capacity and time constraints.
- **Output**: Solved Allocation Plan (`AllocationPlan`).
- **Output Format**: JSON.
- **Persistence Mechanism**: Relational DB.
- **Storage Location**: PostgreSQL (`table: allocation_plans`).
- **Consumer**: Task Assignment Engine & Logistics Dashboard.
- **Failure Behavior**: If infeasible, relax secondary constraints and return partial allocation plan with explicit shortage warnings.
- **Versioning Strategy**: Optimization Engine Version.
- **Explainability Requirements**: Return shadow prices and binding constraint summaries explaining supply bottlenecks.

---

### STAGE 11: ALLOCATION PLAN `[VERIFIED]`
- **Stage Owner**: Decision Engine
- **Input**: Solved `AllocationPlan` from STAGE 10.
- **Input Source**: STAGE 10 Output.
- **Data Format**: JSON.
- **Validation Rules**: Human Commander Sign-off (if high severity) or automated policy approval.
- **Processing Step**: Freeze allocation plan, lock inventory allocations, generate operational dispatch orders.
- **Output**: Approved Allocation Plan (`ApprovedAllocationPlan`).
- **Output Format**: JSON.
- **Persistence Mechanism**: Relational DB.
- **Storage Location**: PostgreSQL (`table: approved_allocations`).
- **Consumer**: Task Assignment Engine.
- **Failure Behavior**: Revert locked inventory if sign-off is rejected.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Record commander override notes or automated policy rule ID.

---

### STAGE 12: TASK ASSIGNMENT `[VERIFIED]`
- **Stage Owner**: Logistics Dispatch Service
- **Input**: `ApprovedAllocationPlan`.
- **Input Source**: STAGE 11 Output.
- **Data Format**: Dispatch Orders (JSON / PDF / API Call).
- **Validation Rules**: Assigned driver/vehicle status must be `AVAILABLE`.
- **Processing Step**: Split allocation plan into actionable warehouse pick-lists and driver transport routes.
- **Output**: Individual Dispatch Tasks (`TaskAssignment`).
- **Output Format**: JSON.
- **Persistence Mechanism**: Relational DB.
- **Storage Location**: PostgreSQL (`table: dispatch_tasks`).
- **Consumer**: Field Responders & Mobile Dispatch App.
- **Failure Behavior**: Re-route task to secondary vehicle if driver declines assignment.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Provide turn-by-turn route and destination point contact details.

---

### STAGE 13: EXECUTION STATUS `[VERIFIED]`
- **Stage Owner**: Dispatch Telemetry Service
- **Input**: Field mobile app status updates, GPS tracking telemetry.
- **Input Source**: Mobile App Webhook / GPS Telematics API.
- **Data Format**: JSON (`EN_ROUTE`, `DELIVERED`, `DELAYED`, `FAILED`).
- **Validation Rules**: Status state transitions must follow valid state machine graph.
- **Processing Step**: Update dispatch task status, record proof of delivery timestamp.
- **Output**: Real-time Delivery Status Record (`ExecutionStatus`).
- **Output Format**: JSON.
- **Persistence Mechanism**: Append-only audit log.
- **Storage Location**: PostgreSQL (`table: execution_status_logs`).
- **Consumer**: Reassessment Engine & Logistics Control Tower.
- **Failure Behavior**: Log connection timeout; store offline on mobile device until signal is restored.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Log GPS coordinates of delivery event.

---

### STAGE 14: FEEDBACK `[VERIFIED]`
- **Stage Owner**: Field Feedback Service
- **Input**: Post-distribution field surveys, survivor feedback, unmet need reports.
- **Input Source**: Field Worker App / SMS Survey Gateway.
- **Data Format**: JSON.
- **Validation Rules**: Match against original `TaskAssignment` ID.
- **Processing Step**: Ingest actual distribution quantities and residual emergency gap reports.
- **Output**: Structured Field Feedback Record (`FeedbackRecord`).
- **Output Format**: JSON.
- **Persistence Mechanism**: Relational DB.
- **Storage Location**: PostgreSQL (`table: feedback_records`).
- **Consumer**: Reassessment Engine & ML Retraining Pipeline.
- **Failure Behavior**: Store in feedback queue for review.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Link feedback directly to original prediction and allocation IDs.

---

### STAGE 15: REASSESSMENT `[VERIFIED]`
- **Stage Owner**: Continuous Reassessment Loop
- **Input**: `ExecutionStatus` + `FeedbackRecord` + New Incident Reports.
- **Input Source**: STAGE 13 + STAGE 14 + STAGE 3.
- **Data Format**: JSON.
- **Validation Rules**: Verify snapshot time delta > 1 Hour since last assessment.
- **Processing Step**: Re-evaluate residual severity score, update unmet need gaps, trigger new assessment cycle if severity remains \(\ge 2.0\).
- **Output**: Reassessment Trigger Event (`ReassessmentEvent`).
- **Output Format**: JSON.
- **Persistence Mechanism**: Event Bus.
- **Storage Location**: Event Stream (Kafka / RabbitMQ).
- **Consumer**: STAGE 5 (ML Assessment Engine).
- **Failure Behavior**: Continuous polling alert if reassessment fails to trigger after 24 hours.
- **Versioning Strategy**: v1.0.
- **Explainability Requirements**: Summarize change in severity and net reduction in humanitarian needs.
