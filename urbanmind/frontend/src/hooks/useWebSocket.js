import { useEffect, useRef, useState } from 'react'
import { fetchDashboardSnapshot } from '../api/client'

export function useWebSocket() {
  const [intersections, setIntersections] = useState([])
  const [emergencies, setEmergencies] = useState([])
  const [connected, setConnected] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)
  const retryRef = useRef(null)
  const pollRef = useRef(null)

  useEffect(() => {
    let socket
    let cancelled = false
    const transport = import.meta.env.VITE_LIVE_TRANSPORT || 'auto'
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const wsUrl =
      import.meta.env.VITE_WS_URL ||
      apiBaseUrl.replace(/^http/, 'ws').replace(/\/$/, '') + '/ws/live'
    const pollIntervalMs = Number(import.meta.env.VITE_POLL_INTERVAL_MS || 5000)

    const applySnapshot = (payload) => {
      setIntersections(payload.intersections || [])
      setEmergencies(payload.emergencies || [])
      setLastUpdated(new Date())
    }

    const loadSnapshot = async () => {
      try {
        const payload = await fetchDashboardSnapshot()
        if (cancelled) {
          return
        }
        applySnapshot(payload)
        setConnected(true)
      } catch {
        if (!cancelled) {
          setConnected(false)
        }
      }
    }

    const startPolling = () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
      }
      void loadSnapshot()
      pollRef.current = setInterval(() => {
        void loadSnapshot()
      }, pollIntervalMs)
    }

    const connect = () => {
      socket = new WebSocket(wsUrl)

      socket.onopen = () => {
        if (retryRef.current) {
          clearTimeout(retryRef.current)
        }
        setConnected(true)
      }

      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data)
        setIntersections((previous) => {
          if (payload.type === 'snapshot') {
            setEmergencies(payload.emergencies || [])
            setLastUpdated(new Date())
            return payload.intersections || []
          }
          const next = new Map(previous.map((intersection) => [intersection.intersection_id, intersection]))
          ;(payload.intersections || []).forEach((intersection) => {
            next.set(intersection.intersection_id, intersection)
          })
          setEmergencies(payload.emergencies || [])
          setLastUpdated(new Date())
          return [...next.values()]
        })
      }

      socket.onclose = () => {
        setConnected(false)
        if (!cancelled) {
          if (transport === 'auto') {
            startPolling()
            return
          }
          retryRef.current = setTimeout(connect, 3000)
        }
      }
    }

    if (transport === 'polling') {
      startPolling()
    } else {
      connect()
    }

    return () => {
      cancelled = true
      if (retryRef.current) {
        clearTimeout(retryRef.current)
      }
      if (pollRef.current) {
        clearInterval(pollRef.current)
      }
      if (socket) {
        socket.close()
      }
    }
  }, [])

  return { intersections, emergencies, connected, lastUpdated }
}
