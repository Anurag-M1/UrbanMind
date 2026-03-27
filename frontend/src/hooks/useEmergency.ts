import { useEmergencyStore } from '../store/emergencyStore';

export function useEmergency() {
  const activeVehicles = useEmergencyStore((s) => s.activeVehicles);
  const events = useEmergencyStore((s) => s.events);
  const corridorMessage = useEmergencyStore((s) => s.corridorMessage);
  const setCorridorMessage = useEmergencyStore((s) => s.setCorridorMessage);

  const hasActiveEmergency = activeVehicles.length > 0;

  return {
    activeVehicles,
    events,
    corridorMessage,
    hasActiveEmergency,
    setCorridorMessage,
  };
}
