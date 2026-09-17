import { apiRequest } from "./client";
import type { IncidentSummaryResponse, AssessmentResponse } from "./types";

export async function getIncidents(): Promise<IncidentSummaryResponse[]> {
  return apiRequest<IncidentSummaryResponse[]>("/incidents");
}

export async function getIncidentAssessment(incidentId: string): Promise<AssessmentResponse> {
  return apiRequest<AssessmentResponse>(`/incidents/${incidentId}/assessment`);
}
