# Ignite Component Data Schemas & Data Contracts

**Project**: Ignite (PS20)  
**Document**: `docs/schemas/COMPONENT_DATA_SCHEMAS.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED & FROZEN DATA CONTRACTS  
**Last Updated**: 2026-09-16  

---

## 1. Overview
This directory defines the conceptual data contracts and JSON/Pydantic schemas governing inter-component communication in Project Ignite. Every field includes explicit type signatures, validation constraints, and rationale.

---

## 2. Core Entity Schema Definitions

### 2.1 RawReport Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RawReport",
  "type": "object",
  "properties": {
    "raw_report_id": { "type": "string", "format": "uuid", "description": "Unique envelope identifier" },
    "source_type": { "type": "string", "enum": ["SMS", "WEBHOOK", "HOTLINE", "RSS", "FIELD_APP"], "description": "Channel origin" },
    "payload_text": { "type": "string", "minLength": 1, "description": "Unmodified text content" },
    "received_at_utc": { "type": "string", "format": "date-time", "description": "Ingestion timestamp" },
    "sender_metadata": { "type": "object", "description": "Non-PII origin metadata" }
  },
  "required": ["raw_report_id", "source_type", "payload_text", "received_at_utc"]
}
```

### 2.2 StructuredReport Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StructuredReport",
  "type": "object",
  "properties": {
    "structured_report_id": { "type": "string", "format": "uuid" },
    "raw_report_id": { "type": "string", "format": "uuid" },
    "hazard_category": { "type": "string", "enum": ["FLOOD", "EARTHQUAKE", "CYCLONE", "WILDFIRE", "LANDSLIDE", "DROUGHT", "EXTREME_WEATHER", "CONFLICT"] },
    "location_name": { "type": "string", "description": "Extracted location text" },
    "estimated_affected_count": { "type": "integer", "minimum": 0 },
    "reported_fatalities": { "type": "integer", "minimum": 0 },
    "urgency_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "parsed_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["structured_report_id", "raw_report_id", "hazard_category", "parsed_at_utc"]
}
```

### 2.3 VerifiedIncident Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "VerifiedIncident",
  "type": "object",
  "properties": {
    "incident_id": { "type": "string", "format": "uuid" },
    "hazard_category": { "type": "string" },
    "latitude": { "type": "number", "minimum": -90.0, "maximum": 90.0 },
    "longitude": { "type": "number", "minimum": -180.0, "maximum": 180.0 },
    "adm2_pcode": { "type": "string", "pattern": "^[A-Z]{3}[0-9]{6}$", "description": "Standard OCHA ADM2 P-code" },
    "h3_index": { "type": "string", "description": "Uber H3 resolution 8 index" },
    "verification_confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "verified_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["incident_id", "hazard_category", "latitude", "longitude", "adm2_pcode", "verification_confidence"]
}
```

### 2.4 SeverityAssessment Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SeverityAssessment",
  "type": "object",
  "properties": {
    "assessment_id": { "type": "string", "format": "uuid" },
    "adm2_pcode": { "type": "string" },
    "disi_score": { "type": "number", "minimum": 0.0, "maximum": 5.0, "description": "Derived Impact Severity Score" },
    "severity_class": { "type": "integer", "minimum": 0, "maximum": 5 },
    "confidence_interval": { "type": "array", "items": { "type": "number" }, "minItems": 2, "maxItems": 2 },
    "model_version": { "type": "string" },
    "assessed_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["assessment_id", "adm2_pcode", "disi_score", "severity_class", "model_version"]
}
```

### 2.5 RiskAssessment Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RiskAssessment",
  "type": "object",
  "properties": {
    "risk_assessment_id": { "type": "string", "format": "uuid" },
    "adm2_pcode": { "type": "string" },
    "forecast_horizon_months": { "type": "integer", "enum": [1, 3, 6] },
    "trajectory_class": { "type": "integer", "enum": [-1, 0, 1, 2], "description": "-1 De-escalation, 0 Stable, 1 Moderate, 2 Rapid Escalation" },
    "escalation_probability": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "assessed_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["risk_assessment_id", "adm2_pcode", "forecast_horizon_months", "trajectory_class"]
}
```

### 2.6 ExposureAssessment Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ExposureAssessment",
  "type": "object",
  "properties": {
    "exposure_id": { "type": "string", "format": "uuid" },
    "adm2_pcode": { "type": "string" },
    "total_population_at_risk": { "type": "integer", "minimum": 0 },
    "vulnerable_population_count": { "type": "integer", "minimum": 0 },
    "exposed_infrastructure_units": { "type": "integer", "minimum": 0 }
  },
  "required": ["exposure_id", "adm2_pcode", "total_population_at_risk"]
}
```

### 2.7 NeedsAssessment Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NeedsAssessment",
  "type": "object",
  "properties": {
    "needs_id": { "type": "string", "format": "uuid" },
    "adm2_pcode": { "type": "string" },
    "water_required_liters_per_day": { "type": "number", "minimum": 0.0 },
    "food_kcals_required_per_day": { "type": "number", "minimum": 0.0 },
    "shelter_sqm_required": { "type": "number", "minimum": 0.0 },
    "hygiene_kits_required": { "type": "integer", "minimum": 0 },
    "calculation_basis": { "type": "string", "default": "Sphere Standards 2018" }
  },
  "required": ["needs_id", "adm2_pcode", "water_required_liters_per_day", "food_kcals_required_per_day", "shelter_sqm_required"]
}
```

### 2.8 ResourceRequirement Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ResourceRequirement",
  "type": "object",
  "properties": {
    "requirement_id": { "type": "string", "format": "uuid" },
    "adm2_pcode": { "type": "string" },
    "item_sku": { "type": "string" },
    "item_name": { "type": "string" },
    "required_quantity": { "type": "number", "minimum": 0.0 },
    "unit_of_measure": { "type": "string", "enum": ["METRIC_TONS", "LITERS", "KITS", "UNITS"] }
  },
  "required": ["requirement_id", "adm2_pcode", "item_sku", "required_quantity", "unit_of_measure"]
}
```

### 2.9 InventoryState Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "InventoryState",
  "type": "object",
  "properties": {
    "facility_id": { "type": "string" },
    "facility_name": { "type": "string" },
    "latitude": { "type": "number" },
    "longitude": { "type": "number" },
    "stock_levels": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "item_sku": { "type": "string" },
          "available_quantity": { "type": "number", "minimum": 0.0 }
        },
        "required": ["item_sku", "available_quantity"]
      }
    },
    "last_audited_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["facility_id", "facility_name", "stock_levels"]
}
```

### 2.10 AllocationPlan Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AllocationPlan",
  "type": "object",
  "properties": {
    "plan_id": { "type": "string", "format": "uuid" },
    "solver_status": { "type": "string", "enum": ["OPTIMAL", "FEASIBLE", "INFEASIBLE"] },
    "allocations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "source_facility_id": { "type": "string" },
          "target_adm2_pcode": { "type": "string" },
          "item_sku": { "type": "string" },
          "allocated_quantity": { "type": "number" },
          "transport_mode": { "type": "string" }
        },
        "required": ["source_facility_id", "target_adm2_pcode", "item_sku", "allocated_quantity"]
      }
    },
    "created_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["plan_id", "solver_status", "allocations"]
}
```

### 2.11 ExecutionStatus Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ExecutionStatus",
  "type": "object",
  "properties": {
    "task_id": { "type": "string", "format": "uuid" },
    "status": { "type": "string", "enum": ["ASSIGNED", "EN_ROUTE", "DELIVERED", "PARTIAL_DELIVERY", "FAILED"] },
    "delivered_quantity": { "type": "number", "minimum": 0.0 },
    "updated_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["task_id", "status", "updated_at_utc"]
}
```

### 2.12 ReassessmentEvent Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReassessmentEvent",
  "type": "object",
  "properties": {
    "reassessment_id": { "type": "string", "format": "uuid" },
    "adm2_pcode": { "type": "string" },
    "previous_disi_score": { "type": "number" },
    "new_disi_score": { "type": "number" },
    "reassessment_reason": { "type": "string" },
    "triggered_at_utc": { "type": "string", "format": "date-time" }
  },
  "required": ["reassessment_id", "adm2_pcode", "previous_disi_score", "new_disi_score"]
}
```

### 2.13 UnifiedIntelligenceOutput Schema `[VERIFIED]`
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UnifiedIntelligenceOutput",
  "type": "object",
  "properties": {
    "snapshot_id": { "type": "string", "format": "uuid" },
    "timestamp_utc": { "type": "string", "format": "date-time" },
    "severity_assessments": { "type": "array", "items": { "$ref": "#/definitions/SeverityAssessment" } },
    "risk_assessments": { "type": "array", "items": { "$ref": "#/definitions/RiskAssessment" } },
    "needs_assessments": { "type": "array", "items": { "$ref": "#/definitions/NeedsAssessment" } }
  },
  "required": ["snapshot_id", "timestamp_utc", "severity_assessments"]
}
```
