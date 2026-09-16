import os
import json
import hashlib
from datetime import datetime

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def inspect_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            row_count = len(data)
            cols = list(data[0].keys()) if row_count > 0 and isinstance(data[0], dict) else []
            first_5 = data[:5]
            last_5 = data[-5:]
        elif isinstance(data, dict):
            if "features" in data:
                features = data.get("features", [])
                row_count = len(features)
                cols = list(features[0].keys()) if row_count > 0 else []
                first_5 = features[:5]
                last_5 = features[-5:]
            else:
                row_count = len(data.keys())
                cols = list(data.keys())
                first_5 = list(data.items())[:5]
                last_5 = list(data.items())[-5:]
        else:
            row_count = 0
            cols = []
            first_5 = []
            last_5 = []
            
        return {
            "row_count": row_count,
            "columns": cols,
            "first_5_sample": first_5,
            "last_5_sample": last_5
        }
    except Exception as e:
        return {"error": str(e), "row_count": 0, "columns": []}

def run_inventory_audit(data_dir="c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/data"):
    inventory = []
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, data_dir)
            size_bytes = os.path.getsize(filepath)
            mtime = datetime.utcfromtimestamp(os.path.getmtime(filepath)).isoformat()
            sha256 = compute_sha256(filepath)
            
            file_type = os.path.splitext(file)[1]
            
            inspection = {}
            if file_type == ".json":
                inspection = inspect_json_file(filepath)
                
            inventory.append({
                "filename": file,
                "relative_path": rel_path.replace("\\", "/"),
                "full_path": filepath.replace("\\", "/"),
                "extension": file_type,
                "size_bytes": size_bytes,
                "modified_utc": mtime,
                "sha256": sha256,
                "row_count": inspection.get("row_count", 0),
                "column_sample": inspection.get("columns", [])
            })
            
    out_path = "c:/Users/Ashish Tiwari/OneDrive/Desktop/Ignite/ml/reports/raw_data_inventory.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"audited_at_utc": datetime.utcnow().isoformat(), "files": inventory}, f, indent=2)
        
    print(f"Inventory audit completed. Recorded {len(inventory)} files in {out_path}")
    return inventory

if __name__ == "__main__":
    run_inventory_audit()
