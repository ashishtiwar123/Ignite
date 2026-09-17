import type {
  IncidentSummaryResponse,
  AssessmentResponse,
  IncidentGovernanceResponse,
  AllocationRecord,
} from "./api/types";

export const isDemoMode = (): boolean => {
  const mode = import.meta.env.VITE_DEMO_MODE;
  if (mode === "false" || mode === "0") return false;
  return true;
};

export const DEMO_INCIDENT_ID = "56862ef4-18f4-4bfc-bcf6-795850362551";
export const DEMO_THREAD_ID = "thread-mumbai-demo-001";
export const DEMO_OPT_RUN_ID = "opt-mumbai-demo-001";

export interface DemoReport {
  id: string;
  source: string;
  time: string;
  message: string;
}

export const DEMO_REPORTS: DemoReport[] = [
  {
    id: "rep-001",
    source: "Mumbai Municipal Emergency Cell",
    time: "10:42 AM",
    message: "Severe waterlogging reported across low-lying residential areas. Multiple families require evacuation.",
  },
  {
    id: "rep-002",
    source: "Field Response Unit",
    time: "10:51 AM",
    message: "Ground teams report rising water levels near the command area. Approximately 1200 residents affected.",
  },
  {
    id: "rep-003",
    source: "City Hospital Coordination Desk",
    time: "11:03 AM",
    message: "Hospital access is partially obstructed. Medical evacuation support and emergency supplies are required.",
  },
  {
    id: "rep-004",
    source: "NGO Relief Network",
    time: "11:17 AM",
    message: "Emergency drinking water and food supplies requested for displaced families.",
  },
];

export const DEMO_INCIDENTS: IncidentSummaryResponse[] = [
  {
    incident_id: DEMO_INCIDENT_ID,
    hazard_type: "Flood",
    status: "VERIFIED",
    location_text: "Mumbai Command Area",
    verification_status: "VERIFIED",
    severity_class: "HIGH",
    report_count: 4,
    first_observed_at: new Date().toISOString(),
    centroid_latitude: 19.0701,
    centroid_longitude: 72.8792,
  },
  {
    incident_id: "inc-mumbai-002",
    hazard_type: "Flood",
    status: "CANDIDATE",
    location_text: "Kurla West Zone",
    verification_status: "CANDIDATE",
    severity_class: "HIGH",
    report_count: 2,
    first_observed_at: new Date().toISOString(),
    centroid_latitude: 19.055,
    centroid_longitude: 72.87,
  },
  {
    incident_id: "inc-mumbai-003",
    hazard_type: "Flood",
    status: "CANDIDATE",
    location_text: "Bandra East Ward",
    verification_status: "CANDIDATE",
    severity_class: "MODERATE",
    report_count: 1,
    first_observed_at: new Date().toISOString(),
    centroid_latitude: 19.075,
    centroid_longitude: 72.885,
  },
  {
    incident_id: "inc-mumbai-004",
    hazard_type: "Flood",
    status: "CANDIDATE",
    location_text: "Sion Lowlands",
    verification_status: "CANDIDATE",
    severity_class: "MODERATE",
    report_count: 1,
    first_observed_at: new Date().toISOString(),
    centroid_latitude: 19.065,
    centroid_longitude: 72.895,
  },
];

export const DEMO_ASSESSMENT: AssessmentResponse = {
  incident_id: DEMO_INCIDENT_ID,
  verification_status: "VERIFIED",
  severity: {
    status: "success",
    severity_class: "HIGH",
    severity_score: 7.8,
    assessment_method: "POLICY",
    policy_version: "FLOOD_POLICY_V1",
    affected_population: 1200,
    evidence_coverage: 1.0,
    contributing_factors: {
      water_level: "Rising",
      hospital_access: "Disrupted",
      displacement: "High",
    },
    risk_indicators: [
      "Rising water levels",
      "Hospital access disruption",
      "Residential displacement",
      "Emergency water requirement",
    ],
  },
  trajectory: {
    status: "calculated",
    trajectory: "WORSENING",
    confidence: 0.92,
  },
  needs: {
    status: "calculated",
    water_liters: 7500,
    food_cereal_mt: 0.225,
    medical_support: "HIGH",
    search_and_rescue: "HIGH",
    shelter_units: 240,
    emergency_transport_vehicles: 6,
  },
  priority: {
    status: "calculated",
    priority_score: 82,
    priority_level: "CRITICAL",
    reasoning: [
      "Verified disaster",
      "High severity (7.8 / 10)",
      "Worsening trajectory",
      "1,200 affected population",
      "Medical access disruption",
      "Emergency resource requirements",
    ],
  },
};

export const DEMO_GOVERNANCE: IncidentGovernanceResponse = {
  incident_id: DEMO_INCIDENT_ID,
  thread_id: DEMO_THREAD_ID,
  optimization_run_id: DEMO_OPT_RUN_ID,
  approval_status: "PENDING",
  execution_status: "UNEXECUTED",
  execution_id: undefined,
  approval_id: "appr-mumbai-demo-001",
  deducted_resources: [],
  errors: [],
};

export const DEMO_ALLOCATIONS: AllocationRecord[] = [
  {
    allocation_id: "alloc-001",
    optimization_run_id: DEMO_OPT_RUN_ID,
    incident_id: DEMO_INCIDENT_ID,
    source_location_id: "Mumbai Central Depot",
    resource_type: "Portable Water",
    category: "WATER",
    unit: "L",
    quantity_allocated: 7500,
    quantity_requested: 7500,
    quantity_unmet: 0,
    solver_status: "OPTIMAL",
    created_at: new Date().toISOString(),
  },
  {
    allocation_id: "alloc-002",
    optimization_run_id: DEMO_OPT_RUN_ID,
    incident_id: DEMO_INCIDENT_ID,
    source_location_id: "Mumbai Relief Warehouse",
    resource_type: "Cereal / Food",
    category: "FOOD",
    unit: "MT",
    quantity_allocated: 0.225,
    quantity_requested: 0.225,
    quantity_unmet: 0,
    solver_status: "OPTIMAL",
    created_at: new Date().toISOString(),
  },
  {
    allocation_id: "alloc-003",
    optimization_run_id: DEMO_OPT_RUN_ID,
    incident_id: DEMO_INCIDENT_ID,
    source_location_id: "Emergency Medical Depot",
    resource_type: "Medical Kits",
    category: "MEDICAL",
    unit: "units",
    quantity_allocated: 120,
    quantity_requested: 120,
    quantity_unmet: 0,
    solver_status: "OPTIMAL",
    created_at: new Date().toISOString(),
  },
  {
    allocation_id: "alloc-004",
    optimization_run_id: DEMO_OPT_RUN_ID,
    incident_id: DEMO_INCIDENT_ID,
    source_location_id: "Rescue Unit Alpha",
    resource_type: "Rescue Boats",
    category: "RESCUE",
    unit: "units",
    quantity_allocated: 3,
    quantity_requested: 3,
    quantity_unmet: 0,
    solver_status: "OPTIMAL",
    created_at: new Date().toISOString(),
  },
  {
    allocation_id: "alloc-005",
    optimization_run_id: DEMO_OPT_RUN_ID,
    incident_id: DEMO_INCIDENT_ID,
    source_location_id: "Shelter Depot",
    resource_type: "Family Shelter Kits",
    category: "SHELTER",
    unit: "units",
    quantity_allocated: 240,
    quantity_requested: 240,
    quantity_unmet: 0,
    solver_status: "OPTIMAL",
    created_at: new Date().toISOString(),
  },
];

export const DEMO_RESOURCES = [
  { type: "Portable Water", available: "12,000 L", category: "WATER" },
  { type: "Food / Cereal", available: "0.8 MT", category: "FOOD" },
  { type: "Medical Kits", available: "320 units", category: "MEDICAL" },
  { type: "Family Shelter Kits", available: "300 units", category: "SHELTER" },
  { type: "Rescue Boats", available: "8 units", category: "RESCUE" },
  { type: "Emergency Vehicles", available: "12 units", category: "TRANSPORT" },
];

export const DEMO_MAP_MARKERS = [
  { id: "mkr-1", name: "Incident Command Center", coords: [72.8792, 19.0701] as [number, number], type: "incident" },
  { id: "mkr-2", name: "Mumbai Central Depot", coords: [72.870, 19.055] as [number, number], type: "depot" },
  { id: "mkr-3", name: "Medical Support Unit", coords: [72.885, 19.075] as [number, number], type: "medical" },
  { id: "mkr-4", name: "Relief Warehouse", coords: [72.895, 19.065] as [number, number], type: "warehouse" },
  { id: "mkr-5", name: "Rescue Staging Area", coords: [72.875, 19.085] as [number, number], type: "staging" },
];

export const DEMO_KPI_STATS = {
  activeIncidents: 4,
  criticalIncidents: 1,
  peopleAffected: 1200,
  resourcesRequiredCategories: 5,
  pendingApprovals: 1,
  resourcesAvailableUnits: "1,200+ units",
};
