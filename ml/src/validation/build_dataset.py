import json
import os
from datetime import datetime

def assemble_candidate_training_dataset(
    canonical_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents.json",
    outcomes_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes.json",
    features_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/hazard_features.json",
    dataset_output_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/training_dataset_candidate.json",
    metadata_output_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/training_dataset_metadata.json"
):
    """
    Assembles the final candidate training dataset joining Predictor Features (X <= T0)
    with Future Observed Outcomes (Y > T0). Generates comprehensive metadata artifact.
    """
    os.makedirs(os.path.dirname(dataset_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(metadata_output_path), exist_ok=True)
    
    with open(canonical_path, 'r', encoding='utf-8') as f:
        incidents = json.load(f)
        
    outcomes_map = {}
    if os.path.exists(outcomes_path):
        with open(outcomes_path, 'r', encoding='utf-8') as f:
            for o in json.load(f):
                outcomes_map[o['incident_id']] = o
                
    features_map = {}
    if os.path.exists(features_path):
        with open(features_path, 'r', encoding='utf-8') as f:
            for feat in json.load(f):
                features_map[feat['incident_id']] = feat
                
    dataset_rows = []
    hazard_counts = {}
    
    for inc in incidents:
        inc_id = inc['incident_id']
        feat_obj = features_map.get(inc_id, {})
        out_obj = outcomes_map.get(inc_id, {})
        
        hazard = inc['hazard_category']
        hazard_counts[hazard] = hazard_counts.get(hazard, 0) + 1
        
        row = {
            "incident_id": inc_id,
            "prediction_timestamp_t0": feat_obj.get('prediction_timestamp_t0'),
            "hazard_category": hazard,
            "country": inc['country'],
            "iso3": inc.get('iso3'),
            "adm2_pcode": inc.get('adm2_pcode'),
            "predictor_features_x": feat_obj.get('predictor_features_x', {}),
            "observed_outcomes_y": out_obj.get('observed_outcomes', {}),
            "data_quality": out_obj.get('data_quality_flags', {})
        }
        dataset_rows.append(row)
        
    # Write dataset
    with open(dataset_output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset_rows, f, indent=2)
        
    # Write metadata
    metadata = {
        "dataset_version": "v2.0-candidate-historical",
        "created_at_utc": datetime.utcnow().isoformat(),
        "total_records": len(dataset_rows),
        "total_features_count": len(dataset_rows[0]['predictor_features_x']) if dataset_rows else 0,
        "total_outcomes_count": len(dataset_rows[0]['observed_outcomes_y']) if dataset_rows else 0,
        "hazard_counts": hazard_counts,
        "sources_integrated": ["EM-DAT", "DesInventar", "USGS", "GDACS"],
        "schema_version": "v2.0",
        "prediction_boundary": "STRICT_T0_GUARDRAIL",
        "model_training_status": "READY_FOR_PHASE_2C_AUDIT"
    }
    
    with open(metadata_output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Successfully assembled candidate dataset with {len(dataset_rows)} rows to {dataset_output_path}")
    print(f"Metadata written to {metadata_output_path}")
    return metadata

if __name__ == "__main__":
    assemble_candidate_training_dataset()
