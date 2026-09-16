import os
import json
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v2/severity_model.joblib"
METADATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v2/model_metadata.json"
EXAMPLE_EXPORT_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity_v2/example_explanations.json"

SEVERITY_LABELS = {
    0: "Low",
    1: "Moderate",
    2: "High",
    3: "Critical"
}

class SeverityV2Explainer:
    """
    Model Explainability Interface for Frozen Severity V2.
    Provides feature attribution, direction, rank, and structured explanations.
    """
    def __init__(self, model_path=MODEL_PATH, metadata_path=METADATA_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
            
        self.model = joblib.load(model_path)
        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)
            
        self.feature_list = self.metadata["feature_list"]
        self.supported_hazards = set(self.metadata["supported_hazards"])
        self.unsupported_hazards = set(self.metadata.get("unsupported_hazards", []))
        
        # Verify no target variable leakage in features
        forbidden_targets = {"severity_class", "deaths", "injured", "total_affected", "affected", "damage_usd_thousands", "observed_outcomes_y"}
        leak_check = forbidden_targets.intersection(set(self.feature_list))
        if leak_check:
            raise ValueError(f"Target leakage detected in feature list: {leak_check}")

    def explain_instance(self, input_features: dict, incident_id: str = "UNKNOWN", disaster_type: str = None) -> dict:
        """
        Generate structured explanation for a single prediction.
        """
        # Validate hazard support
        if disaster_type is not None and disaster_type not in self.supported_hazards:
            raise ValueError(
                f"Unsupported hazard '{disaster_type}'. Severity V2 only supports: {sorted(list(self.supported_hazards))}"
            )
            
        # Build feature vector matching training feature list exactly
        row_dict = {}
        for feat in self.feature_list:
            val = input_features.get(feat, np.nan)
            row_dict[feat] = val if val is not None else np.nan
            
        df_inst = pd.DataFrame([row_dict])[self.feature_list]
        
        # Predict class and probabilities
        pred_class = int(self.model.predict(df_inst)[0])
        probs = self.model.predict_proba(df_inst)[0]
        
        prob_dict = {SEVERITY_LABELS[i]: float(probs[i]) for i in range(len(probs))}
        
        # Compute tree-based marginal contributions relative to baseline median/mean
        contributions = self._compute_feature_contributions(df_inst, pred_class)
        
        # Rank features by magnitude of contribution
        sorted_contribs = sorted(contributions, key=lambda item: abs(item["contribution"]), reverse=True)
        
        ranked_features = []
        for rank, item in enumerate(sorted_contribs, start=1):
            contrib_val = float(item["contribution"])
            direction = "positive" if contrib_val >= 0 else "negative"
            feat_val = input_features.get(item["feature_name"])
            
            ranked_features.append({
                "rank": rank,
                "feature_name": item["feature_name"],
                "feature_value": float(feat_val) if feat_val is not None and not pd.isna(feat_val) else None,
                "contribution": round(contrib_val, 4),
                "direction": direction
            })
            
        return {
            "incident_id": incident_id,
            "disaster_type": disaster_type,
            "severity_class": pred_class,
            "severity_label": SEVERITY_LABELS[pred_class],
            "probabilities": prob_dict,
            "top_contributing_features": ranked_features
        }

    def _compute_feature_contributions(self, df_inst: pd.DataFrame, target_class: int) -> list:
        """
        Marginal feature perturbation attribution for HistGradientBoosting.
        Computes single-feature impact on the target class probability.
        """
        base_probs = self.model.predict_proba(df_inst)[0]
        target_base_prob = base_probs[target_class]
        
        contributions = []
        
        for feat in self.feature_list:
            df_perturbed = df_inst.copy()
            # Replace feature with NaN (missing feature drop impact)
            df_perturbed[feat] = np.nan
            
            p_perturbed = self.model.predict_proba(df_perturbed)[0]
            target_p_perturbed = p_perturbed[target_class]
            
            # Marginal contribution = base_prob - dropped_feature_prob
            contrib = target_base_prob - target_p_perturbed
            contributions.append({
                "feature_name": feat,
                "contribution": contrib
            })
            
        return contributions

def generate_example_artifacts():
    explainer = SeverityV2Explainer()
    
    # Sample earthquake instance
    eq_sample = {
        "disaster_type_code": 0,
        "seismic_magnitude": 7.8,
        "seismic_depth_km": 15.0,
        "cyclone_max_wind_knots": None,
        "cyclone_min_pressure_mb": None,
        "hazard_intensity_index": 7.8,
        "country_population": 17000000.0,
        "population_density_sqkm": 60.0,
        "log_population_exposure": 16.64
    }
    
    # Sample storm instance
    storm_sample = {
        "disaster_type_code": 1,
        "seismic_magnitude": None,
        "seismic_depth_km": None,
        "cyclone_max_wind_knots": 140.0,
        "cyclone_min_pressure_mb": 910.0,
        "hazard_intensity_index": 7.0,
        "country_population": 110000000.0,
        "population_density_sqkm": 368.0,
        "log_population_exposure": 18.51
    }
    
    ex1 = explainer.explain_instance(eq_sample, incident_id="INC-2025-EQ-TEST", disaster_type="Earthquake")
    ex2 = explainer.explain_instance(storm_sample, incident_id="INC-2025-STORM-TEST", disaster_type="Storm")
    
    examples = [ex1, ex2]
    
    os.makedirs(os.path.dirname(EXAMPLE_EXPORT_PATH), exist_ok=True)
    with open(EXAMPLE_EXPORT_PATH, "w") as f:
        json.dump(examples, f, indent=2)
        
    print(f"Generated example explanations successfully at {EXAMPLE_EXPORT_PATH}")
    return examples

if __name__ == "__main__":
    generate_example_artifacts()
