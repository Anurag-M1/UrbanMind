/* Shared UrbanMind frontend types. */

export interface IntersectionState {
  id: string;
  name: string;
  lat: number;
  lng: number;
  ew_green: boolean;
  ew_phase_seconds: number;
  ew_green_duration: number;
  ns_green_duration: number;
  density_ew: number;
  density_ns: number;
  queue_ew: number;
  queue_ns: number;
  wait_time_avg: number;
  override: boolean;
  fault: boolean;
  last_updated: string;
}

export interface SystemStats {
  total_vehicles_detected: number;
  avg_wait_time_network: number;
  webster_last_recalc: string;
  emissions_saved_pct: number;
}

export interface EmergencyVehicle {
  id: string;
  type: "ambulance" | "fire" | "police";
  lat: number;
  lng: number;
  speed: number;
  heading: number;
  active: boolean;
  corridor_intersections: string[];
}

export interface EmergencyEvent {
  id: string;
  vehicle_id: string;
  vehicle_type: "ambulance" | "fire" | "police";
  event_type: string;
  intersection_id: string | null;
  corridor_intersections: string[];
  duration_seconds: number | null;
  details: string;
  timestamp: string;
}

export interface Alert {
  id: string;
  kind: "fault" | "warning" | "info" | "emergency";
  title: string;
  message: string;
  timestamp: string;
}

export interface ApiEnvelope<T> {
  data: T;
  timestamp: string;
}

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
  intersection_id?: string | null;
}

export interface SummaryData {
  peak_hour_identified: string;
  best_intersection: string;
  worst_intersection: string;
  total_emergency_events: number;
  cumulative_emissions_saved: number;
}

export interface DashboardMessage {
  type: "state_update" | "emergency_activated" | "fault";
  intersections?: IntersectionState[];
  emergency_active?: boolean;
  active_vehicles?: EmergencyVehicle[];
  system_stats?: SystemStats;
  vehicle?: EmergencyVehicle;
  corridor?: string[];
  intersection_id?: string;
  message?: string;
  timestamp: string;
}
