import { useEffect, useState } from 'react'
import { Card } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { apiFetch } from '../lib/api'
import { useLangStore } from '../stores/langStore'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

/** Pick the best localized value for a field, with fallback chain. */
function localizedField(obj, field, lang) {
  const en = obj[`${field}_en`]
  const ar = obj[`${field}_ar`]
  const fallback = obj[field]
  return lang === 'ar' ? (ar || en || fallback) : (en || ar || fallback)
}

function formatDate(val) {
  if (!val) return ''
  const d = new Date(val)
  if (Number.isNaN(d.getTime())) return val
  return d.toLocaleString()
}

export function NotificationsPage() {
  const lang = useLangStore((s) => s.lang)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notifications, setNotifications] = useState([])

  async function loadNotifications() {
    setLoading(true)
    setError('')
    try {
      const res = await apiFetch('/notifications/')
      const json = await res.json().catch(() => [])
      if (!res.ok) throw new Error(json.detail || 'Failed to load notifications')
      setNotifications(parseList(json))
    } catch (err) {
      setError(err.message || 'Failed to load notifications')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadNotifications()
  }, [])

  async function markRead(id) {
    try {
      const res = await apiFetch(`/notifications/${id}/mark-read/`, { method: 'POST' })
      if (res.ok) {
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n))
        )
      }
    } catch (e) {
      // ignore
    }
  }

  async function markAllRead() {
    try {
      const res = await apiFetch(`/notifications/mark-all-read/`, { method: 'POST' })
      if (res.ok) {
        setNotifications((prev) =>
          prev.map((n) => (!n.read_at ? { ...n, read_at: new Date().toISOString() } : n))
        )
      }
    } catch (e) {
      // ignore
    }
  }

  const unreadCount = notifications.filter((n) => !n.read_at).length

  return (
    <>
      <PageHeader
        title="Notifications"
        subtitle="Stay updated on important alerts."
      />
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
        <button
          className="btn btn-secondary"
          onClick={markAllRead}
          disabled={unreadCount === 0 || loading}
        >
          Mark all as read
        </button>
      </div>

      {loading && <p className="muted">Loading notifications...</p>}
      {!loading && error && <p className="teaching-error">{error}</p>}
      {!loading && !error && notifications.length === 0 && (
        <Card>
          <p className="muted" style={{ padding: '2rem 1rem', textAlign: 'center', margin: 0 }}>
            You have no notifications.
          </p>
        </Card>
      )}

      {!loading && !error && notifications.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {notifications.map((n) => {
            const isUnread = !n.read_at
            const displayTitle = localizedField(n, 'title', lang)
            const displayBody = localizedField(n, 'body', lang)
            return (
              <Card key={n.id} style={{ borderLeft: isUnread ? '4px solid #6366f1' : '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                  <div>
                    <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.05rem', fontWeight: isUnread ? 600 : 500, color: 'var(--text-color)' }}>
                      {displayTitle}
                    </h3>
                    <p style={{ margin: 0, color: 'var(--text-color)', lineHeight: 1.5 }}>{displayBody}</p>
                    <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: '#9ca3af' }}>{formatDate(n.created_at)}</p>
                  </div>
                  {isUnread && (
                    <button className="btn btn-ghost" onClick={() => markRead(n.id)} style={{ fontSize: '0.85rem' }}>
                      Mark read
                    </button>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </>
  )
}
