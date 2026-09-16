import os
import json
import urllib.request
import pandas as pd

WB_URL = "http://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&per_page=20000&date=2000:2025"
WB_DEN_URL = "http://api.worldbank.org/v2/country/all/indicator/EN.POP.DNST?format=json&per_page=20000&date=2000:2025"
WB_URB_URL = "http://api.worldbank.org/v2/country/all/indicator/SP.URB.TOTL.IN.ZS?format=json&per_page=20000&date=2000:2025"
WB_POV_URL = "http://api.worldbank.org/v2/country/all/indicator/SI.POV.NAHC?format=json&per_page=20000&date=2000:2025"

RAW_DIR = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/worldbank/"
os.makedirs(RAW_DIR, exist_ok=True)

def download_indicator(url, filename):
    filepath = os.path.join(RAW_DIR, filename)
    print(f"Downloading {url} to {filepath}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
        out_file.write(response.read())
    print(f"Successfully saved {filepath} ({os.path.getsize(filepath)} bytes).")

if __name__ == "__main__":
    download_indicator(WB_URL, "worldbank_population.json")
    download_indicator(WB_DEN_URL, "worldbank_pop_density.json")
    download_indicator(WB_URB_URL, "worldbank_urban_pct.json")
    download_indicator(WB_POV_URL, "worldbank_poverty_pct.json")
