import json
import os

def build_outcomes_v2(
    canonical_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents_v2.json",
    emdat_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/emdat/raw_emdat.json",
    desinventar_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/desinventar/raw_desinventar.json",
    output_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/observed_outcomes_v2.json"
):
    """
    Extracts observed ground-truth outcomes (Y) v2.0 from EM-DAT and DesInventar records.
    Strictly preserves null (unreported) vs 0 (observed zero).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(canonical_path, 'r', encoding='utf-8') as f:
        incidents = json.load(f)
        
    emdat_map = {}
    if os.path.exists(emdat_path):
        with open(emdat_path, 'r', encoding='utf-8') as f:
            for rec in json.load(f):
                emdat_map[rec['emdat_id']] = rec
                
    des_map = {}
    if os.path.exists(desinventar_path):
        with open(desinventar_path, 'r', encoding='utf-8') as f:
            for rec in json.load(f):
                des_map[rec['desinventar_id']] = rec
                
    outcomes = []
    
    for inc in incidents:
        inc_id = inc['incident_id']
        sources = inc.get('source_records', [])
        
        deaths = None
        injured = None
        displaced = None
        total_affected = None
        total_damage_usd = None
        houses_destroyed = None
        
        for s in sources:
            stype = s.get('source')
            sid = s.get('source_id')
            
            if stype == "EM-DAT" and sid in emdat_map:
                e = emdat_map[sid]
                deaths = e.get('total_deaths')
                injured = e.get('injured')
                displaced = e.get('displaced')
                total_affected = e.get('total_affected')
                total_damage_usd = e.get('total_damage_usd')
                
            elif stype == "DesInventar" and sid in des_map:
                d = des_map[sid]
                deaths = d.get('deaths')
                injured = d.get('injured')
                houses_destroyed = d.get('houses_destroyed')
                
        outcomes.append({
            "incident_id": inc_id,
            "hazard_category": inc['hazard_category'],
            "country": inc['country'],
            "event_start": inc['event_start'],
            "observed_outcomes": {
                "deaths": deaths,
                "injured": injured,
                "displaced": displaced,
                "total_affected": total_affected,
                "total_damage_usd": total_damage_usd,
                "houses_destroyed": houses_destroyed
            },
            "data_quality_flags": {
                "has_ground_truth": any(v is not None for v in [deaths, injured, displaced, total_damage_usd, houses_destroyed])
            }
        })
        
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(outcomes, f, indent=2)
        
    print(f"Successfully extracted {len(outcomes)} observed outcomes v2.0 to {output_path}")
    return outcomes

if __name__ == "__main__":
    build_outcomes_v2()
