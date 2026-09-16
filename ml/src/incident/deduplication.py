from typing import List, Dict, Any
from ml.src.incident.schemas import Report

def deduplicate_reports(reports: List[Report]) -> List[Report]:
    """
    Deterministically deduplicate reports based on exact matches of
    source and source_record_id.
    Retains the first encountered instance but can be extended to 
    merge provenance or take the freshest instance.
    """
    seen = set()
    deduplicated = []
    
    for report in reports:
        key = (report.source, report.source_record_id)
        if key not in seen:
            seen.add(key)
            deduplicated.append(report)
            
    return deduplicated
