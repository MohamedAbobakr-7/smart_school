import { useEffect, useMemo, useState } from 'react'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

const ROLES = ['ADMIN', 'TEACHER', 'STUDENT', 'PARENT']

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

function displayName(user) {
  const n = [user?.first_name, user?.last_name].filter(Boolean).join(' ').trim()
  return n || user?.username || user?.email || '—'
}

export function AdminUsersPage() {
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [users, setUsers] = useState([])
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('ALL')

  async function loadUsers() {
    setLoading(true)
    setError('')
    try {
      const res = await apiFetch('/users/')
      const data = await res.json().catch(() => [])
      if (!res.ok) throw new Error(data.detail || `Failed to load users (${res.status})`)
      setUsers(parseList(data))
    } catch (e) {
      setError(e.message || 'Failed to load users.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return users.filter((u) => {
      const roleOk = roleFilter === 'ALL' || u.role === roleFilter
      if (!q) return roleOk
      const hay = `${u.username || ''} ${u.email || ''} ${u.first_name || ''} ${u.last_name || ''}`.toLowerCase()
      return roleOk && hay.includes(q)
    })
  }, [users, search, roleFilter])

  async function deleteUser(user) {
    const ok = window.confirm(`Delete user "${user.username || user.email}"?`)
    if (!ok) return
    setBusy(true)
    setMessage('')
    try {
      const res = await apiFetch(`/users/${user.id}/`, { method: 'DELETE' })
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail || `Delete failed (${res.status})`)
      }
      setMessage(`User deleted: ${user.username || user.email}`)
      await loadUsers()
    } catch (err) {
      setMessage(err.message || 'Delete user failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Users"
        subtitle="View and delete accounts. To change email, password, or profile details, use Students, Teachers, or Parents."
      />

      {message ? <p className="teaching-msg">{message}</p> : null}
      {loading ? <p className="muted">Loading users...</p> : null}
      {!loading && error ? <p className="teaching-error">{error}</p> : null}

      {!loading && !error ? (
        <Card title="Users Directory">
          <div className="students-toolbar" style={{ marginBottom: '1.25rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div className="topbar-search-label" style={{ flex: '1', minWidth: '240px', maxWidth: '400px', margin: 0 }}>
              <span className="topbar-search-icon" style={{ pointerEvents: 'none' }}>🔍</span>
              <input
                type="search"
                className="topbar-search"
                placeholder="Search by name, username, email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <select
              className="login-input login-input--plain"
              style={{ width: 'auto', borderRadius: '999px', padding: '0.65rem 1rem' }}
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <option value="ALL">All roles</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          {filtered.length ? (
            <div className="feature-table-wrap">
              <table className="feature-table admin-users-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((u) => (
                    <tr key={u.id}>
                      <td>{displayName(u)}</td>
                      <td>{u.email || '—'}</td>
                      <td>
                        <span className="status-chip status-unknown">{u.role || '—'}</span>
                      </td>
                      <td>{u.is_active ? 'Active' : 'Disabled'}</td>
                      <td>
                        <div className="table-actions">
                          <button type="button" className="btn btn-primary btn-xs" disabled={busy} onClick={() => deleteUser(u)}>
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="students-empty" style={{ padding: '2rem 0', textAlign: 'center' }}>
              <p className="muted">No users match your search/filter.</p>
            </div>
          )}
        </Card>
      ) : null}
    </>
  )
}
