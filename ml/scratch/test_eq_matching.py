import pandas as pd
import json
from datetime import datetime

emdat_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/interim/emdat/emdat_normalized.parquet"
usgs_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/usgs/usgs_historical_earthquakes.json"

df_em = pd.read_parquet(emdat_path)
df_eq = df_em[df_em['disaster_type'] == 'Earthquake'].copy()

with open(usgs_path, "r", encoding="utf-8") as f:
    usgs_feats = json.load(f).get("features", [])

# Parse USGS dates & locations
usgs_list = []
for feat in usgs_feats:
    p = feat['properties']
    g = feat['geometry']['coordinates']
    t_dt = datetime.utcfromtimestamp(p['time'] / 1000.0)
    usgs_list.append({
        "usgs_id": feat['id'],
        "mag": p.get('mag'),
        "depth_km": g[2] if len(g) > 2 else None,
        "lat": g[1],
        "lon": g[0],
        "place": p.get('place', ''),
        "date_str": t_dt.strftime('%Y-%m-%d'),
        "dt": t_dt
    })
df_usgs = pd.DataFrame(usgs_list)

matches = []
for _, row in df_eq.iterrows():
    s_yr = row['start_year']
    s_mo = row['start_month']
    s_dy = row['start_day']
    if pd.isna(s_yr):
        continue
    yr = int(s_yr)
    mo = int(s_mo) if pd.notna(s_mo) and s_mo > 0 else 1
    dy = int(s_dy) if pd.notna(s_dy) and s_dy > 0 else 1
    try:
        em_dt = datetime(yr, mo, dy)
    except Exception:
        continue
    
    country = str(row['country']).upper()
    iso = str(row['iso3']).upper() if pd.notna(row['iso3']) else ""
    
    # Candidate USGS within +/- 7 days
    df_cand = df_usgs[abs((df_usgs['dt'] - em_dt).dt.days) <= 7].copy()
    if len(df_cand) == 0:
        continue
        
    for _, urow in df_cand.iterrows():
        u_place = str(urow['place']).upper()
        # Check country / ISO match in place text
        if country in u_place or (iso and iso in u_place) or (country == "TURKEY" and "TÜRKIYE" in u_place) or (country == "SYRIAN ARAB REPUBLIC" and "SYRIA" in u_place) or (country == "UNITED STATES OF AMERICA" and ("UNITED STATES" in u_place or "CALIFORNIA" in u_place or "ALASKA" in u_place or "HAWAII" in u_place)):
            t_diff_hours = abs((urow['dt'] - em_dt).total_seconds()) / 3600.0
            score = 1.0 - (t_diff_hours / (7 * 24))
            matches.append({
                "emdat_dis_no": row['source_record_id'],
                "country": row['country'],
                "start_date": em_dt.strftime('%Y-%m-%d'),
                "usgs_id": urow['usgs_id'],
                "usgs_mag": urow['mag'],
                "usgs_depth": urow['depth_km'],
                "usgs_place": urow['place'],
                "t_diff_hours": t_diff_hours,
                "score": score
            })

df_matches = pd.DataFrame(matches)
print(f"Total Earthquake Candidate Matches Found: {len(df_matches)}")
if len(df_matches) > 0:
    print(f"Unique EM-DAT Earthquakes Matched: {df_matches['emdat_dis_no'].nunique()} out of {len(df_eq)} (Date range in USGS: 2018-2026)")
    print(df_matches.head(10))
