import { useEffect, useMemo, useState } from 'react'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

function formatDate(value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString()
}

function splitSubjectFromClassName(className) {
  if (!className || typeof className !== 'string') return '—'
  const parts = className
    .split('—')
    .map((p) => p.trim())
    .filter(Boolean)
  return parts[0] || className
}

export function StudentAttendancePage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [rows, setRows] = useState([])

  useEffect(() => {
    let disposed = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const [attendanceRes, sessionsRes] = await Promise.all([
          apiFetch('/attendance/'),
          apiFetch('/attendance-sessions/'),
        ])

        const attendanceJson = attendanceRes.ok ? await attendanceRes.json().catch(() => []) : []
        const sessionsJson = sessionsRes.ok ? await sessionsRes.json().catch(() => []) : []

        if (!attendanceRes.ok) {
          throw new Error(
            (attendanceJson && attendanceJson.detail) || `Failed to load attendance (${attendanceRes.status})`
          )
        }

        const attendanceList = parseList(attendanceJson)
        const sessionsList = parseList(sessionsJson)
        const subjectBySessionId = new Map(
          sessionsList.map((s) => [s.id, splitSubjectFromClassName(s.class_name)])
        )

        const mapped = attendanceList.map((a) => ({
          id: a.id,
          date: a.date,
          subject: subjectBySessionId.get(a.session) || subjectBySessionId.get(a.session_id) || '—',
          status: a.status,
        }))

        if (!disposed) setRows(mapped)
      } catch (e) {
        if (!disposed) setError(e.message || 'Failed to load attendance.')
      } finally {
        if (!disposed) setLoading(false)
      }
    })()
    return () => {
      disposed = true
    }
  }, [])

  const summary = useMemo(() => {
    const total = rows.length
    const present = rows.filter((r) => r.status === 'present').length
    const pct = total > 0 ? Math.round((present / total) * 100) : null
    return {
      totalDays: total,
      attendancePct: pct,
    }
  }, [rows])

  return (
    <>
      <PageHeader
        title="Attendance"
        subtitle="Track your attendance history with subject context and current attendance rate."
      />

      <div className="grid-cards">
        <Card title="Attendance %">
          <p className="student-attendance-metric">
            {loading ? '...' : summary.attendancePct == null ? '—' : `${summary.attendancePct}%`}
          </p>
        </Card>
        <Card title="Total days">
          <p className="student-attendance-metric">{loading ? '...' : summary.totalDays}</p>
        </Card>
      </div>

      <Card title="Attendance Table">
        {loading ? <p className="muted">Loading attendance...</p> : null}
        {!loading && error ? <p className="teaching-error">{error}</p> : null}

        {!loading && !error ? (
          rows.length ? (
            <div className="feature-table-wrap">
              <table className="feature-table student-attendance-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Subject</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id}>
                      <td>{formatDate(r.date)}</td>
                      <td>{r.subject}</td>
                      <td>
                        <span className={`status-chip status-${r.status || 'unknown'}`}>
                          {r.status === 'present'
                            ? 'Present'
                            : r.status === 'absent'
                              ? 'Absent'
                              : r.status || '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="student-attendance-empty">
              <p className="muted">No attendance records found.</p>
            </div>
          )
        ) : null}
      </Card>
    </>
  )
}
