import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
})

export async function fetchDashboardSnapshot() {
  const [{ data: intersections }, { data: emergencies }] = await Promise.all([
    apiClient.get('/intersections'),
    apiClient.get('/emergency/active')
  ])

  return {
    intersections: intersections || [],
    emergencies: emergencies || []
  }
}

export async function deactivateEmergency(vehicleId) {
  const { data } = await apiClient.post(`/emergency/deactivate/${vehicleId}`)
  return data
}
