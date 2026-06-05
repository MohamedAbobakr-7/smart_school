import { create } from 'zustand'
import { apiFetch } from '../lib/api'
import { useAuthStore } from './authStore'

/** Parse DRF paginated or plain list response */
function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

/**
 * Notification store with real-time WebSocket push.
 *
 * - Connects to ws:///ws/notifications/?access=<JWT> when authenticated.
 * - Falls back to REST polling if WebSocket fails.
 * - Shares unread count and notification list across all components.
 */
export const useNotificationStore = create((set, get) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,
  error: '',
  _ws: null,
  _pollInterval: null,
  _reconnectAttempts: 0,

  /** Fetch notifications from REST API */
  fetchNotifications: async () => {
    const { access } = useAuthStore.getState()
    if (!access) return
    set({ loading: true, error: '' })
    try {
      const res = await apiFetch('/notifications/')
      const json = await res.json().catch(() => [])
      if (!res.ok) throw new Error(json.detail || 'Failed to load notifications')
      const list = parseList(json)
      const unread = list.filter((n) => !n.read_at).length
      set({ notifications: list, unreadCount: unread, loading: false })
    } catch (err) {
      set({ error: err.message || 'Failed to load notifications', loading: false })
    }
  },

  /** Fetch only unread count (lightweight, for badge) */
  fetchUnreadCount: async () => {
    const { access } = useAuthStore.getState()
    if (!access) return
    try {
      const res = await apiFetch('/notifications/?unread=true')
      if (!res.ok) return
      const json = await res.json()
      const count = Array.isArray(json)
        ? json.length
        : json.count ?? (json.results ? json.results.length : 0)
      set({ unreadCount: count })
    } catch {
      // silent – don't disrupt UI
    }
  },

  /** Mark a single notification as read */
  markRead: async (id) => {
    try {
      const res = await apiFetch(`/notifications/${id}/mark-read/`, { method: 'POST' })
      if (res.ok) {
        set((state) => ({
          notifications: state.notifications.map((n) =>
            n.id === id ? { ...n, read_at: new Date().toISOString() } : n
          ),
          unreadCount: state.unreadCount - 1,
        }))
      }
    } catch {
      // silent
    }
  },

  /** Mark all notifications as read */
  markAllRead: async () => {
    try {
      const res = await apiFetch('/notifications/mark-all-read/', { method: 'POST' })
      if (res.ok) {
        set((state) => ({
          notifications: state.notifications.map((n) =>
            !n.read_at ? { ...n, read_at: new Date().toISOString() } : n
          ),
          unreadCount: 0,
        }))
      }
    } catch {
      // silent
    }
  },

  /** Handle a real-time notification pushed via WebSocket */
  _onPush: (payload) => {
    set((state) => {
      // Avoid duplicates (dedupe_key or id)
      const exists = state.notifications.some((n) => n.id === payload.id)
      const list = exists
        ? state.notifications.map((n) => (n.id === payload.id ? payload : n))
        : [payload, ...state.notifications]
      const unread = list.filter((n) => !n.read_at).length
      return { notifications: list, unreadCount: unread }
    })
  },

  /** Open WebSocket connection for real-time notifications */
  connectWebSocket: () => {
    const { _ws } = get()
    if (_ws) return // already connected

    const { access } = useAuthStore.getState()
    if (!access) return // not authenticated

    // Determine WebSocket URL based on current location
    const loc = window.location
    const wsProtocol = loc.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = loc.host // includes port, works with Vite proxy
    const wsUrl = `${wsProtocol}//${wsHost}/ws/notifications/?access=${access}`

    let ws
    try {
      ws = new WebSocket(wsUrl)
    } catch {
      // WebSocket construction failed – fall back to polling
      get()._startPolling()
      return
    }

    ws.onopen = () => {
      set({ _ws: ws, _reconnectAttempts: 0 })
      // Stop polling when WS is connected (real-time is better)
      get()._stopPolling()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.notification_type || data.id) {
          get()._onPush(data)
        }
      } catch {
        // ignore malformed messages
      }
    }

    ws.onerror = () => {
      // WS error – fall back to polling
      get()._startPolling()
    }

    ws.onclose = () => {
      set({ _ws: null })
      // Auto-reconnect with exponential backoff (max 5 attempts)
      const attempts = get()._reconnectAttempts
      if (attempts < 5) {
        const delay = Math.min(1000 * Math.pow(2, attempts), 30000)
        set({ _reconnectAttempts: attempts + 1 })
        setTimeout(() => get().connectWebSocket(), delay)
      } else {
        // Give up on WS, rely on polling
        get()._startPolling()
      }
    }

    set({ _ws: ws })
  },

  /** Disconnect WebSocket (e.g. on logout) */
  disconnectWebSocket: () => {
    const { _ws } = get()
    if (_ws) {
      _ws.onclose = null // prevent auto-reconnect
      _ws.close()
    }
    get()._stopPolling()
    set({
      _ws: null,
      _pollInterval: null,
      _reconnectAttempts: 0,
      notifications: [],
      unreadCount: 0,
    })
  },

  /** Start REST polling fallback (every 30s) */
  _startPolling: () => {
    const { _pollInterval } = get()
    if (_pollInterval) return // already polling
    get().fetchUnreadCount()
    const id = setInterval(() => get().fetchUnreadCount(), 30000)
    set({ _pollInterval: id })
  },

  /** Stop REST polling */
  _stopPolling: () => {
    const { _pollInterval } = get()
    if (_pollInterval) {
      clearInterval(_pollInterval)
      set({ _pollInterval: null })
    }
  },
}))