# Phase 2C.3.2 — Statistical Evaluation Artifact Correction

## Executive Summary

Phase 2C.3.2 successfully corrects the statistical validation artifact inconsistencies identified in the Phase 2C.3.1 independent audit. All statistical analyses have been updated to compare frozen predictions directly from `ml/reports/severity/test_predictions.csv` (V1) and `ml/reports/severity_v2/v2_test_predictions.csv` (V2).

---

## 1. Authoritative Evaluation Population Analysis

### File & Line Count Investigation
- **V1 Prediction File (`ml/reports/severity/test_predictions.csv`)**: 337 total CSV file lines (1 header line + 336 incident evaluation rows).
- **V2 Prediction File (`ml/reports/severity_v2/v2_test_predictions.csv`)**: 337 total CSV file lines (1 header line + 336 incident evaluation rows).
- **V5 Processed Dataset (`ml/data/processed/v5/event_level_features.parquet`)**: 336 data rows (parquet binary format without line headers).

### Explanation for 337 vs 336 Line Difference
The apparent discrepancy between 337 prediction file lines and 336 dataset rows is purely a CSV line counting artifact:
- CSV text files include **1 header line** at line 1.
- Subtracting the header line yields **336 incident evaluation data rows**.
- All 336 evaluation incidents in V1 match 1-to-1 with V2 in identical order and with 100% identical ground-truth severity targets after integer normalization.
- **Conclusion**: There are no extra, stale, or duplicate prediction rows. The evaluation population is exactly **336 incidents**.

---

## 2. Direct V1 vs V2 Metrics & Bootstrap Analysis

The statistical baseline now directly compares frozen V1 test predictions against frozen V2 test predictions. Model A / ablation baseline files (`v2_ablation_results.csv`) are NOT used for the official statistical significance analysis.

### Official Configuration
- **Bootstrap Iterations**: 10,000
- **Random Seed**: 42
- **Confidence Interval**: 95% Percentile Confidence Interval (2.5th to 97.5th percentiles)
- **Brier Score Definition**: Multiclass Mean Squared Error ($Brier = \frac{1}{N} \sum_{i=1}^N \sum_{k=0}^3 (p_{i,k} - y_{i,k})^2$). Lower is better.

### Metric Results & Statistical Conclusions

| Metric | V1 Observed | V2 Observed | Observed Difference (V2 - V1) | 95% Bootstrap CI | Statistical Conclusion |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Macro F1** | 0.2497 | 0.2794 | +0.0297 | [-0.0269, +0.0859] | **NOT DEMONSTRATED** |
| **Weighted F1** | 0.3045 | 0.3139 | +0.0093 | [-0.0447, +0.0642] | **NOT DEMONSTRATED** |
| **High Recall** | 0.0000 | 0.1594 | +0.1594 | [+0.0758, +0.2500] | **SUPPORTED BY THIS TEST** |
| **Critical Recall** | 0.1389 | 0.1389 | +0.0000 | [-0.1143, +0.1111] | **NOT DEMONSTRATED** |
| **Brier Score** | 0.7115 | 0.7316 | +0.0201 | [-0.0066, +0.0469] | **NOT DEMONSTRATED** |

---

## 3. Architecture & Test Isolation Fixes

### Optional Output Paths
`ml/src/validation/statistical_significance.py` was refactored:
```python
def run_paired_bootstrap(n_iterations=10000, random_seed=42, output_csv=None, output_doc=None):
```
- `output_csv` and `output_doc` default to official paths when run as a script (`__main__`).
- Unit tests pass temporary `tmp_path` arguments to `output_csv` and `output_doc`.
- This strictly isolates pytest execution, ensuring unit tests running small iteration counts (e.g., 50 or 100) **NEVER overwrite** the official 10,000-iteration statistical report.

---

## 4. Verification & Reproducibility

1. **Deterministic Execution**: Confirmed identical output upon repeated runs with `n_iterations=10000` and `random_seed=42`.
2. **Pytest Protection**: Executed full test suite (`pytest ml/tests/ -v`). Inspected `ml/reports/severity_v2/statistical_significance.csv` post-pytest and verified it retained `bootstrap_iterations = 10000`.
