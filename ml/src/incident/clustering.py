from typing import List, Dict, Any, Optional
from datetime import datetime
from ml.src.incident.schemas import Report, IncidentCandidate
from ml.src.incident.matching import match_reports
import uuid

def cluster_reports(reports: List[Report]) -> List[IncidentCandidate]:
    """
    Cluster reports into IncidentCandidates based on matching logic.
    Maintains provenance and handles conflicts explicitly.
    """
    clusters: List[List[Report]] = []
    
    for report in reports:
        matched = False
        for cluster in clusters:
            # Simple approach: compare with the first report in the cluster
            # In a real graph clustering, we might do connected components.
            match_result = match_reports(cluster[0], report)
            if match_result["decision"] == "MATCH":
                cluster.append(report)
                matched = True
                break
        if not matched:
            clusters.append([report])
            
    # Now build IncidentCandidates from clusters
    candidates = []
    for cluster in clusters:
        candidate = IncidentCandidate(
            hazard_type=cluster[0].hazard_type
        )
        
        sources = set()
        report_ids = []
        conflicts = []
        
        # We will collect all fields to find conflicts
        field_values = {}
        
        min_observed = None
        max_observed = None
        
        lat_sum = 0.0
        lon_sum = 0.0
        valid_coords = 0
        
        for r in cluster:
            sources.add(r.source)
            report_ids.append(r.report_id)
            
            # temporal
            if r.observed_at:
                if min_observed is None or r.observed_at < min_observed:
                    min_observed = r.observed_at
                if max_observed is None or r.observed_at > max_observed:
                    max_observed = r.observed_at
            
            # spatial
            if r.latitude is not None and r.longitude is not None:
                lat_sum += r.latitude
                lon_sum += r.longitude
                valid_coords += 1
                
            # Conflict tracking (e.g., magnitude)
            if r.magnitude is not None:
                if 'magnitude' not in field_values:
                    field_values['magnitude'] = []
                field_values['magnitude'].append({"source": r.source, "value": r.magnitude})
                
        # Handle conflicts and canonical attributes
        canonical_attrs = {}
        for field, values in field_values.items():
            unique_vals = {v['value'] for v in values}
            if len(unique_vals) > 1:
                conflicts.append({"field": field, "values": values})
                # Do not silently pick one if there is a conflict
            else:
                canonical_attrs[field] = values[0]['value']
                
        candidate.report_ids = report_ids
        candidate.source_count = len(sources)
        candidate.source_list = list(sources)
        candidate.first_observed_at = min_observed
        candidate.last_observed_at = max_observed
        
        if valid_coords > 0:
            candidate.centroid_latitude = lat_sum / valid_coords
            candidate.centroid_longitude = lon_sum / valid_coords
            candidate.location_precision = "POINT"
        else:
            candidate.location_precision = "UNKNOWN"
            
        candidate.conflicting_information = conflicts
        candidate.canonical_attributes = canonical_attrs
        candidate.raw_report_count = len(cluster)
        
        # Calculate matching confidence and reasons if >1 report
        if len(cluster) > 1:
            match_res = match_reports(cluster[0], cluster[1]) # basic pairwise for summary
            candidate.matching_confidence = match_res["match_score"]
            candidate.matching_reasons = match_res["reasons"]
        
        candidates.append(candidate)
        
    return candidates
