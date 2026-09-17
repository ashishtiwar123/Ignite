import { apiRequest } from "./client";
import type { ResourceRecord } from "./types";

export async function getResources(locationId?: string): Promise<ResourceRecord[]> {
  const query = locationId ? `?location_id=${encodeURIComponent(locationId)}` : "";
  return apiRequest<ResourceRecord[]>(`/resources${query}`);
}

export async function upsertResource(data: Partial<ResourceRecord>): Promise<ResourceRecord> {
  return apiRequest<ResourceRecord>("/resources", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
