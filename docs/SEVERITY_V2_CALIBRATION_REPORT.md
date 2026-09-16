# Severity V2 Probability Calibration Report

## Calibration Methodology
- **Data Splitting**: Strict Out-Of-Fold (OOF) prediction strategy using 5-fold Stratified CV.
- **Leak Prevention**: Calibration parameters (Platt sigmoid vs Isotonic) fitted strictly within fold training subsets; final validation scores evaluated on held-out out-of-fold folds.
- **Chosen Method**: **SIGMOID** scaling (Platt scaling preferred due to small sample size N=336).

## Performance Comparison (Out-of-Fold)

| Pipeline | Multiclass Brier Score (Lower is better) | Multiclass Log Loss (Lower is better) | Status |
| :--- | :---: | :---: | :--- |
| **Raw V2 (Uncalibrated)** | 0.7316 | 1.3225 | Raw Model Binary |
| **Calibrated V2 (Sigmoid)** | 0.6959 | 1.2631 | SELECTED |
| **Calibrated V2 (Isotonic)** | 0.7027 | 1.5648 | Evaluated |

## Safety & Verification Audit
- **Target Leakage**: VERIFIED NONE (No evaluation labels exposed to calibrator fitting).
- **Production Impact**: Calibration binary stored under `ml/models/severity_v2/calibration/v2_calibrator.joblib`. Raw V2 model binary (`severity_model.joblib`) remains untouched and frozen.
- **Deterministic Execution**: Verified via `random_state=42` across all folds.
- **Sample Size Constraints**: N=336 total events across 4 classes. Platt sigmoid scaling provides smoother, less overfitted probability updates than isotonic regression on this sample size.