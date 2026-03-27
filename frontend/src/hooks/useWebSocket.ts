import { useEffect, useRef, useCallback, useState } from 'react';
import { useTrafficStore } from '../lib/store';
import { useEmergencyStore } from '../store/emergencyStore';
import type { WSMessage } from '../types';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/ws/dashboard`;
const RECONNECT_DELAY = 2000;
const MAX_RECONNECT_DELAY = 30000;
const defaultCenter: [number, number] = [28.6139, 77.2090];

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const lastMetricsRef = useRef({
    activeEmergencies: 0,
    websterRecalculations: 0,
    liveVisionStatus: '',
    lastDetectionCount: 0,
    lastSirenDetectedAt: '',
    criticalCount: 0,
  });
  const eventCooldownRef = useRef<Map<string, number>>(new Map());
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);

  const syncRealtimeState = useTrafficStore((s) => s.syncRealtimeState);
  const updateSystemStatus = useTrafficStore((s) => s.updateSystemStatus);
  const addEvent = useTrafficStore((s) => s.addEvent);
  const clearOldEvents = useTrafficStore((s) => s.clearOldEvents);
  const addVehicle = useEmergencyStore((s) => s.addVehicle);
  const removeVehicle = useEmergencyStore((s) => s.removeVehicle);
  const updateVehiclePosition = useEmergencyStore((s) => s.updateVehiclePosition);
  const setCorridorMessage = useEmergencyStore((s) => s.setCorridorMessage);
  const setActiveVehicles = useEmergencyStore((s) => s.setActiveVehicles);

  const emitEvent = useCallback(
    (
      type: 'alert' | 'warning' | 'info' | 'emergency' | 'success',
      title: string,
      description: string,
      intersectionId?: string,
      cooldownMs = 15000
    ) => {
      const signature = `${type}:${title}:${intersectionId ?? 'network'}`;
      const now = Date.now();
      const lastFired = eventCooldownRef.current.get(signature) ?? 0;

      if (now - lastFired < cooldownMs) {
        return;
      }

      eventCooldownRef.current.set(signature, now);
      addEvent({ type, title, description, intersectionId });
    },
    [addEvent]
  );

  const analyzeRealtimeState = useCallback(
    (data: WSMessage) => {
      const intersections = data.intersections ?? [];
      const system = data.system;

      if (!intersections.length || !system) {
        return;
      }

      const hotspot = [...intersections].sort(
        (a, b) => b.wait_time_avg + b.density_ew + b.density_ns - (a.wait_time_avg + a.density_ew + a.density_ns)
      )[0];
      const criticalCount = intersections.filter((intersection) => intersection.wait_time_avg >= 35).length;
      const hotspotActiveLoad = hotspot ? Math.round(hotspot.density_ew + hotspot.density_ns) : 0;

      if (hotspot && (hotspot.wait_time_avg >= 28 || hotspotActiveLoad >= 70)) {
        const severity = hotspot.wait_time_avg >= 35 || hotspotActiveLoad >= 85 ? 'alert' : 'warning';
        emitEvent(
          severity,
          severity === 'alert' ? 'Priority Congestion Alert' : 'Traffic Load Rising',
          `${hotspot.name} is averaging ${Math.round(hotspot.wait_time_avg)}s delay with ${hotspotActiveLoad} vehicles in active load.`,
          hotspot.id,
          12000
        );
      }

      if (criticalCount < lastMetricsRef.current.criticalCount && criticalCount === 0) {
        emitEvent(
          'success',
          'Network Stabilized',
          'All monitored sectors have returned below the critical wait threshold.',
          undefined,
          20000
        );
      }

      if (system.active_emergencies > lastMetricsRef.current.activeEmergencies) {
        emitEvent(
          'emergency',
          'Emergency Corridor Opened',
          `${system.active_emergencies} emergency corridor${system.active_emergencies > 1 ? 's are' : ' is'} active across the grid.`,
          undefined,
          8000
        );
      }

      if (system.webster_recalculations && system.webster_recalculations > lastMetricsRef.current.websterRecalculations) {
        emitEvent(
          'info',
          'Adaptive Signal Plan Updated',
          `Webster optimization recalculated ${system.webster_recalculations} times during the current run.`,
          undefined,
          10000
        );
      }

      if (system.live_vision_status && system.live_vision_status !== lastMetricsRef.current.liveVisionStatus) {
        emitEvent(
          'info',
          'Vision Feed Status Changed',
          `Live vision is now reporting ${system.live_vision_status.toUpperCase()}.`,
          undefined,
          10000
        );
      }

      if (
        typeof system.last_detection_count === 'number' &&
        system.last_detection_count > 0 &&
        system.last_detection_count !== lastMetricsRef.current.lastDetectionCount
      ) {
        emitEvent(
          'info',
          'Fresh Ground Truth Received',
          `${system.last_detection_count} vehicles were confirmed in the most recent vision frame.`,
          undefined,
          12000
        );
      }

      if (
        system.last_siren_detected_at &&
        system.last_siren_detected_at !== lastMetricsRef.current.lastSirenDetectedAt
      ) {
        emitEvent(
          'emergency',
          'Siren Priority Signature Confirmed',
          `${(system.last_siren_vehicle_type || 'Emergency vehicle').toString().toUpperCase()} siren pattern verified at ${Math.round(system.siren_detection_confidence ?? 0)}% confidence. Corridor optimization has been elevated.`,
          undefined,
          8000
        );
      }

      lastMetricsRef.current = {
        activeEmergencies: system.active_emergencies,
        websterRecalculations: system.webster_recalculations ?? 0,
        liveVisionStatus: system.live_vision_status ?? '',
        lastDetectionCount: system.last_detection_count ?? 0,
        lastSirenDetectedAt: system.last_siren_detected_at ?? '',
        criticalCount,
      };
    },
    [emitEvent]
  );

  const handleMessage = useCallback(
    (data: WSMessage) => {
      switch (data.type) {
        case 'init':
          syncRealtimeState({
            intersections: data.intersections,
            system: data.system ?? data.stats,
          });
          if (data.emergencies) setActiveVehicles(data.emergencies);
          emitEvent(
            'info',
            'Command Grid Linked',
            `Live telemetry synchronized across ${data.intersections?.length ?? 0} sectors.`,
            undefined,
            60000
          );
          break;

        case 'tick':
          syncRealtimeState({ intersections: data.intersections, system: data.system });
          clearOldEvents();
          analyzeRealtimeState(data);
          break;

        case 'density_update':
          syncRealtimeState({ intersections: data.intersections });
          break;

        case 'emergency_activated':
          if (data.vehicle && data.vehicle.id) {
            const v = data.vehicle;
            const detectionTriggered = data.trigger_source?.startsWith('vision_auto');
            const sirenTriggered = data.trigger_source === 'vision_auto_siren';
            v.corridor_intersections = v.corridor_intersections || [];
            v.current_intersection_idx = v.current_intersection_idx ?? 0;
            v.lat = typeof v.lat === 'number' ? v.lat : defaultCenter[0];
            v.lng = typeof v.lng === 'number' ? v.lng : defaultCenter[1];
            addVehicle(v);
            if (data.message) setCorridorMessage(data.message);
            emitEvent(
              'emergency',
              sirenTriggered
                ? `${v.type.toUpperCase()} Siren Verified`
                : detectionTriggered
                ? `${v.type.toUpperCase()} Detected By Live Vision`
                : `${v.type.toUpperCase()} Unit Dispatched`,
              data.message ||
                (sirenTriggered
                  ? `${v.id} triggered automatic Emergency Ops activation from the live siren detection module.`
                  : detectionTriggered
                  ? `${v.id} triggered automatic Emergency Ops activation from the live detection feed.`
                  : `${v.id} has entered the green corridor response route.`),
              undefined,
              5000
            );
          }
          break;

        case 'vehicle_position':
          if (data.vehicle_id && data.lat !== undefined && data.lng !== undefined) {
            updateVehiclePosition(
              data.vehicle_id,
              data.lat,
              data.lng,
              data.speed_kmh ?? 0,
              data.heading ?? 0
            );
          }
          break;

        case 'emergency_deactivated':
          if (data.vehicle_id) {
            removeVehicle(data.vehicle_id);
            setCorridorMessage(null);
            emitEvent(
              'success',
              'Emergency Corridor Cleared',
              `${data.vehicle_id} completed corridor traversal and was returned to normal routing.`,
              undefined,
              5000
            );
          }
          break;

        case 'corridor_update':
          if (data.message) {
            emitEvent('info', 'Corridor Route Updated', data.message, undefined, 8000);
          }
          break;

        case 'webster_recalc':
          emitEvent('info', 'Signal Plan Rebalanced', 'Adaptive timing was recalculated from the live traffic state.', data.intersection_id, 10000);
          break;

        case 'demo_reset':
          emitEvent('info', 'Demo State Reset', 'The network state was reseeded and telemetry is re-synchronizing.', undefined, 5000);
          break;

        case 'pong':
        case 'keepalive':
          break;
      }
    },
    [syncRealtimeState, setActiveVehicles, emitEvent, clearOldEvents, analyzeRealtimeState, addVehicle, removeVehicle, updateVehiclePosition, setCorridorMessage]
  );

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setReconnecting(false);
        reconnectAttemptsRef.current = 0;
        updateSystemStatus('connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSMessage;
          handleMessage(data);
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        setConnected(false);
        setReconnecting(true);
        updateSystemStatus('syncing');
        emitEvent('warning', 'Realtime Link Interrupted', 'Attempting to reconnect the command telemetry channel.', undefined, 10000);
        const delay = Math.min(
          RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current),
          MAX_RECONNECT_DELAY
        );
        reconnectAttemptsRef.current++;
        reconnectTimerRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        updateSystemStatus('fault');
        ws.close();
      };
    } catch {
      setConnected(false);
      setReconnecting(true);
      updateSystemStatus('fault');
      const delay = Math.min(
        RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current),
        MAX_RECONNECT_DELAY
      );
      reconnectAttemptsRef.current++;
      reconnectTimerRef.current = setTimeout(connect, delay);
    }
  }, [handleMessage, emitEvent, updateSystemStatus]);

  useEffect(() => {
    connect();
    // Ping every 20s
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 20000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, reconnecting };
}
