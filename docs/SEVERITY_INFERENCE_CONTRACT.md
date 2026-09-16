# Severity Engine V1 — Inference API Contract Specification
**Project**: Ignite (PS20)  
**Document**: `docs/SEVERITY_INFERENCE_CONTRACT.md`  
**Date**: 2026-09-16  

---

## 1. Python Interface Signature

```python
from ml.src.models.severity.predictor import SeverityPredictorV1

predictor = SeverityPredictorV1()
response = predictor.predict_severity(event_dict)
```

---

## 2. Response Schema (Success)

```json
{
  "status": "success",
  "prediction_id": "PRED-2023-0001",
  "model_version": "severity_v1",
  "incident_id": "INC-TEST-EQ",
  "hazard_type": "EARTHQUAKE",
  "country": "Turkey",
  "severity": "Critical",
  "severity_score": 3,
  "confidence": 0.8111,
  "probabilities": {
    "low": 0.0441,
    "moderate": 0.1432,
    "high": 0.0017,
    "critical": 0.8111
  },
  "top_factors": [
    {
      "feature": "seismic_magnitude",
      "value": 7.8,
      "direction": "increases_severity"
    }
  ],
  "data_quality": {
    "hazard_source": "USGS",
    "match_confidence": "HIGH"
  },
  "timestamp_utc": "2026-09-16T08:32:58.977813+00:00"
}
```

---

## 3. Response Schema (Unsupported Hazard)

```json
{
  "status": "unsupported_hazard",
  "hazard_type": "Flood",
  "reason": "Hazard 'FLOOD' is not supported by Severity Engine V1. Trained only on Earthquake and Storm/Cyclone.",
  "model_version": "severity_v1",
  "supported_hazards": ["Earthquake", "Storm"]
}
```
