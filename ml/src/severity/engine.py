import logging
from typing import Dict, Any, Optional
from ml.src.models.severity_v2.predictor_v2 import SeverityPredictorV2
from ml.src.severity.schemas import SeverityAssessmentResult
from ml.src.severity.policies import FloodPolicyV1, WildfirePolicyV1, HeavyRainfallPolicyV1

logger = logging.getLogger(__name__)

# Class index to normalized 0-10 display score mapping for ML Severity V2
ML_DISPLAY_SCORE_MAP = {
    0: 1.25,  # Low (range 0.0 - 2.5)
    1: 3.75,  # Moderate (range 2.5 - 5.0)
    2: 6.25,  # High (range 5.0 - 7.5)
    3: 8.75   # Critical (range 7.5 - 10.0)
}

class UnifiedSeverityEngine:
    """
    Unified Hazard-Aware Severity Intelligence Engine.
    
    Routing Architecture:
    - EARTHQUAKE, CYCLONE, STORM -> Delegates to ML SeverityPredictorV2 (unmodified)
    - FLOOD -> FloodPolicyV1 (Deterministic Operational Heuristic)
    - WILDFIRE, FIRE -> WildfirePolicyV1 (Deterministic Operational Heuristic)
    - HEAVY RAINFALL, RAINFALL -> HeavyRainfallPolicyV1 (Deterministic Operational Heuristic)
    - UNKNOWN / Unsupported -> Returns status="unsupported_hazard"
    """
    def __init__(self, predictor_v2: Optional[SeverityPredictorV2] = None):
        if predictor_v2 is not None:
            self.predictor_v2 = predictor_v2
        else:
            try:
                self.predictor_v2 = SeverityPredictorV2()
            except Exception as e:
                logger.warning(f"Failed to load SeverityPredictorV2 artifacts: {e}")
                self.predictor_v2 = None

        self.flood_policy = FloodPolicyV1()
        self.wildfire_policy = WildfirePolicyV1()
        self.rainfall_policy = HeavyRainfallPolicyV1()

    def predict_severity(self, event_features: Dict[str, Any]) -> Dict[str, Any]:
        disaster_type = str(event_features.get("disaster_type", "")).strip().upper()

        # 1. Route ML-supported hazards (Earthquake, Cyclone, Storm)
        if disaster_type in ["EARTHQUAKE", "CYCLONE", "STORM"]:
            if not self.predictor_v2:
                return {
                    "status": "failed",
                    "hazard_type": disaster_type,
                    "reason": "SeverityPredictorV2 artifacts unavailable."
                }
            ml_event = dict(event_features)
            if disaster_type in ["CYCLONE", "STORM"]:
                ml_event["disaster_type"] = "Storm"

            ml_res = self.predictor_v2.predict_severity(ml_event)
            ml_res["hazard_type"] = event_features.get("disaster_type")
            if ml_res.get("status") == "success":
                class_idx = ml_res.get("severity_score", 0)
                display_score = ML_DISPLAY_SCORE_MAP.get(class_idx, float(class_idx))
                severity_label = str(ml_res.get("severity", "Low")).upper()
                
                # Enrich ML response with unified contract fields without altering original ML data
                ml_res["severity_class"] = severity_cls = severity_label if severity_label in ["LOW", "MODERATE", "HIGH", "CRITICAL"] else "LOW"
                ml_res["severity_score"] = display_score
                ml_res["raw_class_index"] = class_idx
                ml_res["assessment_method"] = "ML"
                ml_res["policy_version"] = None
                ml_res["evidence_coverage"] = {
                    "available_factors_count": len(ml_res.get("top_factors", [])),
                    "total_factors_count": len(ml_res.get("top_factors", [])),
                    "note": "ML model feature vector evaluated"
                }
                ml_res["explanation"] = f"SeverityPredictorV2 ML prediction: {severity_cls} (confidence {ml_res.get('confidence', 0.0)})."
            return ml_res

        # 2. Route Policy-supported hazards
        elif disaster_type in ["FLOOD", "FLOODING"]:
            policy_res = self.flood_policy.evaluate(event_features)
            return policy_res.model_dump()

        elif disaster_type in ["WILDFIRE", "FIRE", "BUSHFIRE"]:
            policy_res = self.wildfire_policy.evaluate(event_features)
            return policy_res.model_dump()

        elif disaster_type in ["HEAVY RAINFALL", "RAINFALL", "HEAVY_RAINFALL", "RAIN"]:
            policy_res = self.rainfall_policy.evaluate(event_features)
            return policy_res.model_dump()

        # 3. Unsupported hazards
        else:
            return {
                "status": "unsupported_hazard",
                "hazard_type": event_features.get("disaster_type"),
                "reason": f"Hazard '{disaster_type}' has no supported ML model or operational severity policy.",
                "assessment_method": "UNSUPPORTED",
                "model_version": None,
                "policy_version": None
            }
