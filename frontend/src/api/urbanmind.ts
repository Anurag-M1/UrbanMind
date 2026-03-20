/* UrbanMind REST API client helpers. */

import type {
  ApiEnvelope,
  EmergencyEvent,
  EmergencyVehicle,
  IntersectionState,
  SummaryData,
  TimeSeriesPoint,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function fetchIntersections(): Promise<IntersectionState[]> {
  const response = await request<ApiEnvelope<IntersectionState[]>>("/signals/intersections");
  return response.data;
}

export async function fetchWaitTimeSeries(intersectionId?: string): Promise<TimeSeriesPoint[]> {
  const query = intersectionId ? `?intersection_id=${intersectionId}` : "";
  const response = await request<ApiEnvelope<TimeSeriesPoint[]>>(`/analytics/wait-times${query}`);
  return response.data;
}

export async function fetchFlowSeries(intersectionId?: string): Promise<TimeSeriesPoint[]> {
  const query = intersectionId ? `?intersection_id=${intersectionId}` : "";
  const response = await request<ApiEnvelope<TimeSeriesPoint[]>>(`/analytics/flow${query}`);
  return response.data;
}

export async function fetchEmergencyHistory(): Promise<EmergencyEvent[]> {
  const response = await request<ApiEnvelope<EmergencyEvent[]>>("/emergency/history");
  return response.data;
}

export async function fetchAnalyticsSummary(): Promise<SummaryData> {
  const response = await request<ApiEnvelope<SummaryData>>("/analytics/summary");
  return response.data;
}

export async function simulateEmergency(): Promise<EmergencyVehicle> {
  const response = await request<ApiEnvelope<EmergencyVehicle>>("/emergency/simulate", {
    method: "POST",
  });
  return response.data;
}
