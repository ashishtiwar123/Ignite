import json
import urllib.request
import os
from datetime import datetime, timedelta

def fetch_usgs_earthquakes(min_magnitude=4.5, days=30, output_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/usgs_earthquakes.json"):
    """
    Fetches real seismic event data from USGS API for the past N days.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    url = (
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?"
        f"format=geojson&starttime={start_time.strftime('%Y-%m-%d')}"
        f"&endtime={end_time.strftime('%Y-%m-%d')}"
        f"&minmagnitude={min_magnitude}&limit=500"
    )
    
    print(f"Fetching USGS data from: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"Successfully downloaded {len(data.get('features', []))} seismic events to {output_path}")
            return data
    except Exception as e:
        print(f"Failed to fetch USGS data: {e}")
        return None

if __name__ == "__main__":
    fetch_usgs_earthquakes()
