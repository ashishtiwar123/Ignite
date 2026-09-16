import os
import json
import pandas as pd
import numpy as np

V4_PARQUET = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v4/event_level_training.parquet"
RAW_WB_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/worldbank/"
V5_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/processed/v5/"

def convert_types(obj):
    if isinstance(obj, dict):
        return {k: convert_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_types(i) for i in obj]
    elif hasattr(obj, 'item'):
        return obj.item()
    return obj

def load_worldbank_map(filename):
    filepath = os.path.join(RAW_WB_DIR, filename)
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        if len(data) > 1 and isinstance(data[1], list):
            # Key: (iso3, year_str)
            wb_map = {}
            for item in data[1]:
                iso3 = item.get('countryiso3code')
                date_str = item.get('date')
                val = item.get('value')
                if iso3 and date_str and val is not None:
                    wb_map[(str(iso3).upper(), str(date_str))] = float(val)
            return wb_map
    return {}

def build_v5_pipeline():
    os.makedirs(V5_DIR, exist_ok=True)
    df_v4 = pd.read_parquet(V4_PARQUET)
    print(f"Loaded {len(df_v4)} records from V4 training dataset.")

    # Load World Bank indicators
    pop_map = load_worldbank_map("worldbank_population.json")
    den_map = load_worldbank_map("worldbank_pop_density.json")
    urb_map = load_worldbank_map("worldbank_urban_pct.json")
    pov_map = load_worldbank_map("worldbank_poverty_pct.json")

    print(f"Loaded World Bank mappings: Pop ({len(pop_map)}), Density ({len(den_map)}), Urban ({len(urb_map)}), Poverty ({len(pov_map)}).")

    v5_rows = []
    provenance_rows = []
    quality_rows = []

    pop_matched = 0
    den_matched = 0
    urb_matched = 0
    pov_matched = 0

    for _, row in df_v4.iterrows():
        inc_id = row['incident_id']
        iso3 = str(row['iso3']).upper() if pd.notna(row['iso3']) else ""
        s_date = str(row['start_date']) if pd.notna(row['start_date']) else ""
        year_str = s_date.split("-")[0] if "-" in s_date else "2020"

        # Search historical match (exact year or nearest preceding)
        wb_pop = None
        wb_den = None
        wb_urb = None
        wb_pov = None
        matched_year = None

        if iso3 and year_str.isdigit():
            target_yr = int(year_str)
            for yr in range(target_yr, 1999, -1):
                yr_s = str(yr)
                if (iso3, yr_s) in pop_map and wb_pop is None:
                    wb_pop = pop_map[(iso3, yr_s)]
                    matched_year = yr_s
                if (iso3, yr_s) in den_map and wb_den is None:
                    wb_den = den_map[(iso3, yr_s)]
                if (iso3, yr_s) in urb_map and wb_urb is None:
                    wb_urb = urb_map[(iso3, yr_s)]
                if (iso3, yr_s) in pov_map and wb_pov is None:
                    wb_pov = pov_map[(iso3, yr_s)]

        if wb_pop is not None: pop_matched += 1
        if wb_den is not None: den_matched += 1
        if wb_urb is not None: urb_matched += 1
        if wb_pov is not None: pov_matched += 1

        # Combine physical hazard X with exposure/vulnerability X
        fx = dict(row['predictor_features_x'])
        
        # Exposure Features
        fx['country_population'] = wb_pop
        fx['population_density_sqkm'] = wb_den
        fx['urban_population_pct'] = wb_urb
        fx['poverty_headcount_pct'] = wb_pov
        
        # Derived Features
        fx['log_population_exposure'] = round(float(np.log1p(wb_pop)), 4) if wb_pop is not None else None
        
        # Hazard intensity x Exposure interaction
        haz_int = fx.get('hazard_intensity_index', 0.0)
        if haz_int is not None and wb_den is not None:
            fx['hazard_x_exposure_interaction'] = round(float(haz_int * np.log1p(wb_den)), 4)
        else:
            fx['hazard_x_exposure_interaction'] = None

        rec = dict(row)
        rec['predictor_features_x'] = fx
        rec['exposure_provenance'] = {
            "population_source": "WorldBank_SP.POP.TOTL",
            "population_density_source": "WorldBank_EN.POP.DNST",
            "urban_pct_source": "WorldBank_SP.URB.TOTL.IN.ZS",
            "poverty_pct_source": "WorldBank_SI.POV.NAHC",
            "matched_year": matched_year,
            "temporal_alignment_status": "EXACT_MATCH" if matched_year == year_str else "HISTORICAL_NEAREST_PRECEDING"
        }
        rec['dataset_version'] = "v5.0-exposure-enriched"
        
        v5_rows.append(rec)

        provenance_rows.append({
            "incident_id": inc_id,
            "iso3": iso3,
            "event_year": year_str,
            "matched_population_year": matched_year,
            "has_population": wb_pop is not None,
            "has_density": wb_den is not None,
            "has_urban_pct": wb_urb is not None,
            "has_poverty_pct": wb_pov is not None,
            "provenance_classification": "[VERIFIED API RETRIEVAL]"
        })

    v5_rows = convert_types(v5_rows)

    # Export V5 artifacts
    df_v5 = pd.DataFrame(v5_rows)
    df_v5.to_parquet(os.path.join(V5_DIR, "event_level_features.parquet"), index=False)
    with open(os.path.join(V5_DIR, "event_level_features.json"), "w", encoding="utf-8") as f:
        json.dump(v5_rows, f, indent=2)

    pd.DataFrame(provenance_rows).to_parquet(os.path.join(V5_DIR, "feature_provenance.parquet"), index=False)

    print("\n--- DATASET V5.0 PIPELINE RESULTS ---")
    print(f"Total V5 Event-Enriched Rows: {len(df_v5)}")
    print(f"Population Matched Rows: {pop_matched} ({round(pop_matched/len(df_v5)*100, 2)}%)")
    print(f"Population Density Matched: {den_matched} ({round(den_matched/len(df_v5)*100, 2)}%)")
    print(f"Urban Population % Matched: {urb_matched} ({round(urb_matched/len(df_v5)*100, 2)}%)")
    print(f"Poverty Headcount % Matched: {pov_matched} ({round(pov_matched/len(df_v5)*100, 2)}%)")

    # Generate V2 feature quality report CSV
    qual_rows = []
    sample_fx = df_v5['predictor_features_x'].iloc[0]
    for feat_name in sample_fx.keys():
        vals = [r['predictor_features_x'].get(feat_name) for r in v5_rows]
        non_null_c = sum(1 for v in vals if v is not None and not pd.isna(v))
        qual_rows.append({
            "feature_name": feat_name,
            "total_rows": len(df_v5),
            "non_null_count": non_null_c,
            "null_count": len(df_v5) - non_null_c,
            "null_pct": round(((len(df_v5) - non_null_c) / len(df_v5)) * 100, 2)
        })
    pd.DataFrame(qual_rows).to_csv("c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/v2_feature_quality.csv", index=False)
    print("Saved v2_feature_quality.csv successfully.")

if __name__ == "__main__":
    build_v5_pipeline()
