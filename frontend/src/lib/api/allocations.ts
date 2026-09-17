import { apiRequest } from "./client";
import type { AllocationRecord, OptimizationRequest, OptimizationResponse } from "./types";

export async function optimizeAllocations(request: OptimizationRequest): Promise<OptimizationResponse> {
  return apiRequest<OptimizationResponse>("/allocations/optimize", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getIncidentAllocations(incidentId: string): Promise<AllocationRecord[]> {
  return apiRequest<AllocationRecord[]>(`/allocations/incident/${incidentId}`);
}
