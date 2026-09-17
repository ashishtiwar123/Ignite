import { apiRequest } from "./client";
import type { ReportCreate, ReportResponse } from "./types";

export async function createReport(data: ReportCreate): Promise<ReportResponse> {
  return apiRequest<ReportResponse>("/reports", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
