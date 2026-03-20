/* Zustand store for emergency vehicle and corridor state. */

import { create } from "zustand";

import type { EmergencyEvent, EmergencyVehicle } from "../types";

interface EmergencyStoreState {
  activeVehicles: EmergencyVehicle[];
  activeCorridor: string[];
  emergencyHistory: EmergencyEvent[];
  activateEmergency: (vehicle: EmergencyVehicle, corridor: string[]) => void;
  deactivateEmergency: (vehicleId: string) => void;
  addHistoryEvent: (event: EmergencyEvent) => void;
  replaceHistory: (events: EmergencyEvent[]) => void;
  setActiveVehicles: (vehicles: EmergencyVehicle[]) => void;
}

export const useEmergencyStore = create<EmergencyStoreState>((set) => ({
  activeVehicles: [],
  activeCorridor: [],
  emergencyHistory: [],
  activateEmergency: (vehicle, corridor) =>
    set((current) => ({
      activeVehicles: [
        vehicle,
        ...current.activeVehicles.filter((item) => item.id !== vehicle.id),
      ],
      activeCorridor: corridor,
    })),
  deactivateEmergency: (vehicleId) =>
    set((current) => ({
      activeVehicles: current.activeVehicles.filter((item) => item.id !== vehicleId),
      activeCorridor: current.activeCorridor,
    })),
  addHistoryEvent: (event) =>
    set((current) => ({
      emergencyHistory: [event, ...current.emergencyHistory].slice(0, 20),
    })),
  replaceHistory: (events) => set(() => ({ emergencyHistory: events })),
  setActiveVehicles: (vehicles) =>
    set(() => ({
      activeVehicles: vehicles,
      activeCorridor: Array.from(
        new Set(vehicles.flatMap((vehicle) => vehicle.corridor_intersections)),
      ),
    })),
}));
