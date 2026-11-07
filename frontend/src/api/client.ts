/**
 * NileOps Frontend API Client
 */

import { HealthCheckResponse } from "../types";

const API_BASE = "/api";

export async function fetchHealth(): Promise<HealthCheckResponse> {
  const response = await fetch("/health");
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

export async function fetchApiStatus(): Promise<any> {
  const response = await fetch(`${API_BASE}/v1/status`);
  if (!response.ok) {
    throw new Error(`API status check failed: ${response.status}`);
  }
  return response.json();
}
