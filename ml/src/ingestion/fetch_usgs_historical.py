import json
import urllib.request
import os
from datetime import datetime, timedelta

def fetch_usgs_historical_earthquakes(min_magnitude=5.5, start_year=2018, output_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/usgs/usgs_historical_earthquakes.json"):
    """
    Fetches multi-year historical earthquake events (Mw >= 5.5) from USGS API.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    end_time = datetime.utcnow().strftime('%Y-%m-%d')
    start_time = f"{start_year}-01-01"
    
    url = (
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?"
        f"format=geojson&starttime={start_time}"
        f"&endtime={end_time}"
        f"&minmagnitude={min_magnitude}&limit=2000"
    )
    
    print(f"Fetching multi-year USGS historical data from: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            features = data.get('features', [])
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"Successfully downloaded {len(features)} historical seismic events ({start_year}-Present) to {output_path}")
            return data
    except Exception as e:
        print(f"Failed to fetch historical USGS data: {e}")
        return None

if __name__ == "__main__":
    fetch_usgs_historical_earthquakes()
