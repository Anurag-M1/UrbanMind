'use client';

import { useWebSocket } from '@/hooks/useWebSocket';

export function SimulatorInit() {
  useWebSocket();
  return null;
}
