// UrbanMind TypeScript Types

export interface IntersectionState {
  id: string;
  name: string;
  lat: number;
  lng: number;
  address: string;
  ew_green: boolean;
  ew_phase_seconds: number;
  ew_green_duration: number;
  ns_green_duration: number;
  cycle_length: number;
  density_ew: number;
  density_ns: number;
  queue_ew_meters: number;
  queue_ns_meters: number;
  wait_time_avg: number;
  wait_time_history: number[];
  throughput_per_hour: number;
  override: boolean;
  override_reason: string;
  fault: boolean;
  last_updated: string;
  webster_last_calc: string;
  total_vehicles_processed: number;
  timer?: number;
}

export interface VehicleDetection {
  frame_number: number;
  class_name: string;
  confidence: number;
  bbox: number[];
  lane: string;
  intersection_id: string;
}

export interface VideoFrame {
  frame_number: number;
  timestamp_seconds: number;
  detections: VehicleDetection[];
  ew_count: number;
  ns_count: number;
  annotated_image_b64: string;
}

export interface VideoAnalysisResult {
  video_id: string;
  filename: string;
  duration_seconds: number;
  total_frames: number;
  fps: number;
  frames_processed: number;
  intersections_detected: string[];
  vehicle_counts: Record<string, number>;
  lane_density: Record<string, number>;
  recommended_timings: {
    ew_green: number;
    ns_green: number;
    cycle_length: number;
    y_ew?: number;
    y_ns?: number;
    Y?: number;
    flow_ew_per_hour?: number;
    flow_ns_per_hour?: number;
  };
  detection_frames: VideoFrame[];
  processing_time_seconds: number;
  status: 'processing' | 'complete' | 'error';
  error_message?: string;
  progress_pct?: number;
}

export interface EmergencyVehicle {
  id: string;
  type: 'ambulance' | 'fire' | 'police';
  lat: number;
  lng: number;
  speed_kmh: number;
  heading_degrees: number;
  active: boolean;
  activated_at: string;
  corridor_intersections: string[];
  current_intersection_idx: number;
  eta_seconds: number;
}

export interface EmergencyEvent {
  id: string;
  vehicle_id: string;
  vehicle_type: string;
  activated_at: string;
  deactivated_at: string | null;
  intersections_cleared: number;
  response_time_saved_seconds: number;
}

export interface SystemStats {
  total_vehicles: number;
  network_avg_wait: number;
  webster_countdown: number;
  active_emergencies: number;
  emissions_saved_pct: number;
  uptime_seconds: number;
  webster_recalculations?: number;
  last_vision_update?: string;
  last_detection_count?: number;
  live_vision_status?: string;
  last_siren_detected_at?: string;
  last_siren_vehicle_type?: string;
  siren_detection_confidence?: number;
  siren_detection_status?: string;
}

export interface WSMessage {
  type: string;
  timestamp?: string;
  intersections?: IntersectionState[];
  system?: SystemStats;
  stats?: Partial<SystemStats>;
  emergencies?: EmergencyVehicle[];
  vehicle?: EmergencyVehicle;
  corridor?: IntersectionState[];
  message?: string;
  vehicle_id?: string;
  lat?: number;
  lng?: number;
  speed_kmh?: number;
  heading?: number;
  eta_seconds?: number;
  corridor_progress?: string;
  intersection_id?: string;
  trigger_source?: string;
  status?: string;
  video_id?: string;
  vehicle_counts?: Record<string, number>;
  recommended_timings?: Record<string, number>;
}

export interface AnalyticsSummary {
  network_avg_wait_seconds: number;
  baseline_wait_seconds: number;
  wait_reduction_pct: number;
  total_vehicles_processed: number;
  total_emergency_events: number;
  emissions_saved_pct: number;
  best_intersection: { id: string; name: string; avg_wait: number };
  worst_intersection: { id: string; name: string; avg_wait: number };
  peak_density_intersection: { id: string; name: string; density: number };
  webster_recalculations_today: number;
  uptime_hours: number;
}

export interface FlowSeriesEntry {
  hour: number;
  ew_flow: number;
  ns_flow: number;
  total: number;
}
