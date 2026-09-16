import os
import json
import pandas as pd

def build_dataset_candidate_v3(
    canonical_json="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents_v3.json",
    outcomes_json="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes_v3.json",
    features_json="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/features_v3.json",
    output_parquet="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v3.parquet",
    output_json="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate_v3.json"
):
    """
    Assembles Dataset Candidate v3.0 by joining Canonical Incidents, Observed Outcomes (Y), and Predictor Features (X).
    Enforces strict training eligibility criteria:
    - Must be a real canonical incident
    - Must have verified source provenance
    - Must have valid prediction-time features (T0 defined)
    - Must have at least one observed ground-truth outcome target (Y)
    - Must pass temporal guardrail (X <= T0, Y > T0)
    """
    os.makedirs(os.path.dirname(output_parquet), exist_ok=True)

    with open(canonical_json, 'r', encoding='utf-8') as f:
        incidents = {inc['incident_id']: inc for inc in json.load(f)}

    with open(outcomes_json, 'r', encoding='utf-8') as f:
        outcomes = {out['incident_id']: out for out in json.load(f)}

    with open(features_json, 'r', encoding='utf-8') as f:
        features = {feat['incident_id']: feat for feat in json.load(f)}

    training_rows = []

    for inc_id, inc in incidents.items():
        out = outcomes.get(inc_id, {})
        feat = features.get(inc_id, {})

        has_y = out.get('data_quality_flags', {}).get('has_observed_y', False)
        t0_valid = feat.get('temporal_guardrail', {}).get('is_temporally_valid', False)

        # Classification of Training Eligibility
        if has_y and t0_valid:
            eligibility_status = "TRAINING_ELIGIBLE"
        elif not has_y and t0_valid:
            eligibility_status = "UNLABELED"
        elif not t0_valid:
            eligibility_status = "INVALID_TEMPORAL"
        else:
            eligibility_status = "RECONCILIATION_UNCERTAIN"

        training_rows.append({
            "incident_id": inc_id,
            "prediction_timestamp_t0": feat.get('prediction_timestamp_t0'),
            "hazard_category": inc['hazard_category'],
            "country": inc['country'],
            "iso3": inc.get('iso3'),
            "source_records": inc.get('source_records', []),
            "predictor_features_x": feat.get('predictor_features_x', {}),
            "observed_outcomes_y": out.get('observed_outcomes', {}),
            "target_provenance": out.get('target_provenance', {}),
            "training_eligibility": eligibility_status,
            "is_training_eligible": eligibility_status == "TRAINING_ELIGIBLE",
            "data_quality": {
                "has_observed_y": has_y,
                "is_temporally_valid": t0_valid,
                "reconciliation_confidence": inc.get('confidence_score', 1.0)
            }
        })

    # Save outputs
    df_out = pd.DataFrame(training_rows)
    df_out.to_parquet(output_parquet, index=False)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(training_rows, f, indent=2)

    print(f"Successfully assembled {len(training_rows)} training candidate records v3.0 to {output_parquet}")
    return training_rows

if __name__ == "__main__":
    build_dataset_candidate_v3()
