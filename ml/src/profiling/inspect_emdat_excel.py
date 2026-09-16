import os
import hashlib
import json
import pandas as pd

EXCEL_PATH = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/emdat/public_emdat_custom_request_2026-09-16_d55f319e-bbcb-4f8c-89ac-b6188623cbc8.xlsx"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def inspect_emdat_excel():
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: File not found at {EXCEL_PATH}")
        return
        
    size_bytes = os.path.getsize(EXCEL_PATH)
    sha256 = compute_sha256(EXCEL_PATH)
    
    excel_file = pd.ExcelFile(EXCEL_PATH)
    sheet_names = excel_file.sheet_names
    print(f"Excel File: {EXCEL_PATH}")
    print(f"Size: {size_bytes} bytes ({round(size_bytes / (1024*1024), 2)} MB)")
    print(f"SHA256: {sha256}")
    print(f"Sheets: {sheet_names}")
    
    # Load primary data sheet
    data_sheet_name = "EM-DAT Data" if "EM-DAT Data" in sheet_names else sheet_names[0]
    df = pd.read_excel(EXCEL_PATH, sheet_name=data_sheet_name)
    
    total_rows = len(df)
    total_cols = len(df.columns)
    col_names = list(df.columns)
    
    print(f"\n--- Primary Sheet: '{data_sheet_name}' ---")
    print(f"Row Count: {total_rows}")
    print(f"Column Count: {total_cols}")
    print(f"Columns: {col_names}")
    
    # Missingness profiling
    null_counts = df.isnull().sum().to_dict()
    null_percentages = (df.isnull().sum() / max(1, total_rows) * 100).to_dict()
    
    # Identifier check
    id_col = [c for c in col_names if "DisNo" in c or "Disaster" in c or "ID" in c]
    unique_ids = df[id_col[0]].nunique() if id_col else 0
    duplicate_ids = total_rows - unique_ids if id_col else 0
    
    # Date range
    start_years = df["Start Year"].dropna() if "Start Year" in col_names else []
    min_year = int(start_years.min()) if len(start_years) > 0 else None
    max_year = int(start_years.max()) if len(start_years) > 0 else None
    
    # Geographic & Hazard Breakdown
    countries = df["Country"].dropna().unique().tolist() if "Country" in col_names else []
    disaster_types = df["Disaster Type"].value_counts().to_dict() if "Disaster Type" in col_names else {}
    
    # Key outcome coverage
    deaths_col = [c for c in col_names if "Death" in c or "Killed" in c]
    injured_col = [c for c in col_names if "Injured" in c]
    affected_col = [c for c in col_names if "Total Affected" in c or "Affected" in c]
    damage_col = [c for c in col_names if "Damage" in c]
    
    observed_deaths = df[deaths_col[0]].notnull().sum() if deaths_col else 0
    observed_injured = df[injured_col[0]].notnull().sum() if injured_col else 0
    observed_affected = df[affected_col[0]].notnull().sum() if affected_col else 0
    observed_damage = df[damage_col[0]].notnull().sum() if damage_col else 0
    
    profile_result = {
        "file_path": EXCEL_PATH,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "sheet_names": sheet_names,
        "data_sheet": data_sheet_name,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "columns": col_names,
        "min_year": min_year,
        "max_year": max_year,
        "unique_countries_count": len(countries),
        "disaster_types": disaster_types,
        "unique_disaster_ids": unique_ids,
        "duplicate_disaster_ids": duplicate_ids,
        "outcome_coverage": {
            "observed_deaths_count": int(observed_deaths),
            "observed_injured_count": int(observed_injured),
            "observed_affected_count": int(observed_affected),
            "observed_damage_count": int(observed_damage)
        },
        "first_5_head": df.head(5).to_dict(orient="records"),
        "last_5_tail": df.tail(5).to_dict(orient="records")
    }
    
    out_json = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/emdat_excel_inspection.json"
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(profile_result, f, indent=2, default=str)
        
    print(f"\nInspection JSON written to: {out_json}")
    return profile_result

if __name__ == "__main__":
    inspect_emdat_excel()
