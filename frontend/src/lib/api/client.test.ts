import { describe, it, expect, vi } from "vitest";
import { API_BASE_URL, ApiError, apiRequest } from "./client";

describe("Frontend API Client", () => {
  it("uses default API base URL when VITE_API_BASE_URL is unconfigured", () => {
    expect(API_BASE_URL).toContain("http://localhost:8001");
  });

  it("constructs ApiError correctly", () => {
    const err = new ApiError(404, "Incident not found");
    expect(err.status).toBe(404);
    expect(err.detail).toBe("Incident not found");
    expect(err.message).toContain("404");
  });
});
