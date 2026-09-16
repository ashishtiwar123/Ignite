# ML Service to FastAPI Backend Data & Service Contract

**Project**: Ignite (PS20)  
**Document**: `docs/ML_FASTAPI_CONTRACT.md`  
**Phase**: Phase 1.5 Architecture Freeze  
**Status**: APPROVED & FROZEN CONTRACT SPECIFICATION  
**Last Updated**: 2026-09-16  

---

## 1. Architectural Overview & System Flow

This document defines the service integration contract between the **FastAPI Backend Service** and the **ML Intelligence Microservice (`:8001`)**.

```
┌─────────────────┐             POST /api/v1/predict/severity            ┌─────────────────┐
│                 │ ───────────────────────────────────────────────────► │                 │
│ FastAPI Backend │                                                      │ ML Service      │
│ (Port 8000)     │ ◄─────────────────────────────────────────────────── │ (Port 8001)     │
└─────────────────┘             200 OK (Structured Prediction JSON)      └─────────────────┘
```

---

## 2. API Endpoint Specifications

### Endpoint: `POST /api/v1/predict/intelligence`

#### Request Headers:
- `Content-Type`: `application/json`
- `X-Correlation-ID`: `string` (UUID v4 for request tracing)

#### Request Payload Schema:
```json
{
  "adm2_pcode": "SDN001002",
  "prediction_timestamp_utc": "2026-09-16T00:00:00Z",
  "requested_horizons_months": [1, 3, 6],
  "feature_overrides": {
    "recent_precip_mm": 150.5
  },
  "include_explanation": true
}
```

#### Response Payload Schema (200 OK):
```json
{
  "request_id": "8e8e29e6-4823-4d03-9809-4006b998c1c9",
  "adm2_pcode": "SDN001002",
  "model_metadata": {
    "model_version": "v1.2.0-xgboost-disi",
    "trained_at_utc": "2026-09-01T12:00:00Z",
    "feature_schema_version": "v1.0"
  },
  "data_quality_indicators": {
    "data_completeness_ratio": 0.98,
    "source_staleness_days": {
      "hydromet": 0.5,
      "acled": 8.0,
      "ipc": 45.0
    },
    "imputed_features_count": 1
  },
  "severity_prediction": {
    "disi_score": 3.42,
    "severity_class": 3,
    "class_label": "Severe Disaster",
    "confidence": {
      "point_estimate": 3.42,
      "lower_bound_95": 3.10,
      "upper_bound_95": 3.75,
      "prediction_std_dev": 0.165
    }
  },
  "risk_trajectory_predictions": [
    {
      "horizon_months": 1,
      "trajectory_class": 1,
      "class_label": "Moderate Escalation",
      "escalation_probability": 0.74
    },
    {
      "horizon_months": 3,
      "trajectory_class": 2,
      "class_label": "Rapid Escalation",
      "escalation_probability": 0.88
    },
    {
      "horizon_months": 6,
      "trajectory_class": 1,
      "class_label": "Moderate Escalation",
      "escalation_probability": 0.62
    }
  ],
  "explanation": {
    "shap_top_drivers": [
      { "feature": "precip_accum_7d", "shap_value": +0.85, "description": "7-day accumulated rainfall spike" },
      { "feature": "fatalities_sum_3m", "shap_value": +0.42, "description": "Rolling 3-month conflict mortality baseline" },
      { "feature": "ipc_phase", "shap_value": +0.30, "description": "Contextual food insecurity score" }
    ]
  },
  "processed_at_utc": "2026-09-16T12:00:01.245Z",
  "latency_ms": 142.5
}
```

---

## 3. Error Handling & Validation Failures

### 3.1 Validation Error (422 Unprocessable Entity)
Returned when input payload fails schema verification (e.g. invalid `ADM2_PCODE` format):
```json
{
  "error_code": "INVALID_PCODE_FORMAT",
  "message": "String 'INVALID_PCODE' does not match required regex pattern ^[A-Z]{3}[0-9]{6}$",
  "field": "adm2_pcode",
  "timestamp_utc": "2026-09-16T12:00:01Z"
}
```

### 3.2 Service Unavailable & Fallback Behavior (503 / Timeout)
- **Timeout Standard**: FastAPI backend enforces a **2000ms hard timeout** on calls to ML Service.
- **Fallback Strategy**: If ML Service times out or returns 503, FastAPI backend falls back to deterministic rule-based severity scoring and returns a `fallback_mode: true` payload flag.
