import { create } from 'zustand';
import type { EmergencyVehicle, EmergencyEvent } from '../types';

interface EmergencyStore {
  activeVehicles: EmergencyVehicle[];
  events: EmergencyEvent[];
  corridorMessage: string | null;
  setActiveVehicles: (vehicles: EmergencyVehicle[]) => void;
  addVehicle: (vehicle: EmergencyVehicle) => void;
  removeVehicle: (id: string) => void;
  updateVehiclePosition: (id: string, lat: number, lng: number, speed: number, heading: number) => void;
  setEvents: (events: EmergencyEvent[]) => void;
  addEvent: (event: EmergencyEvent) => void;
  setCorridorMessage: (message: string | null) => void;
}

export const useEmergencyStore = create<EmergencyStore>((set, get) => ({
  activeVehicles: [],
  events: [],
  corridorMessage: null,

  setActiveVehicles: (vehicles) => set({ activeVehicles: vehicles }),

  addVehicle: (vehicle) =>
    set((state) => ({
      activeVehicles: [...state.activeVehicles.filter((v) => v.id !== vehicle.id), vehicle],
    })),

  removeVehicle: (id) =>
    set((state) => ({
      activeVehicles: state.activeVehicles.filter((v) => v.id !== id),
    })),

  updateVehiclePosition: (id, lat, lng, speed, heading) =>
    set((state) => ({
      activeVehicles: state.activeVehicles.map((v) =>
        v.id === id ? { ...v, lat, lng, speed_kmh: speed, heading_degrees: heading } : v
      ),
    })),

  setEvents: (events) => set({ events }),
  addEvent: (event) => set((state) => ({ events: [event, ...state.events].slice(0, 50) })),
  setCorridorMessage: (message) => set({ corridorMessage: message }),
}));
