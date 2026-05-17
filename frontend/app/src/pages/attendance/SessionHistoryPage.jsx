import { useEffect, useMemo, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch, apiFetchAll } from '../../lib/api'

/* ── helpers ──────────────────────────────────────────────────────── */

function statusChip(status) {
  const map = {
    active: { label: 'Active', bg: '#dcfce7', color: '#166534' },
    completed: { label: 'Finished', bg: '#dbeafe', color: '#1e40af' },
    cancelled: { label: 'Cancelled', bg: '#fee2e2', color: '#991b1b' },
  }
  const s = map[status] || { label: status || '—', bg: '#f3f4f6', color: '#374151' }
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '0.15rem 0.6rem',
        borderRadius: '9999px',
        fontSize: '0.78rem',
        fontWeight: 600,
        background: s.bg,
        color: s.color,
      }}
    >
      {s.label}
    </span>
  )
}

function studentStatusBadge(status) {
  const map = {
    present: { label: 'Present', bg: '#dcfce7', color: '#166534', icon: '✓' },
    absent: { label: 'Absent', bg: '#fee2e2', color: '#991b1b', icon: '✗' },
    not_marked: { label: 'Not Marked', bg: '#fef9c3', color: '#854d0e', icon: '?' },
  }
  const s = map[status] || { label: status, bg: '#f3f4f6', color: '#374151', icon: '' }
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.3rem',
        padding: '0.15rem 0.55rem',
        borderRadius: '9999px',
        fontSize: '0.78rem',
        fontWeight: 600,
        background: s.bg,
        color: s.color,
      }}
    >
      {s.icon} {s.label}
    </span>
  )
}

/* ── Session detail view ──────────────────────────────────────────── */

function SessionDetail({ sessionData, onBack }) {
  const session = sessionData.session
  const students = sessionData.students || []

  const presentStudents = students.filter((s) => s.status === 'present')
  const absentStudents = students.filter((s) => s.status === 'absent')
  const notMarkedStudents = students.filter((s) => s.status === 'not_marked')

  return (
    <div>
      <button
        className="btn btn-ghost btn-xs"
        onClick={onBack}
        style={{ marginBottom: '1rem' }}
      >
        ← Back to session list
      </button>

      {/* Session summary card */}
      <Card title={`Session #${session.id} — ${session.school_class_name || session.class_name || '—'}`}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{ textAlign: 'center' }}>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>Date</p>
            <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>{session.date || '—'}</p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>Status</p>
            <p style={{ margin: 0 }}>{statusChip(session.status)}</p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>Instructor</p>
            <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>{session.instructor_name || '—'}</p>
          </div>
          <div style={{ textAlign: 'center' }}>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>Total Students</p>
            <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>{sessionData.total_class_students}</p>
          </div>
        </div>

        {/* Counts row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
          <div
            style={{
              background: '#dcfce7',
              borderRadius: '0.5rem',
              padding: '0.75rem 1rem',
              textAlign: 'center',
            }}
          >
            <p style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, color: '#166534' }}>
              {sessionData.present_count}
            </p>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#166534' }}>Present</p>
          </div>
          <div
            style={{
              background: '#fee2e2',
              borderRadius: '0.5rem',
              padding: '0.75rem 1rem',
              textAlign: 'center',
            }}
          >
            <p style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, color: '#991b1b' }}>
              {sessionData.absent_count}
            </p>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#991b1b' }}>Absent</p>
          </div>
          <div
            style={{
              background: '#fef9c3',
              borderRadius: '0.5rem',
              padding: '0.75rem 1rem',
              textAlign: 'center',
            }}
          >
            <p style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, color: '#854d0e' }}>
              {sessionData.not_marked_count}
            </p>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#854d0e' }}>Not Marked</p>
          </div>
        </div>
      </Card>

      {/* Present students */}
      <Card title={`Present (${presentStudents.length})`} style={{ marginTop: '1.5rem' }}>
        {presentStudents.length === 0 ? (
          <p className="muted" style={{ margin: 0 }}>No present students.</p>
        ) : (
          <div className="feature-table-wrap">
            <table className="feature-table">
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Name</th>
                  <th>Source</th>
                  <th>Marked At</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {presentStudents.map((s) => (
                  <tr key={s.student_db_id}>
                    <td>{s.student_id || '—'}</td>
                    <td style={{ fontWeight: 500 }}>{s.student_name || '—'}</td>
                    <td>{s.source_display || s.source || '—'}</td>
                    <td>{s.marked_at ? new Date(s.marked_at).toLocaleString() : '—'}</td>
                    <td>{studentStatusBadge(s.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Absent students */}
      <Card title={`Absent (${absentStudents.length})`} style={{ marginTop: '1.5rem' }}>
        {absentStudents.length === 0 ? (
          <p className="muted" style={{ margin: 0 }}>No absent students.</p>
        ) : (
          <div className="feature-table-wrap">
            <table className="feature-table">
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Name</th>
                  <th>Source</th>
                  <th>Marked At</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {absentStudents.map((s) => (
                  <tr key={s.student_db_id}>
                    <td>{s.student_id || '—'}</td>
                    <td style={{ fontWeight: 500 }}>{s.student_name || '—'}</td>
                    <td>{s.source_display || s.source || '—'}</td>
                    <td>{s.marked_at ? new Date(s.marked_at).toLocaleString() : '—'}</td>
                    <td>{studentStatusBadge(s.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Not marked students */}
      {notMarkedStudents.length > 0 && (
        <Card title={`Not Marked (${notMarkedStudents.length})`} style={{ marginTop: '1.5rem' }}>
          <div className="feature-table-wrap">
            <table className="feature-table">
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Name</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {notMarkedStudents.map((s) => (
                  <tr key={s.student_db_id}>
                    <td>{s.student_id || '—'}</td>
                    <td style={{ fontWeight: 500 }}>{s.student_name || '—'}</td>
                    <td>{studentStatusBadge(s.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}

/* ── Main page ────────────────────────────────────────────────────── */

export function SessionHistoryPage({ title = 'Session History' }) {
  const navigate = useNavigate()
  const { sessionId } = useParams()

  const [classes, setClasses] = useState([])
  const [selectedClass, setSelectedClass] = useState('')
  const [statusFilter, setStatusFilter] = useState('')  // '' = default (completed+cancelled)
  const [sessionsData, setSessionsData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [detailData, setDetailData] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')

  // Load classes on mount
  useEffect(() => {
    let disposed = false
    async function loadClasses() {
      try {
        const data = await apiFetchAll('/classes/')
        if (!disposed) setClasses(data)
      } catch {
        if (!disposed) setError('Failed to load classes.')
      }
    }
    loadClasses()
    return () => { disposed = true }
  }, [])

  // Fetch class session history when class is selected
  const fetchHistory = useCallback(async () => {
    if (!selectedClass) return
    let disposed = false
    setLoading(true)
    setError('')
    setDetailData(null)
    try {
      let url = `/attendance-sessions/class-history/?school_class=${selectedClass}`
      if (statusFilter) url += `&status=${statusFilter}`
      const res = await apiFetch(url)
      const json = await res.json()
      if (!res.ok) {
        throw new Error(json.message || json.detail || `Failed to load history (${res.status})`)
      }
      if (!disposed) setSessionsData(json)
    } catch (err) {
      if (!disposed) setError(err.message || 'Failed to load session history.')
    } finally {
      if (!disposed) setLoading(false)
    }
    return () => { disposed = true }
  }, [selectedClass, statusFilter])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  // If sessionId is in URL params, load that session's detail
  useEffect(() => {
    if (!sessionId) return
    let disposed = false
    setDetailLoading(true)
    setDetailError('')
    async function loadDetail() {
      try {
        const res = await apiFetch(`/attendance-sessions/${sessionId}/history/`)
        const json = await res.json()
        if (!res.ok) {
          throw new Error(json.message || json.detail || `Failed to load session detail (${res.status})`)
        }
        if (!disposed) setDetailData(json)
      } catch (err) {
        if (!disposed) setDetailError(err.message || 'Failed to load session detail.')
      } finally {
        if (!disposed) setDetailLoading(false)
      }
    }
    loadDetail()
    return () => { disposed = true }
  }, [sessionId])

  // If we have detail data, show the session detail view
  if (sessionId) {
    if (detailLoading) {
      return (
        <>
          <PageHeader title={title} subtitle="View attendance details for a session." />
          <Card><p className="muted">Loading session detail…</p></Card>
        </>
      )
    }
    if (detailError) {
      return (
        <>
          <PageHeader title={title} subtitle="View attendance details for a session." />
          <Card><p className="teaching-error">{detailError}</p></Card>
        </>
      )
    }
    if (detailData) {
      return (
        <>
          <PageHeader title={title} subtitle="View attendance details for a session." />
          <SessionDetail
            sessionData={detailData}
            onBack={() => navigate(-1)}
          />
        </>
      )
    }
  }

  return (
    <>
      <PageHeader
        title={title}
        subtitle="View all students in a class — who was present, absent, or not marked for each session."
      />

      {/* Class selector + status filter */}
      <Card title="Select Class">
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 200px', minWidth: 200 }}>
            <label className="login-label" htmlFor="history-class-select">Class</label>
            <select
              id="history-class-select"
              className="login-input login-input--plain"
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
            >
              <option value="">— Choose a class —</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.display_name || c.name || `Class #${c.id}`}
                </option>
              ))}
            </select>
          </div>
          <div style={{ flex: '1 1 160px', minWidth: 160 }}>
            <label className="login-label" htmlFor="history-status-filter">Session Status</label>
            <select
              id="history-status-filter"
              className="login-input login-input--plain"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">Completed & Cancelled</option>
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <button
            className="btn btn-ghost btn-xs"
            onClick={fetchHistory}
            disabled={loading || !selectedClass}
          >
            {loading ? 'Loading…' : '↻ Refresh'}
          </button>
        </div>
      </Card>

      {!selectedClass ? (
        <Card style={{ marginTop: '1.5rem' }}>
          <p className="muted" style={{ margin: 0 }}>Select a class above to view session history.</p>
        </Card>
      ) : loading ? (
        <Card style={{ marginTop: '1.5rem' }}>
          <p className="muted">Loading session history…</p>
        </Card>
      ) : error ? (
        <Card style={{ marginTop: '1.5rem' }}>
          <p className="teaching-error">{error}</p>
        </Card>
      ) : sessionsData && sessionsData.sessions && sessionsData.sessions.length > 0 ? (
        <div style={{ marginTop: '1.5rem' }}>
          {/* Summary stats */}
          <Card title={`${sessionsData.school_class_name} — ${sessionsData.total_sessions} Sessions`}>
            <div className="feature-table-wrap">
              <table className="feature-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Class / Subject</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Present</th>
                    <th>Absent</th>
                    <th>Not Marked</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sessionsData.sessions.map((entry) => {
                    const s = entry.session
                    return (
                      <tr key={s.id}>
                        <td>{s.id}</td>
                        <td>{s.school_class_name || s.class_name || '—'}</td>
                        <td>{s.date || '—'}</td>
                        <td>{statusChip(s.status)}</td>
                        <td style={{ fontWeight: 600, color: '#166534' }}>{entry.present_count}</td>
                        <td style={{ fontWeight: 600, color: '#991b1b' }}>{entry.absent_count}</td>
                        <td style={{ fontWeight: 600, color: '#854d0e' }}>{entry.not_marked_count}</td>
                        <td>
                          <button
                            className="btn btn-primary btn-xs"                            onClick={() => navigate(String(s.id))}
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      ) : sessionsData ? (
        <Card style={{ marginTop: '1.5rem' }}>
          <p className="muted" style={{ margin: 0 }}>No sessions found for this class with the selected filter.</p>
        </Card>
      ) : null}
    </>
  )
}