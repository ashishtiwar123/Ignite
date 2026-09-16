import os
import hashlib
import json
import pandas as pd

EXCEL_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/emdat/public_emdat_custom_request_2026-09-16_d55f319e-bbcb-4f8c-89ac-b6188623cbc8.xlsx"
LEGACY_JSON_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/emdat/raw_emdat.json"
OUTPUT_PARQUET = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/interim/emdat/emdat_normalized.parquet"
OUTPUT_JSON = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/interim/emdat/emdat_normalized.json"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def ingest_official_emdat_excel():
    """
    Ingests official manually downloaded EM-DAT Excel export (PRIMARY_EMDAT_SOURCE).
    Reads 16,764 historical records (2000-2025) and outputs normalized dataset.
    Preserves raw missingness (NaN remains None, NOT 0).
    """
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Official EM-DAT Excel export file missing at {EXCEL_PATH}")
        
    sha256_hash = compute_sha256(EXCEL_PATH)
    print(f"Ingesting official EM-DAT Excel export: {EXCEL_PATH}")
    print(f"SHA256: {sha256_hash}")
    
    # Read Excel sheet 'EM-DAT Data'
    df_raw = pd.read_excel(EXCEL_PATH, sheet_name="EM-DAT Data")
    total_raw_rows = len(df_raw)
    
    if total_raw_rows < 1000:
        raise ValueError(f"Expected >10,000 EM-DAT records, but found only {total_raw_rows} rows!")
        
    print(f"Successfully loaded {total_raw_rows} raw records from 'EM-DAT Data' sheet.")
    
    # Construct normalized DataFrame directly from dict mapping to avoid pandas index alignment issues
    norm_dict = {
        "source_dataset": ["EM-DAT"] * total_raw_rows,
        "source_record_id": df_raw["DisNo."].astype(str),
        "emdat_disno": df_raw["DisNo."].astype(str),
        "disaster_group": df_raw["Disaster Group"],
        "disaster_subgroup": df_raw["Disaster Subgroup"],
        "disaster_type": df_raw["Disaster Type"],
        "disaster_subtype": df_raw["Disaster Subtype"],
        "event_name": df_raw["Event Name"],
        "iso3": df_raw["ISO"],
        "country": df_raw["Country"],
        "region": df_raw["Region"],
        "subregion": df_raw["Subregion"],
        "location_text": df_raw["Location"],
        "latitude": df_raw["Latitude"],
        "longitude": df_raw["Longitude"],
        "start_year": df_raw["Start Year"],
        "start_month": df_raw["Start Month"],
        "start_day": df_raw["Start Day"],
        "end_year": df_raw["End Year"],
        "end_month": df_raw["End Month"],
        "end_day": df_raw["End Day"],
        "total_deaths": df_raw["Total Deaths"],
        "no_injured": df_raw["No. Injured"],
        "no_affected": df_raw["No. Affected"],
        "no_homeless": df_raw["No. Homeless"],
        "total_affected": df_raw["Total Affected"],
        "total_damage_usd_thousands": df_raw["Total Damage ('000 US$)"],
        "total_damage_adjusted_usd_thousands": df_raw["Total Damage, Adjusted ('000 US$)"],
        "ingestion_version": ["v2.0-official-export"] * total_raw_rows,
        "ingestion_timestamp_utc": [pd.Timestamp.now('UTC').isoformat()] * total_raw_rows,
        "source_file": [os.path.basename(EXCEL_PATH)] * total_raw_rows,
        "source_file_sha256": [sha256_hash] * total_raw_rows
    }
    
    df_normalized = pd.DataFrame(norm_dict)
    
    # Export to Parquet and JSON
    os.makedirs(os.path.dirname(OUTPUT_PARQUET), exist_ok=True)
    df_normalized.to_parquet(OUTPUT_PARQUET, index=False)
    
    records_json = df_normalized.to_dict(orient="records")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(records_json, f, indent=2, default=str)
        
    print(f"Normalized dataset written to Parquet ({OUTPUT_PARQUET}) and JSON ({OUTPUT_JSON}).")
    return df_normalized

if __name__ == "__main__":
    ingest_official_emdat_excel()
