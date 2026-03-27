const API_BASE = '/api/v1/emergency';

export async function simulateEmergency(vehicleType: string): Promise<{
  vehicle_id: string;
  vehicle_type: string;
  corridor: string[];
  activated_at: string;
}> {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vehicle_type: vehicleType }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to simulate' }));
    throw new Error(err.detail || 'Failed to simulate emergency');
  }
  return res.json();
}

export async function getActiveEmergencies(): Promise<{ active: any[]; count: number }> {
  const res = await fetch(`${API_BASE}/active`);
  if (!res.ok) throw new Error('Failed to get active emergencies');
  return res.json();
}

export async function deactivateEmergency(vehicleId: string): Promise<{ deactivated: boolean }> {
  const res = await fetch(`${API_BASE}/deactivate/${vehicleId}`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to deactivate');
  return res.json();
}

export async function getEmergencyHistory(): Promise<{ events: any[] }> {
  const res = await fetch(`${API_BASE}/history`);
  if (!res.ok) throw new Error('Failed to get history');
  return res.json();
}

export async function resetDemo(): Promise<{ reset: boolean }> {
  const res = await fetch('/api/v1/demo/reset');
  if (!res.ok) throw new Error('Failed to reset demo');
  return res.json();
}

export async function getAnalyticsSummary(): Promise<any> {
  const res = await fetch('/api/v1/analytics/summary');
  if (!res.ok) throw new Error('Failed to get analytics summary');
  return res.json();
}

export async function getFlowSeries(): Promise<{ flow_series: any[] }> {
  const res = await fetch('/api/v1/analytics/flow-series');
  if (!res.ok) throw new Error('Failed to get flow series');
  return res.json();
}

export async function getWaitTimes(): Promise<{ wait_times: any[] }> {
  const res = await fetch('/api/v1/analytics/wait-times');
  if (!res.ok) throw new Error('Failed to get wait times');
  return res.json();
}
