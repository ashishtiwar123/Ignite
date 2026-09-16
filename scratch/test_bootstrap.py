import pandas as pd
import numpy as np
from sklearn.metrics import f1_score, confusion_matrix

def compute_multiclass_brier(y_true, probs):
    N = len(y_true)
    y_onehot = np.zeros((N, 4))
    for i, label in enumerate(y_true):
        y_onehot[i, int(label)] = 1.0
    return np.mean(np.sum((probs - y_onehot) ** 2, axis=1))

def compute_metrics(y_true, preds, probs):
    macro_f1 = f1_score(y_true, preds, average='macro', zero_division=0)
    weighted_f1 = f1_score(y_true, preds, average='weighted', zero_division=0)
    
    cm = confusion_matrix(y_true, preds, labels=[0, 1, 2, 3])
    high_recall = cm[2, 2] / sum(cm[2, :]) if sum(cm[2, :]) > 0 else 0.0
    critical_recall = cm[3, 3] / sum(cm[3, :]) if sum(cm[3, :]) > 0 else 0.0
    
    brier = compute_multiclass_brier(y_true, probs)
    
    return {
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "high_recall": high_recall,
        "critical_recall": critical_recall,
        "brier": brier
    }

v1_df = pd.read_csv('ml/reports/severity/test_predictions.csv')
v2_df = pd.read_csv('ml/reports/severity_v2/v2_test_predictions.csv')

print("V1 columns:", v1_df.columns.tolist())
print("V2 columns:", v2_df.columns.tolist())

# Target values normalization
y_v1 = v1_df['severity_class'].astype(int).values
y_v2 = v2_df['severity_class'].astype(int).values

assert (y_v1 == y_v2).all(), "Target mismatch!"
assert (v1_df['incident_id'] == v2_df['incident_id']).all(), "Incident ID mismatch!"

v1_preds = v1_df['predicted_class'].astype(int).values
v2_preds = v2_df['predicted_class'].astype(int).values

v1_probs = v1_df[['prob_low', 'prob_moderate', 'prob_high', 'prob_critical']].values
v2_probs = v2_df[['prob_low', 'prob_moderate', 'prob_high', 'prob_critical']].values

m_v1 = compute_metrics(y_v1, v1_preds, v1_probs)
m_v2 = compute_metrics(y_v1, v2_preds, v2_probs)

print("V1 Metrics:", m_v1)
print("V2 Metrics:", m_v2)

# Paired Bootstrap
n_iterations = 10000
random_seed = 42

np.random.seed(random_seed)
n_samples = len(y_v1)
metrics = ["macro_f1", "weighted_f1", "high_recall", "critical_recall", "brier"]
diff_bootstraps = {m: np.zeros(n_iterations) for m in metrics}

for i in range(n_iterations):
    idx = np.random.choice(n_samples, size=n_samples, replace=True)
    y_b = y_v1[idx]
    
    m1_b = compute_metrics(y_b, v1_preds[idx], v1_probs[idx])
    m2_b = compute_metrics(y_b, v2_preds[idx], v2_probs[idx])
    
    for m in metrics:
        diff_bootstraps[m][i] = m2_b[m] - m1_b[m]

res = []
for m in metrics:
    v1_val = m_v1[m]
    v2_val = m_v2[m]
    diff = v2_val - v1_val
    ci_low = np.percentile(diff_bootstraps[m], 2.5)
    ci_high = np.percentile(diff_bootstraps[m], 97.5)
    
    # Statistical conclusion
    # If CI includes 0 -> NOT DEMONSTRATED
    # If CI excludes 0 -> SUPPORTED BY THIS TEST
    if ci_low <= 0 <= ci_high:
        conclusion = "NOT DEMONSTRATED"
    else:
        conclusion = "SUPPORTED BY THIS TEST"
        
    res.append(f"{m}: V1={v1_val:.4f}, V2={v2_val:.4f}, diff={diff:+.4f}, 95% CI=[{ci_low:+.4f}, {ci_high:+.4f}], Result={conclusion}")

with open('scratch/metrics_out.txt', 'w') as f:
    f.write('\n'.join(res))

print("Bootstrap completed.")
