import os
import json
import joblib
import numpy as np
import pandas as pd

MODEL_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v2/"

class SeverityPredictorV2:
    """
    Production Severity Intelligence Engine Predictor V2 Interface.
    Enforces schema validation for exposure-enriched features, handles missing features,
    executes model, calculates confidence & probabilities, and handles unsupported hazards.
    """
    def __init__(self, model_dir=MODEL_DIR):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "severity_model.joblib")
        self.metadata_path = os.path.join(model_dir, "model_metadata.json")
        
        if not os.path.exists(self.model_path) or not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Severity V2 model artifacts not found at {model_dir}")
            
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
                "reason": f"Hazard '{disaster_type}' is not supported by Severity Engine V2. Trained only on Earthquake and Storm/Cyclone.",
                "model_version": self.metadata.get("model_version", "severity_v2"),
                "supported_hazards": self.metadata.get("supported_hazards", [])
            }
            
        fx = event.get("predictor_features_x", {})
        
        mag = fx.get("seismic_magnitude") if fx.get("seismic_magnitude") is not None else np.nan
        depth = fx.get("seismic_depth_km") if fx.get("seismic_depth_km") is not None else np.nan
        wind = fx.get("cyclone_max_wind_knots") if fx.get("cyclone_max_wind_knots") is not None else np.nan
        press = fx.get("cyclone_min_pressure_mb") if fx.get("cyclone_min_pressure_mb") is not None else np.nan
        
        pop = fx.get("country_population") if fx.get("country_population") is not None else np.nan
        den = fx.get("population_density_sqkm") if fx.get("population_density_sqkm") is not None else np.nan
        log_pop = fx.get("log_population_exposure") if fx.get("log_population_exposure") is not None else (np.log1p(pop) if pd.notna(pop) else np.nan)
        urb = fx.get("urban_population_pct") if fx.get("urban_population_pct") is not None else np.nan
        pov = fx.get("poverty_headcount_pct") if fx.get("poverty_headcount_pct") is not None else np.nan
        
        if disaster_type in ["STORM", "CYCLONE"]:
            hazard_intensity = (wind / 20.0) if pd.notna(wind) else 4.0
            disaster_code = 1
        else:
            hazard_intensity = mag if pd.notna(mag) else 5.0
            disaster_code = 0
            
        inter = (hazard_intensity * np.log1p(den)) if pd.notna(den) else np.nan
        
        row_dict = {
            "disaster_type_code": disaster_code,
            "seismic_magnitude": mag,
            "seismic_depth_km": depth,
            "cyclone_max_wind_knots": wind,
            "cyclone_min_pressure_mb": press,
            "hazard_intensity_index": hazard_intensity,
            "country_population": pop,
            "population_density_sqkm": den,
            "log_population_exposure": log_pop,
            "urban_population_pct": urb,
            "hazard_x_exposure_interaction": inter,
            "poverty_headcount_pct": pov
        }
        
        # Filter down to exact model feature_list
        feat_df = pd.DataFrame([row_dict])[self.feature_list]
        
        pred_class_idx = int(self.model.predict(feat_df)[0])
        probs = self.model.predict_proba(feat_df)[0]
        
        prob_dict = {
            "low": round(float(probs[0]), 4) if len(probs) > 0 else 0.0,
            "moderate": round(float(probs[1]), 4) if len(probs) > 1 else 0.0,
            "high": round(float(probs[2]), 4) if len(probs) > 2 else 0.0,
            "critical": round(float(probs[3]), 4) if len(probs) > 3 else 0.0
        }
        
        confidence = round(float(np.max(probs)), 4)
        severity_label = self.severity_map.get(pred_class_idx, "Unknown")
        
        top_factors = []
        if disaster_type in ["STORM", "CYCLONE"] and pd.notna(wind):
            top_factors.append({"feature": "cyclone_max_wind_knots", "value": wind, "direction": "increases_severity"})
        elif disaster_type == "EARTHQUAKE" and pd.notna(mag):
            top_factors.append({"feature": "seismic_magnitude", "value": mag, "direction": "increases_severity"})
        if pd.notna(den):
            top_factors.append({"feature": "population_density_sqkm", "value": den, "direction": "increases_exposure"})
            
        return {
            "status": "success",
            "prediction_id": f"PRED-{event.get('emdat_dis_no', 'LOCAL')}",
            "model_version": self.metadata.get("model_version", "severity_v2"),
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
                "exposure_source": "WorldBank_2000_2025",
                "match_confidence": event.get("match_confidence", "HIGH")
            },
            "timestamp_utc": pd.Timestamp.now('UTC').isoformat()
        }

if __name__ == "__main__":
    predictor = SeverityPredictorV2()
    test_eq = {
        "incident_id": "INC-TEST-EQ-V2",
        "emdat_dis_no": "2023-0001",
        "disaster_type": "Earthquake",
        "country": "Turkey",
        "hazard_source": "USGS",
        "match_confidence": "HIGH",
        "predictor_features_x": {
            "seismic_magnitude": 7.8,
            "seismic_depth_km": 10.0,
            "country_population": 85000000.0,
            "population_density_sqkm": 110.0
        }
    }
    res = predictor.predict_severity(test_eq)
    print("\nSeverity Predictor V2 Output:", json.dumps(res, indent=2))
