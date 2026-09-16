import json
import os
from datetime import datetime

def profile_usgs_data(raw_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/usgs_earthquakes.json"):
    if not os.path.exists(raw_path):
        return {"status": "FILE_NOT_FOUND", "path": raw_path}
    
    with open(raw_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    features = data.get('features', [])
    total_records = len(features)
    
    null_counts = {
        "magnitude": 0,
        "place": 0,
        "time": 0,
        "coordinates": 0,
        "depth": 0
    }
    
    magnitudes = []
    timestamps = []
    coordinates = []
    
    for feat in features:
        props = feat.get('properties', {})
        geom = feat.get('geometry', {})
        
        mag = props.get('mag')
        if mag is None:
            null_counts["magnitude"] += 1
        else:
            magnitudes.append(mag)
            
        t = props.get('time')
        if t is None:
            null_counts["time"] += 1
        else:
            timestamps.append(t)
            
        coords = geom.get('coordinates', [])
        if not coords or len(coords) < 3:
            null_counts["coordinates"] += 1
        else:
            coordinates.append(coords)
            
    min_mag = min(magnitudes) if magnitudes else None
    max_mag = max(magnitudes) if magnitudes else None
    avg_mag = sum(magnitudes)/len(magnitudes) if magnitudes else None
    
    min_date = datetime.utcfromtimestamp(min(timestamps)/1000.0).isoformat() if timestamps else None
    max_date = datetime.utcfromtimestamp(max(timestamps)/1000.0).isoformat() if timestamps else None
    
    return {
        "source": "USGS Earthquake API",
        "status": "ACCESSIBLE",
        "total_records": total_records,
        "null_counts": null_counts,
        "null_percentages": {k: (v / max(1, total_records)) * 100 for k, v in null_counts.items()},
        "metrics": {
            "min_magnitude": min_mag,
            "max_magnitude": max_mag,
            "avg_magnitude": round(avg_mag, 2) if avg_mag else None,
            "earliest_event_utc": min_date,
            "latest_event_utc": max_date
        },
        "spatial_resolution": "Point (Latitude, Longitude, Depth)",
        "temporal_resolution": "Real-Time (Millisecond Timestamps)"
    }

def profile_gdacs_data(raw_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/gdacs_alerts.json"):
    if not os.path.exists(raw_path):
        return {"status": "FILE_NOT_FOUND", "path": raw_path}
        
    with open(raw_path, 'r', encoding='utf-8') as f:
        alerts = json.load(f)
        
    total_records = len(alerts)
    null_counts = {
        "title": 0,
        "event_type": 0,
        "alert_level": 0,
        "country": 0,
        "point": 0
    }
    
    event_types = {}
    alert_levels = {}
    
    for a in alerts:
        for k in null_counts:
            if not a.get(k):
                null_counts[k] += 1
                
        etype = a.get('event_type') or "UNKNOWN"
        event_types[etype] = event_types.get(etype, 0) + 1
        
        alevel = a.get('alert_level') or "UNKNOWN"
        alert_levels[alevel] = alert_levels.get(alevel, 0) + 1
        
    return {
        "source": "GDACS Disaster Alert API",
        "status": "ACCESSIBLE",
        "total_records": total_records,
        "null_counts": null_counts,
        "null_percentages": {k: (v / max(1, total_records)) * 100 for k, v in null_counts.items()},
        "event_type_distribution": event_types,
        "alert_level_distribution": alert_levels,
        "spatial_resolution": "Point / Country Polygon",
        "temporal_resolution": "Near Real-Time (Daily Alerts)"
    }

def run_profiling(report_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/profiling_report.json"):
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    report = {
        "profiled_at_utc": datetime.utcnow().isoformat(),
        "datasets": {
            "usgs_earthquakes": profile_usgs_data(),
            "gdacs_alerts": profile_gdacs_data()
        }
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"Profiling report written to: {report_path}")
    return report

if __name__ == "__main__":
    run_profiling()
