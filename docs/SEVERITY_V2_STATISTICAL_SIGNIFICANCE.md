# Severity V2 Statistical Significance Analysis

## Methodological Overview
- **Methodology**: Paired bootstrap resampling of evaluation predictions across identical incident splits (336 evaluation incidents).
- **Iterations**: 100
- **Random Seed**: 42
- **Confidence Level**: 95% Percentile Confidence Interval (2.5th to 97.5th percentile of difference distribution)
- **Baseline Source**: Direct comparison between frozen V1 prediction artifact (`test_predictions.csv`) and frozen V2 prediction artifact (`v2_test_predictions.csv`). Supercedes prior ablation-based V1 baselines.
- **Brier Score Metric**: Multiclass Brier score computed as mean squared error over predicted class probabilities vs one-hot targets. Lower score is better.

## Paired Bootstrap Results

| Metric | V1 Observed | V2 Observed | Observed Difference (V2 - V1) | 95% Confidence Interval | Statistical Significance Result |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `macro_f1` | 0.2497 | 0.2794 | +0.0297 | [-0.0153, +0.0888] | **NOT DEMONSTRATED** |
| `weighted_f1` | 0.3045 | 0.3139 | +0.0093 | [-0.0380, +0.0710] | **NOT DEMONSTRATED** |
| `high_recall` | 0.0000 | 0.1594 | +0.1594 | [+0.0883, +0.2388] | **SUPPORTED BY THIS TEST** |
| `critical_recall` | 0.1389 | 0.1389 | +0.0000 | [-0.0998, +0.0995] | **NOT DEMONSTRATED** |
| `brier` | 0.7115 | 0.7316 | +0.0201 | [-0.0104, +0.0428] | **NOT DEMONSTRATED** |

## Conclusion & Claims Compliance
1. **Macro F1**: Observed V1=0.2497, V2=0.2794, difference=+0.0297 [-0.0153, +0.0888]. **STATISTICAL SIGNIFICANCE = NOT DEMONSTRATED**.
2. **Weighted F1**: Observed V1=0.3045, V2=0.3139, difference=+0.0093 [-0.0380, +0.0710]. **STATISTICAL SIGNIFICANCE = NOT DEMONSTRATED**.
3. **High Recall**: Observed V1=0.0000, V2=0.1594, difference=+0.1594 [+0.0883, +0.2388]. **STATISTICAL SIGNIFICANCE = SUPPORTED BY THIS TEST**.
4. **Critical Recall**: Observed V1=0.1389, V2=0.1389, difference=+0.0000 [-0.0998, +0.0995]. **STATISTICAL SIGNIFICANCE = NOT DEMONSTRATED**.
5. **Brier**: Observed V1=0.7115, V2=0.7316, difference=+0.0201 [-0.0104, +0.0428]. **STATISTICAL SIGNIFICANCE = NOT DEMONSTRATED**.

> [!IMPORTANT]
> Direct statistical comparison across 336 evaluation incidents confirms that statistical significance conclusions MUST be based strictly on non-zero-overlapping 95% bootstrap confidence intervals. High Recall improvement (+0.1594) is statistically supported, whereas Macro F1, Weighted F1, Critical Recall, and Brier score differences are NOT demonstrated to be statistically significant on N=336.