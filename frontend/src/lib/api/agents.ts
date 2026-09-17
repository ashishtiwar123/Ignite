import { apiRequest } from "./client";
import type {
  AgentRunRequest,
  AgentRunResponse,
  AgentResumeRequest,
  ExecutionRequest,
  ExecutionResponse,
  ReassessmentRequest,
  ReassessmentResponse,
} from "./types";

export async function runAgent(request: AgentRunRequest): Promise<AgentRunResponse> {
  return apiRequest<AgentRunResponse>("/agents/run", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function submitReview(
  threadId: string,
  request: AgentResumeRequest
): Promise<AgentRunResponse> {
  return apiRequest<AgentRunResponse>(`/agents/review/${threadId}`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function executeProposal(
  threadId: string,
  request: ExecutionRequest = {}
): Promise<ExecutionResponse> {
  return apiRequest<ExecutionResponse>(`/agents/execute/${threadId}`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function reassessIncident(
  threadId: string,
  request: ReassessmentRequest
): Promise<ReassessmentResponse> {
  return apiRequest<ReassessmentResponse>(`/agents/reassess/${threadId}`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}
