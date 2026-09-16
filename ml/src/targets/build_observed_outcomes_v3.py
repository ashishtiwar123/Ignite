import os
import json
import pandas as pd

def build_observed_outcomes_v3(
    emdat_parquet_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/interim/emdat/emdat_normalized.parquet",
    desinventar_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/desinventar/raw_desinventar.json",
    canonical_json_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents_v3.json",
    output_parquet="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes_v3.parquet",
    output_json="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes_v3.json"
):
    """
    Extracts observed ground-truth outcome targets (Y) v3.0 from real EM-DAT export and DesInventar records.
    Strictly preserves null (unreported) vs 0 (observed zero).
    """
    os.makedirs(os.path.dirname(output_parquet), exist_ok=True)

    with open(canonical_json_path, 'r', encoding='utf-8') as f:
        canonical_incidents = json.load(f)

    # Load normalized EM-DAT map
    emdat_map = {}
    if os.path.exists(emdat_parquet_path):
        df_emdat = pd.read_parquet(emdat_parquet_path)
        for _, row in df_emdat.iterrows():
            dis_no = str(row['source_record_id'])
            emdat_map[dis_no] = {
                "deaths": float(row['total_deaths']) if pd.notna(row['total_deaths']) else None,
                "injured": float(row['no_injured']) if pd.notna(row['no_injured']) else None,
                "affected": float(row['no_affected']) if pd.notna(row['no_affected']) else None,
                "homeless": float(row['no_homeless']) if pd.notna(row['no_homeless']) else None,
                "total_affected": float(row['total_affected']) if pd.notna(row['total_affected']) else None,
                "total_damage_usd_thousands": float(row['total_damage_usd_thousands']) if pd.notna(row['total_damage_usd_thousands']) else None,
            }

    # Load DesInventar map
    des_map = {}
    if os.path.exists(desinventar_path):
        with open(desinventar_path, 'r', encoding='utf-8') as f:
            for rec in json.load(f):
                des_map[rec['desinventar_id']] = {
                    "deaths": float(rec['deaths']) if rec.get('deaths') is not None else None,
                    "injured": float(rec['injured']) if rec.get('injured') is not None else None,
                    "houses_destroyed": float(rec['houses_destroyed']) if rec.get('houses_destroyed') is not None else None,
                }

    outcomes = []
    for inc in canonical_incidents:
        inc_id = inc['incident_id']
        sources = inc.get('source_records', [])

        deaths = None
        injured = None
        affected = None
        homeless = None
        total_affected = None
        total_damage_usd_thousands = None
        houses_destroyed = None

        has_ground_truth = False

        for s in sources:
            stype = s.get('source')
            sid = str(s.get('source_id'))

            if stype == "EM-DAT" and sid in emdat_map:
                e = emdat_map[sid]
                deaths = e['deaths']
                injured = e['injured']
                affected = e['affected']
                homeless = e['homeless']
                total_affected = e['total_affected']
                total_damage_usd_thousands = e['total_damage_usd_thousands']
                has_ground_truth = any(v is not None for v in [deaths, injured, affected, homeless, total_affected, total_damage_usd_thousands])

            elif stype == "DesInventar" and sid in des_map:
                d = des_map[sid]
                deaths = d['deaths']
                injured = d['injured']
                houses_destroyed = d['houses_destroyed']
                has_ground_truth = any(v is not None for v in [deaths, injured, houses_destroyed])

        outcomes.append({
            "incident_id": inc_id,
            "hazard_category": inc['hazard_category'],
            "country": inc['country'],
            "event_start": inc.get('event_start'),
            "observed_outcomes": {
                "deaths": deaths,
                "injured": injured,
                "affected": affected,
                "homeless": homeless,
                "total_affected": total_affected,
                "total_damage_usd_thousands": total_damage_usd_thousands,
                "houses_destroyed": houses_destroyed
            },
            "target_provenance": {
                "source_dataset": sources[0]['source'] if sources else "UNKNOWN",
                "source_record_id": sources[0]['source_id'] if sources else "UNKNOWN",
                "provenance_classification": sources[0].get('provenance', '[UNKNOWN]') if sources else "[UNKNOWN]"
            },
            "data_quality_flags": {
                "has_observed_y": has_ground_truth,
                "deaths_is_null": deaths is None,
                "damage_is_null": total_damage_usd_thousands is None,
                "affected_is_null": total_affected is None
            }
        })

    # Save outputs
    df_out = pd.DataFrame(outcomes)
    df_out.to_parquet(output_parquet, index=False)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(outcomes, f, indent=2)

    print(f"Successfully constructed {len(outcomes)} observed outcomes v3.0 to {output_parquet}")
    return outcomes

if __name__ == "__main__":
    build_observed_outcomes_v3()
