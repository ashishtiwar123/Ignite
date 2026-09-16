import json
import urllib.request
import os
import xml.etree.ElementTree as ET

def fetch_gdacs_alerts(output_path="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data/raw/gdacs_alerts.json"):
    """
    Fetches real disaster alerts (Floods, Cyclones, Wildfires, Earthquakes) from GDACS RSS API.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    url = "https://www.gdacs.org/xml/rss.xml"
    print(f"Fetching GDACS RSS data from: {url}")
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            xml_data = response.read().decode('utf-8')
            root = ET.fromstring(xml_data)
            
            alerts = []
            channel = root.find('channel')
            if channel is not None:
                for item in channel.findall('item'):
                    title = item.findtext('title')
                    description = item.findtext('description')
                    pub_date = item.findtext('pubDate')
                    link = item.findtext('link')
                    
                    # Extract GeoRSS lat/lon if available
                    point = item.findtext('{http://www.georss.org/georss}point')
                    event_type = item.findtext('{http://www.gdacs.org}eventtype')
                    alert_level = item.findtext('{http://www.gdacs.org}alertlevel')
                    country = item.findtext('{http://www.gdacs.org}country')
                    
                    alerts.append({
                        "title": title,
                        "description": description,
                        "pub_date": pub_date,
                        "link": link,
                        "point": point,
                        "event_type": event_type,
                        "alert_level": alert_level,
                        "country": country
                    })
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, indent=2)
            print(f"Successfully downloaded {len(alerts)} GDACS alerts to {output_path}")
            return alerts
    except Exception as e:
        print(f"Failed to fetch GDACS data: {e}")
        return None

if __name__ == "__main__":
    fetch_gdacs_alerts()
