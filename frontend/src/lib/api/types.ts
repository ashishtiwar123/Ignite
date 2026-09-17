/**
 * Type-safe API contracts mirroring FastAPI backend Pydantic models.
 */

export interface ReportCreate {
  source?: string;
  source_record_id?: string;
  hazard_type?: string;
  location_name?: string;
  latitude?: number | null;
  longitude?: number | null;
  magnitude?: number | null;
  depth?: number | null;
  wind_speed?: number | null;
  pressure?: number | null;
  affected_population?: number | null;
  displaced_population?: number | null;
  observed_at?: string | null;
  raw_text?: string | null;
  raw_payload_reference?: Record<string, any> | null;
}

export interface ReportResponse {
  report_id: string;
  status: string;
  message: string;
}

export interface IncidentSummaryResponse {
  incident_id: string;
  hazard_type: string;
  status: string;
  location_text?: string;
  verification_status?: string;
  severity_class?: string;
  report_count?: number;
  first_observed_at: string;
  centroid_latitude: number | null;
  centroid_longitude: number | null;
}

export interface AssessmentRecord {
  assessment_id: string;
  incident_id: string;
  parent_assessment_id?: string | null;
  reassessment_reason?: string | null;
  idempotency_key?: string | null;
  verification_status?: string | null;
  severity_status?: string | null;
  severity?: Record<string, any> | null;
  trajectory_status?: string | null;
  trajectory?: Record<string, any> | null;
  priority_level?: string | null;
  priority_score?: number | null;
  severity_model_version?: string | null;
  verification_policy_version?: string | null;
  trajectory_policy_version?: string | null;
  needs_policy_version?: string | null;
  priority_policy_version?: string | null;
  assessed_at: string;
  created_at: string;
}

export interface AssessmentResponse {
  incident_id: string;
  verification_status: string;
  severity: Record<string, any>;
  trajectory: Record<string, any>;
  needs: Record<string, any>;
  priority: Record<string, any>;
}

export interface UnsupportedHazardResponse {
  hazard_type: string;
  message: string;
}

export interface NeedRecord {
  need_id: string;
  incident_id: string;
  assessment_id?: string | null;
  resource_type: string;
  category?: string | null;
  quantity?: number | null;
  unit?: string | null;
  urgency?: string | null;
  status?: string | null;
  time_window?: string | null;
  rule_id?: string | null;
  policy_version?: string | null;
  calculation_basis?: Record<string, any> | null;
  provenance?: Record<string, any> | null;
  explanation?: string | null;
  created_at: string;
}

export interface ResourceRecord {
  resource_id: string;
  location_id: string;
  resource_type: string;
  category?: string | null;
  quantity_available: number;
  unit: string;
  provenance?: Record<string, any> | null;
  updated_at: string;
  created_at: string;
}

export interface AllocationRecord {
  allocation_id: string;
  optimization_run_id?: string | null;
  previous_optimization_run_id?: string | null;
  incident_id: string;
  requirement_id?: string | null;
  source_location_id: string;
  resource_type: string;
  category?: string | null;
  unit: string;
  quantity_allocated: number;
  quantity_requested: number;
  quantity_unmet: number;
  priority_score?: number | null;
  solver_status?: string | null;
  explanation?: string | null;
  created_at: string;
}

export interface OptimizationRequest {
  incident_ids: string[];
  optimization_run_id?: string | null;
}

export interface OptimizationResponse {
  optimization_run_id?: string | null;
  solver_status: string;
  allocations: AllocationRecord[];
  total_requested: number;
  total_allocated: number;
  total_unmet: number;
  objective_value: number;
  generated_at: string;
}

export interface AgentRunRequest {
  incident_id?: string | null;
  run_id?: string | null;
  raw_reports?: string[];
}

export interface AgentRunResponse {
  run_id?: string | null;
  thread_id?: string | null;
  status: string;
  human_approval_state: string;
  errors: string[];
}

export interface ApprovalRecord {
  approval_id: string;
  incident_id: string;
  thread_id?: string | null;
  optimization_run_id?: string | null;
  action_id?: string | null;
  status: string;
  reviewer_id?: string | null;
  reason?: string | null;
  decided_at?: string | null;
  created_at: string;
}

export interface AgentResumeRequest {
  decision: "APPROVED" | "REJECTED" | "REVISION_REQUESTED";
  reason?: string | null;
}

export interface ActionRecord {
  action_id: string;
  execution_id?: string | null;
  incident_id: string;
  optimization_run_id?: string | null;
  approval_id?: string | null;
  action_type: string;
  status: string;
  description?: string | null;
  payload?: Record<string, any> | null;
  executed_by?: string | null;
  executed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExecutionRequest {
  optimization_run_id?: string | null;
  incident_id?: string | null;
  executor_id?: string | null;
  approved?: boolean | null;
}

export interface DeductedResourceItem {
  resource_id: string;
  location_id: string;
  resource_type: string;
  category?: string | null;
  quantity_deducted: number;
  unit: string;
  previous_quantity: number;
  new_quantity: number;
}

export interface ExecutionResponse {
  execution_id: string;
  status: string; // EXECUTED, ALREADY_EXECUTED, FAILED, NOT_APPROVED, INVALID_PROPOSAL
  optimization_run_id?: string | null;
  approval_id?: string | null;
  incident_id?: string | null;
  deducted_resources: DeductedResourceItem[];
  errors: string[];
}

export interface IncidentGovernanceResponse {
  incident_id: string;
  thread_id?: string | null;
  optimization_run_id?: string | null;
  approval_status: string;
  execution_status: string;
  execution_id?: string | null;
  approval_id?: string | null;
  deducted_resources: DeductedResourceItem[];
  errors: string[];
}

export interface AssessmentDiff {
  parent_assessment_id?: string | null;
  current_assessment_id: string;
  severity_changed: boolean;
  previous_severity?: string | null;
  current_severity?: string | null;
  previous_severity_score?: number | null;
  current_severity_score?: number | null;
  trajectory_changed: boolean;
  previous_trajectory?: string | null;
  current_trajectory?: string | null;
  priority_changed: boolean;
  previous_priority_level?: string | null;
  current_priority_level?: string | null;
  previous_priority_score?: number | null;
  current_priority_score?: number | null;
  priority_score_delta: number;
  needs_changed: boolean;
  added_needs: Record<string, any>[];
  increased_needs: Record<string, any>[];
  decreased_needs: Record<string, any>[];
  resolved_needs: Record<string, any>[];
}

export interface AllocationDeltaItem {
  resource_type: string;
  category?: string | null;
  source_location_id: string;
  unit: string;
  change_type: "ADDED" | "INCREASED" | "DECREASED" | "REMOVED" | "UNCHANGED";
  previous_quantity: number;
  new_quantity: number;
  delta_quantity: number;
  explanation?: string | null;
}

export interface AllocationDiff {
  baseline_optimization_run_id?: string | null;
  new_optimization_run_id?: string | null;
  deltas: AllocationDeltaItem[];
  total_previous_allocated: number;
  total_new_allocated: number;
  net_allocated_delta: number;
  has_meaningful_change: boolean;
}

export interface ReassessmentRequest {
  new_reports: string[];
  run_id?: string | null;
  reassessment_reason?: string | null;
}

export interface ReassessmentResponse {
  run_id?: string | null;
  thread_id: string;
  incident_id?: string | null;
  previous_assessment_id?: string | null;
  current_assessment_id?: string | null;
  assessment_diff?: AssessmentDiff | null;
  reallocation_decision_status: string;
  reallocation_required: boolean;
  new_optimization_run_id?: string | null;
  allocation_diff?: AllocationDiff | null;
  human_approval_state: string;
  status: string;
  errors: string[];
}
