import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

DATA_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
df = pd.read_parquet(DATA_PATH)

X_rows = []
for _, row in df.iterrows():
    fx = row['predictor_features_x']
    y = row['observed_outcomes_y']
    
    deaths = y.get('deaths') if pd.notna(y.get('deaths')) else 0.0
    injured = y.get('injured') if pd.notna(y.get('injured')) else 0.0
    affected = y.get('total_affected') if pd.notna(y.get('total_affected')) else (y.get('affected') if pd.notna(y.get('affected')) else 0.0)
    damage = y.get('damage_usd_thousands') if pd.notna(y.get('damage_usd_thousands')) else 0.0
    
    impact_score = np.log1p(deaths) + 0.5 * np.log1p(injured) + 0.1 * np.log1p(affected) + 0.2 * np.log1p(damage)
    
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
        "disaster_type": row['disaster_type'],
        "disaster_type_code": 1 if row['disaster_type'] == 'Storm' else 0,
        "seismic_magnitude": mag,
        "seismic_depth_km": depth,
        "cyclone_max_wind_knots": wind,
        "cyclone_min_pressure_mb": press,
        "hazard_intensity_index": hazard_intensity,
        "impact_score": impact_score
    })

df_feat = pd.DataFrame(X_rows)

analysis_rows = []
for col in ["disaster_type_code", "seismic_magnitude", "seismic_depth_km", "cyclone_max_wind_knots", "cyclone_min_pressure_mb", "hazard_intensity_index"]:
    ser = df_feat[[col, "impact_score"]].dropna()
    if len(ser) > 5:
        p_corr, p_val = pearsonr(ser[col], ser["impact_score"])
        s_corr, s_val = spearmanr(ser[col], ser["impact_score"])
        analysis_rows.append({
            "feature": col,
            "sample_size": len(ser),
            "pearson_r": round(float(p_corr), 4),
            "pearson_p_value": round(float(p_val), 4),
            "spearman_rho": round(float(s_corr), 4),
            "spearman_p_value": round(float(s_val), 4)
        })

df_ana = pd.DataFrame(analysis_rows)
df_ana.to_csv("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/v1_feature_target_analysis.csv", index=False)
print("Saved v1_feature_target_analysis.csv successfully.")
print(df_ana)
