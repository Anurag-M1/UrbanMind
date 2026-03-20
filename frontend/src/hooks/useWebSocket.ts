/* Live dashboard WebSocket hook with exponential backoff reconnects. */

import { useEffect, useRef, useState } from "react";

import { useEmergencyStore } from "../store/emergencyStore";
import { useIntersectionStore } from "../store/intersectionStore";
import type { DashboardMessage } from "../types";

const DASHBOARD_WS_URL =
  import.meta.env.VITE_WS_URL ??
  `ws://${window.location.hostname}:8000/ws/dashboard`;

type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<DashboardMessage | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const socketRef = useRef<WebSocket | null>(null);
  const retryAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<number | null>(null);

  const updateAllIntersections = useIntersectionStore((state) => state.updateAllIntersections);
  const updateSystemStats = useIntersectionStore((state) => state.updateSystemStats);
  const addAlert = useIntersectionStore((state) => state.addAlert);
  const setActiveVehicles = useEmergencyStore((state) => state.setActiveVehicles);
  const activateEmergency = useEmergencyStore((state) => state.activateEmergency);

  useEffect(() => {
    const connect = () => {
      setConnectionStatus("connecting");
      const socket = new WebSocket(DASHBOARD_WS_URL);
      socketRef.current = socket;

      socket.onopen = () => {
        retryAttemptRef.current = 0;
        setIsConnected(true);
        setConnectionStatus("connected");
      };

      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data) as DashboardMessage;
        setLastMessage(payload);

        if (payload.intersections) {
          updateAllIntersections(payload.intersections);
        }
        if (payload.system_stats) {
          updateSystemStats(payload.system_stats);
        }
        if (payload.active_vehicles) {
          setActiveVehicles(payload.active_vehicles);
        }
        if (payload.type === "emergency_activated" && payload.vehicle && payload.corridor) {
          activateEmergency(payload.vehicle, payload.corridor);
          addAlert({
            id: `${payload.vehicle.id}-${payload.timestamp}`,
            kind: "emergency",
            title: "Emergency Corridor Activated",
            message: `${payload.vehicle.type.toUpperCase()} routed through ${payload.corridor.length} signals`,
            timestamp: payload.timestamp,
          });
        }
        if (payload.type === "fault" && payload.intersection_id && payload.message) {
          addAlert({
            id: `${payload.intersection_id}-${payload.timestamp}`,
            kind: "fault",
            title: "Hardware Fault",
            message: payload.message,
            timestamp: payload.timestamp,
          });
        }
      };

      socket.onerror = () => {
        setConnectionStatus("error");
      };

      socket.onclose = () => {
        setIsConnected(false);
        setConnectionStatus("disconnected");
        const attempt = retryAttemptRef.current + 1;
        retryAttemptRef.current = attempt;
        const delay = Math.min(30000, 1000 * 2 ** Math.min(attempt - 1, 4));
        reconnectTimerRef.current = window.setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      socketRef.current?.close();
    };
  }, [activateEmergency, addAlert, setActiveVehicles, updateAllIntersections, updateSystemStats]);

  return { isConnected, lastMessage, connectionStatus };
}
