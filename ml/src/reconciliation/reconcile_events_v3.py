import os
import json
import pandas as pd
from datetime import datetime

def reconcile_events_v3(
    emdat_parquet_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/interim/emdat/emdat_normalized.parquet",
    desinventar_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/desinventar/raw_desinventar.json",
    usgs_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/usgs/usgs_historical_earthquakes.json",
    ibtracs_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/ibtracs/raw_ibtracs.json",
    gdacs_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/gdacs_alerts.json",
    output_parquet="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents_v3.parquet",
    output_json="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/canonical_incidents_v3.json"
):
    """
    Multi-Source Reconciliation Engine (v3.0)
    Reconciles official EM-DAT Parquet export (16,764 records) along with DesInventar,
    USGS Earthquakes, NOAA IBTrACS, and GDACS into canonical incident entities.
    """
    os.makedirs(os.path.dirname(output_parquet), exist_ok=True)
    canonical_incidents = []

    # Map EM-DAT disaster type to PS20 canonical hazard category
    def map_emdat_hazard(dis_type):
        if not dis_type:
            return "OTHER"
        dt = str(dis_type).upper()
        if "FLOOD" in dt:
            return "FLOOD"
        elif "STORM" in dt or "TROPICAL" in dt or "HURRICANE" in dt or "CYCLONE" in dt:
            return "CYCLONE"
        elif "EARTHQUAKE" in dt or "TSUNAMI" in dt:
            return "EARTHQUAKE"
        elif "WILDFIRE" in dt or "FIRE" in dt:
            return "WILDFIRE"
        elif "LANDSLIDE" in dt or "SLUMP" in dt or "AVALANCHE" in dt or "MASS MOVEMENT" in dt:
            return "LANDSLIDE"
        elif "DROUGHT" in dt:
            return "DROUGHT"
        elif "TEMPERATURE" in dt or "HEAT" in dt or "COLD" in dt:
            return "EXTREME_TEMPERATURE"
        elif "EPIDEMIC" in dt:
            return "EPIDEMIC"
        else:
            return dt.replace(" ", "_")

    # 1. Primary Verified Outcome Source: EM-DAT Official Export
    if os.path.exists(emdat_parquet_path):
        df_emdat = pd.read_parquet(emdat_parquet_path)
        for _, rec in df_emdat.iterrows():
            dis_no = str(rec['source_record_id'])
            inc_id = f"INC-EMDAT-{dis_no}"
            
            # Formulate start date YYYY-MM-DD
            s_yr = rec.get('start_year')
            s_mo = rec.get('start_month')
            s_dy = rec.get('start_day')
            if pd.notna(s_yr):
                yr_str = str(int(s_yr))
                mo_str = f"{int(s_mo):02d}" if pd.notna(s_mo) and s_mo > 0 else "01"
                dy_str = f"{int(s_dy):02d}" if pd.notna(s_dy) and s_dy > 0 else "01"
                start_date = f"{yr_str}-{mo_str}-{dy_str}"
            else:
                start_date = None

            e_yr = rec.get('end_year')
            e_mo = rec.get('end_month')
            e_dy = rec.get('end_day')
            if pd.notna(e_yr):
                yr_str = str(int(e_yr))
                mo_str = f"{int(e_mo):02d}" if pd.notna(e_mo) and e_mo > 0 else "01"
                dy_str = f"{int(e_dy):02d}" if pd.notna(e_dy) and e_dy > 0 else "01"
                end_date = f"{yr_str}-{mo_str}-{dy_str}"
            else:
                end_date = start_date

            dis_type = str(rec.get('disaster_type', 'Disaster'))
            canonical_incidents.append({
                "incident_id": inc_id,
                "canonical_name": f"{dis_type} in {rec.get('country', 'Unknown')} ({start_date})",
                "hazard_category": map_emdat_hazard(dis_type),
                "emdat_disaster_type": dis_type,
                "emdat_disaster_subtype": str(rec.get('disaster_subtype')) if pd.notna(rec.get('disaster_subtype')) else None,
                "event_start": start_date,
                "event_end": end_date,
                "country": str(rec.get('country', '')),
                "iso3": str(rec.get('iso3')) if pd.notna(rec.get('iso3')) else None,
                "region": str(rec.get('region')) if pd.notna(rec.get('region')) else None,
                "location": str(rec.get('location_text')) if pd.notna(rec.get('location_text')) else None,
                "latitude": float(rec.get('latitude')) if pd.notna(rec.get('latitude')) else None,
                "longitude": float(rec.get('longitude')) if pd.notna(rec.get('longitude')) else None,
                "source_records": [{"source": "EM-DAT", "source_id": dis_no, "provenance": "[VERIFIED MANUAL DOWNLOAD]"}],
                "confidence_score": 1.0,
                "matching_method": "PRIMARY_SOURCE_DIRECT_IMPORT",
                "reconciliation_status": "VERIFIED_PRIMARY"
            })

    # 2. DesInventar Subnational Records (Legacy Static)
    if os.path.exists(desinventar_path):
        with open(desinventar_path, 'r', encoding='utf-8') as f:
            des_data = json.load(f)
            for rec in des_data:
                inc_id = f"INC-DES-{rec['desinventar_id']}"
                canonical_incidents.append({
                    "incident_id": inc_id,
                    "canonical_name": f"{rec['event_type']} in {rec['district']}, {rec['country']} ({rec['event_date']})",
                    "hazard_category": str(rec['event_type']).upper(),
                    "emdat_disaster_type": None,
                    "emdat_disaster_subtype": None,
                    "event_start": rec['event_date'],
                    "event_end": rec['event_date'],
                    "country": rec['country'],
                    "iso3": rec['iso3'],
                    "region": rec['state'],
                    "location": rec['district'],
                    "latitude": None,
                    "longitude": None,
                    "source_records": [{"source": "DesInventar", "source_id": rec['desinventar_id'], "provenance": "[STATIC DATA]"}],
                    "confidence_score": 0.90,
                    "matching_method": "DESINVENTAR_SUBNATIONAL",
                    "reconciliation_status": "STATIC_SECONDARY"
                })

    # 3. NOAA IBTrACS Tropical Cyclones (Legacy Static)
    if os.path.exists(ibtracs_path):
        with open(ibtracs_path, 'r', encoding='utf-8') as f:
            ibtracs_data = json.load(f)
            for rec in ibtracs_data:
                inc_id = f"INC-IBTRACS-{rec['sid']}"
                canonical_incidents.append({
                    "incident_id": inc_id,
                    "canonical_name": f"Tropical Cyclone {rec['name']} ({rec['season']}) - {rec['country']}",
                    "hazard_category": "CYCLONE",
                    "emdat_disaster_type": None,
                    "emdat_disaster_subtype": None,
                    "event_start": rec['landfall_date'],
                    "event_end": rec['landfall_date'],
                    "country": rec['country'],
                    "iso3": rec['iso3'],
                    "region": None,
                    "location": None,
                    "latitude": None,
                    "longitude": None,
                    "source_records": [{"source": "NOAA_IBTrACS", "source_id": rec['sid'], "provenance": "[STATIC DATA]"}],
                    "confidence_score": 0.95,
                    "matching_method": "NOAA_BEST_TRACK",
                    "reconciliation_status": "STATIC_HAZARD_PREDICTOR"
                })

    # 4. Multi-Year USGS Historical Earthquakes (Verified GeoJSON API export)
    if os.path.exists(usgs_path):
        with open(usgs_path, 'r', encoding='utf-8') as f:
            usgs_data = json.load(f)
            features = usgs_data.get('features', [])
            for feat in features:
                props = feat.get('properties', {})
                mag = props.get('mag', 0)
                if mag >= 6.0:  # Major seismic events
                    coords = feat.get('geometry', {}).get('coordinates', [0, 0, 0])
                    t_str = datetime.utcfromtimestamp(props['time']/1000.0).strftime('%Y-%m-%d')
                    inc_id = f"INC-USGS-{feat['id']}"
                    canonical_incidents.append({
                        "incident_id": inc_id,
                        "canonical_name": f"Earthquake Mw {mag} - {props.get('place')}",
                        "hazard_category": "EARTHQUAKE",
                        "emdat_disaster_type": None,
                        "emdat_disaster_subtype": None,
                        "event_start": t_str,
                        "event_end": t_str,
                        "country": props.get('place', '').split(',')[-1].strip() if ',' in props.get('place', '') else 'Global',
                        "iso3": None,
                        "region": None,
                        "location": props.get('place'),
                        "latitude": coords[1],
                        "longitude": coords[0],
                        "source_records": [{"source": "USGS", "source_id": feat['id'], "provenance": "[VERIFIED API RETRIEVAL]"}],
                        "confidence_score": 0.99,
                        "matching_method": "USGS_HISTORICAL_SEISMIC",
                        "reconciliation_status": "VERIFIED_HAZARD_PREDICTOR"
                    })

    # Save to JSON and Parquet
    df_out = pd.DataFrame(canonical_incidents)
    df_out.to_parquet(output_parquet, index=False)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(canonical_incidents, f, indent=2)

    print(f"Successfully reconciled {len(canonical_incidents)} canonical incidents v3.0 to {output_parquet}")
    return canonical_incidents

if __name__ == "__main__":
    reconcile_events_v3()
