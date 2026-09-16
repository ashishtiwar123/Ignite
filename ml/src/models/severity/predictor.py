import os
import json
import joblib
import numpy as np
import pandas as pd

MODEL_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v1/"

class SeverityPredictorV1:
    """
    Production Severity Intelligence Engine Predictor V1 Interface.
    Enforces schema validation, handles missing features, executes model,
    calculates confidence & probabilities, and handles unsupported hazards.
    """
    def __init__(self, model_dir=MODEL_DIR):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "severity_model.joblib")
        self.metadata_path = os.path.join(model_dir, "model_metadata.json")
        
        if not os.path.exists(self.model_path) or not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Severity V1 model artifacts not found at {model_dir}")
            
        self.model = joblib.load(self.model_path)
        with open(self.metadata_path, "r") as f:
            self.metadata = json.load(f)
            
        self.supported_hazards = [h.upper() for h in self.metadata.get("supported_hazards", [])]
        self.feature_list = self.metadata.get("feature_list", [])
        self.severity_map = {0: "Low", 1: "Moderate", 2: "High", 3: "Critical"}

    def predict_severity(self, event: dict) -> dict:
        disaster_type = str(event.get("disaster_type", "")).strip().upper()
        
        # Check unsupported hazard
        if disaster_type not in self.supported_hazards:
            return {
                "status": "unsupported_hazard",
                "hazard_type": event.get("disaster_type"),
                "reason": f"Hazard '{disaster_type}' is not supported by Severity Engine V1. Trained only on Earthquake and Storm/Cyclone.",
                "model_version": self.metadata.get("model_version", "severity_v1"),
                "supported_hazards": self.metadata.get("supported_hazards", [])
            }
            
        fx = event.get("predictor_features_x", {})
        
        mag = fx.get("seismic_magnitude") if fx.get("seismic_magnitude") is not None else np.nan
        depth = fx.get("seismic_depth_km") if fx.get("seismic_depth_km") is not None else np.nan
        wind = fx.get("cyclone_max_wind_knots") if fx.get("cyclone_max_wind_knots") is not None else np.nan
        press = fx.get("cyclone_min_pressure_mb") if fx.get("cyclone_min_pressure_mb") is not None else np.nan
        
        if disaster_type in ["STORM", "CYCLONE"]:
            hazard_intensity = (wind / 20.0) if pd.notna(wind) else 4.0
            disaster_code = 1
        else:
            hazard_intensity = mag if pd.notna(mag) else 5.0
            disaster_code = 0
            
        feat_df = pd.DataFrame([{
            "disaster_type_code": disaster_code,
            "seismic_magnitude": mag,
            "seismic_depth_km": depth,
            "cyclone_max_wind_knots": wind,
            "cyclone_min_pressure_mb": press,
            "hazard_intensity_index": hazard_intensity
        }])[self.feature_list]
        
        pred_class_idx = int(self.model.predict(feat_df)[0])
        probs = self.model.predict_proba(feat_df)[0]
        
        # Format probabilities dict
        prob_dict = {
            "low": round(float(probs[0]), 4) if len(probs) > 0 else 0.0,
            "moderate": round(float(probs[1]), 4) if len(probs) > 1 else 0.0,
            "high": round(float(probs[2]), 4) if len(probs) > 2 else 0.0,
            "critical": round(float(probs[3]), 4) if len(probs) > 3 else 0.0
        }
        
        confidence = round(float(np.max(probs)), 4)
        severity_label = self.severity_map.get(pred_class_idx, "Unknown")
        
        # Feature contributions / top factors
        top_factors = []
        if disaster_type in ["STORM", "CYCLONE"] and pd.notna(wind):
            top_factors.append({"feature": "cyclone_max_wind_knots", "value": wind, "direction": "increases_severity"})
        elif disaster_type == "EARTHQUAKE" and pd.notna(mag):
            top_factors.append({"feature": "seismic_magnitude", "value": mag, "direction": "increases_severity"})
            
        return {
            "status": "success",
            "prediction_id": f"PRED-{event.get('emdat_dis_no', 'LOCAL')}",
            "model_version": self.metadata.get("model_version", "severity_v1"),
            "incident_id": event.get("incident_id", "INC-UNKNOWN"),
            "hazard_type": disaster_type,
            "country": event.get("country", "Unknown"),
            "severity": severity_label,
            "severity_score": pred_class_idx,
            "confidence": confidence,
            "probabilities": prob_dict,
            "top_factors": top_factors,
            "data_quality": {
                "hazard_source": event.get("hazard_source", "VERIFIED_TELEMETRY"),
                "match_confidence": event.get("match_confidence", "HIGH")
            },
            "timestamp_utc": pd.Timestamp.now('UTC').isoformat()
        }

if __name__ == "__main__":
    predictor = SeverityPredictorV1()
    
    # Test Earthquake prediction
    test_eq = {
        "incident_id": "INC-TEST-EQ",
        "emdat_dis_no": "2023-0001",
        "disaster_type": "Earthquake",
        "country": "Turkey",
        "hazard_source": "USGS",
        "match_confidence": "HIGH",
        "predictor_features_x": {"seismic_magnitude": 7.8, "seismic_depth_km": 10.0}
    }
    res_eq = predictor.predict_severity(test_eq)
    print("\nPredictor Result (Earthquake):", json.dumps(res_eq, indent=2))
    
    # Test Unsupported Hazard
    test_flood = {
        "incident_id": "INC-TEST-FLD",
        "disaster_type": "Flood",
        "country": "Pakistan"
    }
    res_fl = predictor.predict_severity(test_flood)
    print("\nPredictor Result (Unsupported Flood):", json.dumps(res_fl, indent=2))
