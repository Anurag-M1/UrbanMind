import { create } from 'zustand';
import type { IntersectionState, SystemStats } from '../types';
import { deriveTrafficMetrics } from './traffic-metrics';
import { DEFAULT_CAMERA_NODE_ID } from './camera-nodes';

export interface Intersection {
  id: string;
  name: string;
  lat: number;
  lng: number;
  vehicles: number;
  avgWaitTime: number;
  status: 'optimal' | 'congested' | 'critical';
  nsSignal: 'red' | 'yellow' | 'green';
  ewSignal: 'red' | 'yellow' | 'green';
  nsQueueLength: number;
  ewQueueLength: number;
  nsDensity: number;
  ewDensity: number;
  phaseProgress: number;
}

export interface TrafficEvent {
  id: string;
  timestamp: number;
  type: 'alert' | 'warning' | 'info' | 'emergency' | 'success';
  title: string;
  description: string;
  intersectionId?: string;
}

export type CurrentPage =
  | 'dashboard'
  | 'footages'
  | 'analytics'
  | 'emergency'
  | 'roi'
  | 'settings'
  | 'video'
  | 'digital-twin';

export interface TrafficStore {
  // State
  intersections: Intersection[];
  selectedIntersection: string | null;
  emergencyMode: boolean;
  emergencyVehicleLocation: { lat: number; lng: number } | null;
  systemStatus: 'connected' | 'syncing' | 'fault';
  events: TrafficEvent[];
  currentPage: CurrentPage;
  selectedCameraNodeId: string;
  systemLoad: number;
  decisionLatency: number;
  optimizationEfficiency: number;
  nextRecalcSeconds: number;
  totalVehicles: number;
  emissionsSaved: number;
  activeIntersections: number;
  networkAvgWait: number;
  activeEmergencies: number;
  uptimeSeconds: number;
  websterRecalculations: number;
  lastVisionUpdate: string | null;
  liveVisionStatus: string;
  lastDetectionCount: number;
  systemSnapshot: Partial<SystemStats>;

  // Actions
  setSelectedIntersection: (id: string | null) => void;
  toggleEmergencyMode: () => void;
  setEmergencyVehicleLocation: (lat: number, lng: number) => void;
  updateSystemStatus: (status: 'connected' | 'syncing' | 'fault') => void;
  setCurrentPage: (page: CurrentPage) => void;
  setSelectedCameraNodeId: (nodeId: string) => void;
  updateIntersection: (id: string, data: Partial<Intersection>) => void;
  addEvent: (event: Omit<TrafficEvent, 'id' | 'timestamp'>) => void;
  clearOldEvents: () => void;
  updateSystemMetrics: (metrics: {
    systemLoad: number;
    decisionLatency: number;
    optimizationEfficiency: number;
    nextRecalcSeconds: number;
    totalVehicles: number;
    emissionsSaved: number;
    activeIntersections: number;
    networkAvgWait?: number;
    activeEmergencies?: number;
    uptimeSeconds?: number;
    websterRecalculations?: number;
    lastVisionUpdate?: string;
    liveVisionStatus?: string;
    lastDetectionCount?: number;
  }) => void;
  syncRealtimeState: (payload: {
    intersections?: IntersectionState[];
    system?: Partial<SystemStats>;
  }) => void;
  setIntersectionsFromBackend: (states: IntersectionState[]) => void;
  setSystemMetricsFromBackend: (stats: SystemStats) => void;
}

const mapIntersectionState = (state: IntersectionState): Intersection => ({
  id: state.id,
  name: state.name,
  lat: state.lat,
  lng: state.lng,
  vehicles: Math.round(state.total_vehicles_processed || 0),
  avgWaitTime: Math.round(state.wait_time_avg || 0),
  status: (
    state.wait_time_avg > 35 ? 'critical' : state.wait_time_avg > 22 ? 'congested' : 'optimal'
  ) as 'critical' | 'congested' | 'optimal',
  nsSignal: state.ew_green ? 'red' : 'green',
  ewSignal: state.ew_green ? 'green' : 'red',
  nsQueueLength: Math.round(state.queue_ns_meters || 0),
  ewQueueLength: Math.round(state.queue_ew_meters || 0),
  nsDensity: Math.round(state.density_ns || 0),
  ewDensity: Math.round(state.density_ew || 0),
  phaseProgress: state.cycle_length > 0 ? Math.round(((state.ew_phase_seconds % state.cycle_length) / state.cycle_length) * 100) : 0,
});

export const useTrafficStore = create<TrafficStore>((set) => ({
  // Initial state
  intersections: [],
  selectedIntersection: null,
  emergencyMode: false,
  emergencyVehicleLocation: null,
  systemStatus: 'syncing',
  events: [],
  currentPage: 'dashboard',
  selectedCameraNodeId: DEFAULT_CAMERA_NODE_ID,
  systemLoad: 0,
  decisionLatency: 18,
  optimizationEfficiency: 0,
  nextRecalcSeconds: 0,
  totalVehicles: 0,
  emissionsSaved: 0,
  activeIntersections: 0,
  networkAvgWait: 0,
  activeEmergencies: 0,
  uptimeSeconds: 0,
  websterRecalculations: 0,
  lastVisionUpdate: null,
  liveVisionStatus: 'Connecting...',
  lastDetectionCount: 0,
  systemSnapshot: {},

  // Actions
  setSelectedIntersection: (id) =>
    set({ selectedIntersection: id }),

  toggleEmergencyMode: () =>
    set((state) => ({ emergencyMode: !state.emergencyMode })),

  setEmergencyVehicleLocation: (lat, lng) =>
    set({ emergencyVehicleLocation: { lat, lng } }),

  updateSystemStatus: (status) =>
    set({ systemStatus: status }),

  setCurrentPage: (page) =>
    set({ currentPage: page }),

  setSelectedCameraNodeId: (nodeId) =>
    set({ selectedCameraNodeId: nodeId }),

  updateIntersection: (id, data) =>
    set((state) => ({
      intersections: state.intersections.map((i) =>
        i.id === id ? { ...i, ...data } : i
      ),
    })),

  addEvent: (event) =>
    set((state) => ({
      events: [
        {
          ...event,
          id: `event-${Date.now()}`,
          timestamp: Date.now(),
        },
        ...state.events,
      ].slice(0, 50), // Keep last 50 events
    })),

  clearOldEvents: () =>
    set((state) => ({
      events: state.events.filter(
        (e) => Date.now() - e.timestamp < 20 * 60 * 1000
      ),
    })),

  updateSystemMetrics: (metrics) =>
    set(metrics),

  syncRealtimeState: ({ intersections, system }) =>
    set((state) => {
      const mappedIntersections = intersections
        ? intersections.map(mapIntersectionState)
        : state.intersections;
      const systemSnapshot = { ...state.systemSnapshot, ...system };
      const metrics = deriveTrafficMetrics(mappedIntersections, systemSnapshot);
      const selectedIntersection = state.selectedIntersection && mappedIntersections.some((item) => item.id === state.selectedIntersection)
        ? state.selectedIntersection
        : mappedIntersections[0]?.id ?? null;

      return {
        intersections: mappedIntersections,
        selectedIntersection,
        totalVehicles: metrics.totalVehicles,
        networkAvgWait: metrics.networkAvgWait,
        nextRecalcSeconds: metrics.nextRecalcSeconds,
        activeIntersections: metrics.activeIntersections,
        activeEmergencies: metrics.activeEmergencies,
        emissionsSaved: metrics.emissionsSaved,
        systemLoad: metrics.systemLoad,
        decisionLatency: metrics.decisionLatency,
        optimizationEfficiency: metrics.optimizationEfficiency,
        uptimeSeconds: metrics.uptimeSeconds,
        websterRecalculations: metrics.websterRecalculations,
        lastVisionUpdate: systemSnapshot.last_vision_update || null,
        liveVisionStatus: systemSnapshot.live_vision_status || (mappedIntersections.length ? 'Synced' : state.liveVisionStatus),
        lastDetectionCount: systemSnapshot.last_detection_count || 0,
        systemSnapshot,
      };
    }),

  setIntersectionsFromBackend: (states) =>
    set((state) => {
      const mapped = states.map(mapIntersectionState);
      const metrics = deriveTrafficMetrics(mapped, state.systemSnapshot);
      const selectedIntersection = state.selectedIntersection && mapped.some((item) => item.id === state.selectedIntersection)
        ? state.selectedIntersection
        : mapped[0]?.id ?? null;

      return {
        intersections: mapped,
        selectedIntersection,
        totalVehicles: metrics.totalVehicles,
        networkAvgWait: metrics.networkAvgWait,
        activeIntersections: metrics.activeIntersections,
        emissionsSaved: metrics.emissionsSaved,
        systemLoad: metrics.systemLoad,
        decisionLatency: metrics.decisionLatency,
        optimizationEfficiency: metrics.optimizationEfficiency,
      };
    }),

  setSystemMetricsFromBackend: (stats) =>
    set((state) => {
      const systemSnapshot = { ...state.systemSnapshot, ...stats };
      const metrics = deriveTrafficMetrics(state.intersections, systemSnapshot);

      return {
        systemSnapshot,
        totalVehicles: metrics.totalVehicles,
        networkAvgWait: metrics.networkAvgWait,
        nextRecalcSeconds: metrics.nextRecalcSeconds,
        activeIntersections: metrics.activeIntersections,
        activeEmergencies: metrics.activeEmergencies,
        emissionsSaved: metrics.emissionsSaved,
        systemLoad: metrics.systemLoad,
        decisionLatency: metrics.decisionLatency,
        optimizationEfficiency: metrics.optimizationEfficiency,
        uptimeSeconds: metrics.uptimeSeconds,
        websterRecalculations: metrics.websterRecalculations,
        lastVisionUpdate: stats.last_vision_update || null,
        liveVisionStatus: stats.live_vision_status || 'Synced',
        lastDetectionCount: stats.last_detection_count || 0,
      };
    }),
}));
