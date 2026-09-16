import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, brier_score_loss
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from xgboost import XGBClassifier
import joblib

DATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
MODEL_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/models/severity_v1/"
REPORTS_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/severity/"

def prepare_dataset():
    df = pd.read_parquet(DATA_PATH)
    
    X_rows = []
    Y_rows = []
    
    for _, row in df.iterrows():
        fx = row['predictor_features_x']
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
            
        X_rows.append({
            "disaster_type_code": 1 if row['disaster_type'] == 'Storm' else 0,
            "seismic_magnitude": mag,
            "seismic_depth_km": depth,
            "cyclone_max_wind_knots": wind,
            "cyclone_min_pressure_mb": press,
            "hazard_intensity_index": hazard_intensity
        })
        
        Y_rows.append({
            "incident_id": row['incident_id'],
            "hazard_type": row['disaster_type'],
            "country": row['country'],
            "impact_score": impact_score,
            "severity_class": sev_class
        })
        
    df_x = pd.DataFrame(X_rows)
    df_y = pd.DataFrame(Y_rows)
    return df, df_x, df_y

def train_and_evaluate():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    df_orig, df_x, df_y = prepare_dataset()
    print(f"Loaded dataset: {len(df_x)} rows.")
    print("Severity Class Distribution:")
    print(df_y['severity_class'].value_counts().sort_index())
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    candidates = {
        "XGBoost_Classifier": XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42, eval_metric="mlogloss"),
        "RandomForest_Classifier": RandomForestClassifier(n_estimators=50, max_depth=3, random_state=42),
        "ExtraTrees_Classifier": ExtraTreesClassifier(n_estimators=50, max_depth=3, random_state=42),
        "HistGradientBoosting_Classifier": HistGradientBoostingClassifier(max_iter=50, max_depth=3, random_state=42)
    }
    
    results = []
    best_model_name = None
    best_macro_f1 = -1.0
    best_fitted_model = None
    best_oof_preds = None
    best_oof_probs = None
    
    for name, model_obj in candidates.items():
        oof_preds = np.zeros(len(df_y))
        oof_probs = np.zeros((len(df_y), 4))
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(df_x, df_y['severity_class'])):
            X_tr, y_tr = df_x.iloc[train_idx], df_y['severity_class'].iloc[train_idx]
            X_va, y_va = df_x.iloc[val_idx], df_y['severity_class'].iloc[val_idx]
            
            m = model_obj
            m.fit(X_tr, y_tr)
            
            preds = m.predict(X_va)
            probs = m.predict_proba(X_va)
            
            oof_preds[val_idx] = preds
            for i, c in enumerate(m.classes_):
                oof_probs[val_idx, c] = probs[:, i]
                
        acc = accuracy_score(df_y['severity_class'], oof_preds)
        macro_f1 = f1_score(df_y['severity_class'], oof_preds, average='macro')
        weighted_f1 = f1_score(df_y['severity_class'], oof_preds, average='weighted')
        
        print(f"Model: {name:<35} | Macro F1: {macro_f1:.4f} | Weighted F1: {weighted_f1:.4f} | Acc: {acc:.4f}")
        
        results.append({
            "model_name": name,
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "accuracy": round(acc, 4)
        })
        
        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_model_name = name
            best_fitted_model = model_obj.fit(df_x, df_y['severity_class'])
            best_oof_preds = oof_preds
            best_oof_probs = oof_probs
            
    pd.DataFrame(results).to_csv(os.path.join(REPORTS_DIR, "model_comparison.csv"), index=False)
    
    # Save predictions
    df_preds = df_y.copy()
    df_preds['predicted_class'] = best_oof_preds
    df_preds['prob_low'] = best_oof_probs[:, 0]
    df_preds['prob_moderate'] = best_oof_probs[:, 1]
    df_preds['prob_high'] = best_oof_probs[:, 2]
    df_preds['prob_critical'] = best_oof_probs[:, 3]
    df_preds.to_csv(os.path.join(REPORTS_DIR, "test_predictions.csv"), index=False)
    
    # Save feature importances if supported
    if hasattr(best_fitted_model, 'feature_importances_'):
        df_fi = pd.DataFrame({
            "feature": df_x.columns,
            "importance": best_fitted_model.feature_importances_
        }).sort_values(by="importance", ascending=False)
        df_fi.to_csv(os.path.join(REPORTS_DIR, "feature_importance.csv"), index=False)
        
    joblib.dump(best_fitted_model, os.path.join(MODEL_DIR, "severity_model.joblib"))
    
    meta = {
        "model_version": "severity_v1",
        "training_dataset_version": "v4.0-verified-matches",
        "selected_model": best_model_name,
        "primary_metric": "macro_f1",
        "primary_metric_value": round(best_macro_f1, 4),
        "supported_hazards": ["Earthquake", "Storm"],
        "unsupported_hazards": ["Flood", "Wildfire", "Landslide", "Drought", "Epidemic", "Extreme temperature"],
        "feature_list": list(df_x.columns),
        "target_definition": "Ordinal Severity Class (0: Low, 1: Moderate, 2: High, 3: Critical) derived from Impact Score Y",
        "sample_count": len(df_x),
        "training_timestamp_utc": pd.Timestamp.now('UTC').isoformat()
    }
    
    with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)
        
    print(f"\nSelected Model: {best_model_name} with Macro F1: {best_macro_f1:.4f}")
    print("Saved severity_model.joblib and model_metadata.json successfully.")

if __name__ == "__main__":
    train_and_evaluate()
