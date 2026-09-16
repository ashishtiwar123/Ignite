import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, brier_score_loss, confusion_matrix
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, ExtraTreesClassifier
from xgboost import XGBClassifier
import joblib

DATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v5/event_level_features.parquet"
MODEL_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v2/"
REPORTS_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity_v2/"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def prepare_dataset():
    df = pd.read_parquet(DATA_PATH)
    
    Y_class = []
    for _, row in df.iterrows():
        y = row['observed_outcomes_y']
        deaths = y.get('deaths') if pd.notna(y.get('deaths')) else 0.0
        injured = y.get('injured') if pd.notna(y.get('injured')) else 0.0
        affected = y.get('total_affected') if pd.notna(y.get('total_affected')) else (y.get('affected') if pd.notna(y.get('affected')) else 0.0)
        damage = y.get('damage_usd_thousands') if pd.notna(y.get('damage_usd_thousands')) else 0.0
        
        impact_score = np.log1p(deaths) + 0.5 * np.log1p(injured) + 0.1 * np.log1p(affected) + 0.2 * np.log1p(damage)
        
        if impact_score < 3.0:
            sev_class = 0
        elif impact_score < 7.0:
            sev_class = 1
        elif impact_score < 11.0:
            sev_class = 2
        else:
            sev_class = 3
        Y_class.append(sev_class)
        
    df['severity_class'] = Y_class
    return df

def run_ablation_experiments():
    df = prepare_dataset()
    print(f"Loaded V5 dataset: {len(df)} rows.")
    
    # Define Feature Sets
    v1_hazard_cols = [
        "disaster_type_code", "seismic_magnitude", "seismic_depth_km",
        "cyclone_max_wind_knots", "cyclone_min_pressure_mb", "hazard_intensity_index"
    ]
    
    v2_exposure_cols = v1_hazard_cols + [
        "country_population", "population_density_sqkm", "log_population_exposure"
    ]
    
    v2_exposure_context_cols = v2_exposure_cols + [
        "urban_population_pct", "hazard_x_exposure_interaction"
    ]
    
    v2_full_cols = v2_exposure_context_cols + [
        "poverty_headcount_pct"
    ]
    
    feature_sets = {
        "Model A (V1 Hazard Only)": v1_hazard_cols,
        "Model B (V1 + Exposure)": v2_exposure_cols,
        "Model C (V1 + Exposure + Context)": v2_exposure_context_cols,
        "Model D (V1 + Exposure + Context + Vulnerability)": v2_full_cols
    }
    
    # Build dataframe of features
    X_rows = []
    for _, row in df.iterrows():
        fx = row['predictor_features_x']
        mag = fx.get('seismic_magnitude') if fx.get('seismic_magnitude') is not None else np.nan
        depth = fx.get('seismic_depth_km') if fx.get('seismic_depth_km') is not None else np.nan
        wind = fx.get('cyclone_max_wind_knots') if fx.get('cyclone_max_wind_knots') is not None else np.nan
        press = fx.get('cyclone_min_pressure_mb') if fx.get('cyclone_min_pressure_mb') is not None else np.nan
        
        if row['disaster_type'] == 'Earthquake':
            hazard_intensity = mag if pd.notna(mag) else 5.0
        elif row['disaster_type'] == 'Storm':
            hazard_intensity = (wind / 20.0) if pd.notna(wind) else 4.0
        else:
            hazard_intensity = 0.0
            
        pop = fx.get('country_population') if fx.get('country_population') is not None else np.nan
        den = fx.get('population_density_sqkm') if fx.get('population_density_sqkm') is not None else np.nan
        log_pop = fx.get('log_population_exposure') if fx.get('log_population_exposure') is not None else np.nan
        urb = fx.get('urban_population_pct') if fx.get('urban_population_pct') is not None else np.nan
        pov = fx.get('poverty_headcount_pct') if fx.get('poverty_headcount_pct') is not None else np.nan
        inter = (hazard_intensity * np.log1p(den)) if pd.notna(den) else np.nan
        
        X_rows.append({
            "disaster_type_code": 1 if row['disaster_type'] == 'Storm' else 0,
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
        })
        
    df_x_all = pd.DataFrame(X_rows)
    df_y = df['severity_class']
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    ablation_results = []
    
    best_overall_macro_f1 = -1.0
    best_config_name = None
    best_fitted_model = None
    best_oof_preds = None
    best_oof_probs = None
    
    print("\n--- ABLATION EXPERIMENTS RESULTS (HistGradientBoosting) ---")
    
    for set_name, cols in feature_sets.items():
        df_x = df_x_all[cols]
        
        oof_preds = np.zeros(len(df_y))
        oof_probs = np.zeros((len(df_y), 4))
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(df_x, df_y)):
            X_tr, y_tr = df_x.iloc[train_idx], df_y.iloc[train_idx]
            X_va, y_va = df_x.iloc[val_idx], df_y.iloc[val_idx]
            
            m = HistGradientBoostingClassifier(max_iter=50, max_depth=3, random_state=42)
            m.fit(X_tr, y_tr)
            
            preds = m.predict(X_va)
            probs = m.predict_proba(X_va)
            
            oof_preds[val_idx] = preds
            for i, c in enumerate(m.classes_):
                oof_probs[val_idx, c] = probs[:, i]
                
        acc = accuracy_score(df_y, oof_preds)
        macro_f1 = f1_score(df_y, oof_preds, average='macro')
        weighted_f1 = f1_score(df_y, oof_preds, average='weighted')
        
        cm = confusion_matrix(df_y, oof_preds, labels=[0, 1, 2, 3])
        # Recall for High (2) and Critical (3)
        high_recall = cm[2, 2] / sum(cm[2, :]) if sum(cm[2, :]) > 0 else 0.0
        critical_recall = cm[3, 3] / sum(cm[3, :]) if sum(cm[3, :]) > 0 else 0.0
        
        print(f"Set: {set_name:<50} | Macro F1: {macro_f1:.4f} | Weighted F1: {weighted_f1:.4f} | Acc: {acc:.4f} | High Rec: {high_recall:.4f} | Crit Rec: {critical_recall:.4f}")
        
        ablation_results.append({
            "feature_set": set_name,
            "feature_count": len(cols),
            "rows": len(df_y),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "accuracy": round(acc, 4),
            "high_recall": round(high_recall, 4),
            "critical_recall": round(critical_recall, 4)
        })
        
        if macro_f1 > best_overall_macro_f1:
            best_overall_macro_f1 = macro_f1
            best_config_name = set_name
            best_fitted_model = HistGradientBoostingClassifier(max_iter=50, max_depth=3, random_state=42).fit(df_x, df_y)
            best_oof_preds = oof_preds
            best_oof_probs = oof_probs
            best_feature_list = cols
            
    pd.DataFrame(ablation_results).to_csv(os.path.join(REPORTS_DIR, "v2_ablation_results.csv"), index=False)
    
    # Export predictions & error analysis
    df_preds = df[['incident_id', 'disaster_type', 'country', 'severity_class']].copy()
    df_preds['predicted_class'] = best_oof_preds
    df_preds['prob_low'] = best_oof_probs[:, 0]
    df_preds['prob_moderate'] = best_oof_probs[:, 1]
    df_preds['prob_high'] = best_oof_probs[:, 2]
    df_preds['prob_critical'] = best_oof_probs[:, 3]
    df_preds.to_csv(os.path.join(REPORTS_DIR, "v2_test_predictions.csv"), index=False)
    
    # Save V2 Model Artifacts
    joblib.dump(best_fitted_model, os.path.join(MODEL_DIR, "severity_model.joblib"))
    
    meta = {
        "model_version": "severity_v2",
        "training_dataset_version": "v5.0-exposure-enriched",
        "selected_model": "HistGradientBoosting_Classifier",
        "selected_feature_config": best_config_name,
        "primary_metric": "macro_f1",
        "primary_metric_value": round(best_overall_macro_f1, 4),
        "supported_hazards": ["Earthquake", "Storm"],
        "unsupported_hazards": ["Flood", "Wildfire", "Landslide", "Drought", "Epidemic", "Extreme temperature"],
        "feature_list": best_feature_list,
        "sample_count": len(df_y),
        "training_timestamp_utc": pd.Timestamp.now('UTC').isoformat()
    }
    
    with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)
        
    print(f"\nBest Ablation Config: {best_config_name} with Macro F1: {best_overall_macro_f1:.4f}")
    print("Saved severity_v2 artifacts successfully.")

if __name__ == "__main__":
    run_ablation_experiments()
