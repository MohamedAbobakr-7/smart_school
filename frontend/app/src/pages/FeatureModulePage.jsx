import { useEffect, useMemo, useState } from 'react'

import { AttendanceCameraCapture } from '../components/attendance/AttendanceCameraCapture'
import { Card } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { apiFetch } from '../lib/api'

function truncate(value, size = 180) {
  if (typeof value !== 'string') return value
  if (value.length <= size) return value
  return `${value.slice(0, size)}...`
}

function normalizeItems(payload) {
  if (Array.isArray(payload)) return payload
  if (payload && Array.isArray(payload.results)) return payload.results
  return []
}

function splitSessionClass(value) {
  const raw = typeof value === 'string' ? value : ''
  if (!raw) return { subject: '—', className: '—' }
  const parts = raw
    .split('—')
    .map((p) => p.trim())
    .filter(Boolean)
  if (parts.length >= 2) return { subject: parts[0], className: parts.slice(1).join(' — ') }
  return { subject: raw, className: raw }
}

export function FeatureModulePage({
  title,
  endpoint,
  hints = [],
  description = '',
  actions = [],
  enableCameraScan = false,
}) {
  const attendanceEndpoint = '/attendance-sessions/'
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [payload, setPayload] = useState(null)
  const [activeEndpoint, setActiveEndpoint] = useState(endpoint)

  const [subjects, setSubjects] = useState([])
  const [classes, setClasses] = useState([])
  const [selectedSubject, setSelectedSubject] = useState('')
  const [selectedClass, setSelectedClass] = useState('')
  const [activeSession, setActiveSession] = useState(null)
  const [roster, setRoster] = useState({ present: [], absent: [] })  // ← new
  const [attendanceMsg, setAttendanceMsg] = useState('')
  const [attendanceStudents, setAttendanceStudents] = useState([])
  const [manualStudent, setManualStudent] = useState('')
  const [manualStatus, setManualStatus] = useState('present')
  const [manualNote, setManualNote] = useState('')
  const [manualBusy, setManualBusy] = useState(false)
  const [sessionBusy, setSessionBusy] = useState(false)

  const items = useMemo(() => normalizeItems(payload), [payload])
  const previewKeys = useMemo(() => {
    const first = items[0]
    if (!first || typeof first !== 'object') return []
    return Object.keys(first).slice(0, 6)
  }, [items])

  async function load(requestEndpoint = endpoint) {
    setLoading(true)
    setError('')
    setActiveEndpoint(requestEndpoint)
    try {
      const res = await apiFetch(requestEndpoint)
      const json = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(json.detail || `Request failed (${res.status})`)
      }
      setPayload(json)
    } catch (err) {
      setError(err.message || 'Failed to fetch data')
      setPayload(null)
    } finally {
      setLoading(false)
    }
  }

  async function runAction(action) {
    setLoading(true)
    setError('')
    try {
      const res = await apiFetch(action.endpoint, {
        method: action.method || 'GET',
        body: action.body,
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(json.detail || `Action failed (${res.status})`)
      }
      setPayload(json)
      setActiveEndpoint(action.endpoint)
    } catch (err) {
      setError(err.message || 'Action failed')
    } finally {
      setLoading(false)
    }
  }

  async function loadAttendanceFilters() {
    if (!enableCameraScan) return
    try {
      const [subjectsRes, studentsRes, classesRes] = await Promise.all([
        apiFetch('/subjects/'),
        apiFetch('/students/'),
        apiFetch('/classes/'),
      ])
      if (subjectsRes.ok) {
        const s = normalizeItems(await subjectsRes.json().catch(() => []))
        setSubjects(s)
      }
      if (studentsRes.ok) {
        const list = normalizeItems(await studentsRes.json().catch(() => []))
        setAttendanceStudents(list)
      }
      if (classesRes.ok) {
        const list = normalizeItems(await classesRes.json().catch(() => []))
        setClasses(list)
      }
    } catch {
      // Non-blocking.
    }
  }

  async function fetchActiveSession() {
    if (!enableCameraScan) return
    try {
      const res = await apiFetch('/attendance-sessions/active/')
      if (res.ok) {
        const json = await res.json().catch(() => ({}))
        if (json.active && json.session) {
          setActiveSession(json.session)
          setAttendanceMsg(`Resuming active session #${json.session.id} — ${json.session.class_name}`)
          await fetchRoster(json.session.id)
        }
      }
    } catch {
      // Non-blocking.
    }
  }

  async function fetchRoster(sessionId) {
    try {
      const res = await apiFetch(`/attendance-sessions/${sessionId}/roster/`)
      if (res.ok) {
        const json = await res.json().catch(() => ({ present: [], absent: [] }))
        setRoster({ present: json.present || [], absent: json.absent || [] })
      }
    } catch {
      // Non-blocking.
    }
  }

  async function createAttendanceSession() {
    if (!selectedSubject || !selectedClass) {
      setAttendanceMsg('Select Subject and Class first.')
      return
    }
    setSessionBusy(true)
    setAttendanceMsg('')
    try {
      const subject = subjects.find((s) => String(s.id) === String(selectedSubject))
      const cls = classes.find((c) => String(c.id) === String(selectedClass))
      const className = [
        subject?.code || subject?.name || 'Subject',
        cls?.display_name || cls?.name || selectedClass,
      ]
        .filter(Boolean)
        .join(' — ')
      const res = await apiFetch('/attendance-sessions/', {
        method: 'POST',
        body: {
          class_name: className,
          school_class: Number(selectedClass),  // ← send class ID for roster creation
          notes: `Camera session for ${className}`,
        },
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(
        json.detail || (Array.isArray(json) ? json[0] : null) || json.message || `Create failed (${res.status})`
      )
      setActiveSession(json)
      setRoster({ present: [], absent: [] })
      setAttendanceMsg(`✅ Session #${json.id} started — ${json.class_name}`)
      await load(attendanceEndpoint)
      await fetchRoster(json.id)
    } catch (err) {
      setAttendanceMsg(err.message || 'Could not create session.')
    } finally {
      setSessionBusy(false)
    }
  }

  async function endActiveSession() {
    if (!activeSession) return
    setSessionBusy(true)
    setAttendanceMsg('')
    try {
      const res = await apiFetch(`/attendance-sessions/${activeSession.id}/complete/`, { method: 'POST' })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(json.detail || json.message || `Complete failed (${res.status})`)
      setAttendanceMsg(`Session #${activeSession.id} completed.`)
    } catch (err) {
      setAttendanceMsg(err.message || 'Could not complete session.')
    } finally {
      // Always re-verify the active session from the backend so the UI
      // reflects the true state — even if the complete call failed (e.g.
      // session was already completed by another request).
      setActiveSession(null)
      setRoster({ present: [], absent: [] })
      await fetchActiveSession()
      await load(attendanceEndpoint)
      setSessionBusy(false)
    }
  }

  function handleAttendanceResult(result) {
    // If backend returned a roster (new behaviour), use it directly
    if (result?.roster) {
      setRoster({
        present: result.roster.present || [],
        absent: result.roster.absent || [],
      })
      if (activeSession) {
        setActiveSession(prev => prev ? {
          ...prev,
          total_attendance_marked: (result.roster.present || []).length
        } : prev)
        load(attendanceEndpoint)
      }
      return
    }
    // Fallback: refresh roster from API
    if (activeSession) {
      fetchRoster(activeSession.id)
    }
  }

  async function submitManualAttendance(e) {
    e.preventDefault()
    if (!activeSession) {
      setAttendanceMsg('Start a session first, then add manual attendance.')
      return
    }
    if (!manualStudent) {
      setAttendanceMsg('Choose a student for manual attendance.')
      return
    }
    setManualBusy(true)
    setAttendanceMsg('')
    try {
      const res = await apiFetch('/attendance/', {
        method: 'POST',
        body: {
          student: Number(manualStudent),
          date: activeSession.date,
          status: manualStatus,
          source: 'manual',
          session: activeSession.id,
          notes: manualNote.trim(),
        },
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(json.detail || json.message || `Manual attendance failed (${res.status})`)
      }
      const studentObj = attendanceStudents.find((s) => String(s.id) === String(manualStudent))
      const label = studentObj?.student_id || `Student #${manualStudent}`
      setAttendanceMsg(`Manual attendance saved: ${label} → ${manualStatus}.`)
      setManualNote('')
      // Refresh the roster after manual entry
      await fetchRoster(activeSession.id)
    } catch (err) {
      setAttendanceMsg(err.message || 'Could not save manual attendance.')
    } finally {
      setManualBusy(false)
    }
  }

  useEffect(() => {
    load(enableCameraScan ? attendanceEndpoint : endpoint)
  }, [endpoint, enableCameraScan])

  useEffect(() => {
    loadAttendanceFilters()
    fetchActiveSession()
  }, [enableCameraScan])

  if (!enableCameraScan) {
    return (
      <>
        <PageHeader title={title} subtitle={description || 'Live backend integration for this module.'} />

        <div className="grid-cards">
          <Card title="Endpoint">
            <p className="muted">
              Active request: <code>{activeEndpoint}</code>
            </p>
            <div className="feature-actions">
              <button type="button" className="btn btn-primary" onClick={() => load(endpoint)} disabled={loading}>
                Refresh
              </button>
              {actions.map((action) => (
                <button
                  key={`${action.label}-${action.endpoint}`}
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => runAction(action)}
                  disabled={loading}
                >
                  {action.label}
                </button>
              ))}
            </div>
            {hints.length ? (
              <ul className="feature-hints">
                {hints.map((hint) => (
                  <li key={hint}>
                    <code>{hint}</code>
                  </li>
                ))}
              </ul>
            ) : null}
          </Card>

          <Card title="Response Overview">
            {loading ? <p className="muted">Loading...</p> : null}
            {!loading && error ? <p className="feature-error">{error}</p> : null}
            {!loading && !error ? (
              <>
                <p className="muted">
                  {Array.isArray(payload)
                    ? `Array response (${payload.length} items)`
                    : items.length
                      ? `Paginated/list response (${items.length} shown)`
                      : 'Object response'}
                </p>
                {items.length && previewKeys.length ? (
                  <div className="feature-table-wrap">
                    <table className="feature-table">
                      <thead>
                        <tr>
                          {previewKeys.map((k) => (
                            <th key={k}>{k}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {items.slice(0, 8).map((item, idx) => (
                          <tr key={item.id ?? idx}>
                            {previewKeys.map((k) => (
                              <td key={k}>{truncate(String(item[k] ?? '—'))}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <pre className="feature-json">{JSON.stringify(payload, null, 2)}</pre>
                )}
              </>
            ) : null}
          </Card>
        </div>
      </>
    )
  }

  return (
    <>
      <PageHeader title={title} subtitle={description || 'Live backend integration for this module.'} />

      <div className="dash-analytics">

        {/* ── Active Session Banner ── */}
        {activeSession ? (
          <div className="attendance-active-banner">
            <div className="attendance-active-info">
              <span className="attendance-active-dot" />
              <div>
                <strong>Session #{activeSession.id} — {activeSession.class_name}</strong>
                <span className="muted" style={{ marginLeft: '0.75rem', fontSize: '0.85rem' }}>
                  {activeSession.date} &nbsp;·&nbsp; {activeSession.attendances_count ?? 0} marked
                </span>
              </div>
            </div>
            <button
              type="button"
              className="btn btn-ghost btn-xs"
              onClick={endActiveSession}
              disabled={sessionBusy}
            >
              {sessionBusy ? 'Finishing…' : 'End Session'}
            </button>
          </div>
        ) : (
          <div className="attendance-no-session-banner">
            <span>No active session. Select subject &amp; class then click <strong>Start Session</strong>.</span>
          </div>
        )}

        {/* ── Start Session Form ── */}
        {!activeSession && (
          <Card title="Start New Attendance Session">
            <div className="attendance-session-grid">
              <div>
                <label className="login-label" htmlFor="attendance-subject-filter">Subject</label>
                <select
                  id="attendance-subject-filter"
                  className="login-input login-input--plain attendance-scan-input"
                  value={selectedSubject}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                >
                  <option value="">Select subject…</option>
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.code ? `${s.code} — ` : ''}{s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="login-label" htmlFor="attendance-class-filter">Class</label>
                <select
                  id="attendance-class-filter"
                  className="login-input login-input--plain attendance-scan-input"
                  value={selectedClass}
                  onChange={(e) => setSelectedClass(e.target.value)}
                >
                  <option value="">Select class…</option>
                  {classes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.display_name || c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="feature-actions" style={{ marginTop: '1rem' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={createAttendanceSession}
                disabled={sessionBusy || !selectedSubject || !selectedClass}
              >
                {sessionBusy ? 'Starting…' : '▶ Start Session'}
              </button>
            </div>
            {attendanceMsg ? <p className="attendance-hint" style={{ marginTop: '0.75rem' }}>{attendanceMsg}</p> : null}
          </Card>
        )}

        {/* ── Camera Capture ── */}
        <Card title={activeSession ? `📷 Camera Capture — Session #${activeSession.id}` : '📷 Camera Capture'}>
          {!activeSession ? (
            <p className="muted attendance-hint">Start a session above to enable face scanning.</p>
          ) : (
            <AttendanceCameraCapture sessionId={String(activeSession.id)} onResult={handleAttendanceResult} />
          )}
          {attendanceMsg && activeSession ? (
            <p className="attendance-hint" style={{ marginTop: '0.75rem' }}>{attendanceMsg}</p>
          ) : null}
        </Card>

        {/* ── Attendance Roster — Present / Absent ── */}
        <Card title={`Attendance Roster${activeSession ? ` — Session #${activeSession.id}` : ''}`}>
          {!activeSession && !roster.present.length && !roster.absent.length ? (
            <p className="muted" style={{ padding: '0.75rem 0' }}>Start a session to see the attendance roster.</p>
          ) : (
            <div className="roster-grid">
              {/* Present */}
              <div className="roster-section roster-present">
                <div className="roster-section-header">
                  <span className="roster-dot roster-dot--present" />
                  <strong>Present</strong>
                  <span className="roster-count">{roster.present.length}</span>
                </div>
                {roster.present.length ? (
                  <ul className="roster-list">
                    {roster.present.map((s) => (
                      <li key={s.id || s.student_id} className="roster-item roster-item--present">
                        <span className="roster-name">{s.student_name}</span>
                        <span className="roster-sid">{s.student_id}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted roster-empty">No students marked present yet.</p>
                )}
              </div>

              {/* Absent */}
              <div className="roster-section roster-absent">
                <div className="roster-section-header">
                  <span className="roster-dot roster-dot--absent" />
                  <strong>Absent</strong>
                  <span className="roster-count">{roster.absent.length}</span>
                </div>
                {roster.absent.length ? (
                  <ul className="roster-list">
                    {roster.absent.map((s) => (
                      <li key={s.id || s.student_id} className="roster-item roster-item--absent">
                        <span className="roster-name">{s.student_name}</span>
                        <span className="roster-sid">{s.student_id}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted roster-empty">All students accounted for! 🎉</p>
                )}
              </div>
            </div>
          )}
        </Card>

        {/* ── Manual Attendance Fallback ── */}
        <Card title="Manual Attendance Fallback">
          {!activeSession ? (
            <p className="muted attendance-hint">Start a session first to mark attendance manually.</p>
          ) : (
            <form className="manual-attendance-form" onSubmit={submitManualAttendance}>
              <div>
                <label className="login-label" htmlFor="manual-student-select">Student</label>
                <select
                  id="manual-student-select"
                  className="login-input login-input--plain attendance-scan-input"
                  value={manualStudent}
                  onChange={(e) => setManualStudent(e.target.value)}
                  disabled={manualBusy}
                >
                  <option value="">Select student…</option>
                  {attendanceStudents.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.student_id || `id ${s.id}`}
                      {s.class_level ? ` — ${s.class_level}` : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="login-label" htmlFor="manual-status-select">Status</label>
                <select
                  id="manual-status-select"
                  className="login-input login-input--plain attendance-scan-input"
                  value={manualStatus}
                  onChange={(e) => setManualStatus(e.target.value)}
                  disabled={manualBusy}
                >
                  <option value="present">Present</option>
                  <option value="absent">Absent</option>
                </select>
              </div>

              <div>
                <label className="login-label" htmlFor="manual-note-input">Note (optional)</label>
                <input
                  id="manual-note-input"
                  className="login-input login-input--plain"
                  value={manualNote}
                  onChange={(e) => setManualNote(e.target.value)}
                  placeholder="Reason / comment"
                  disabled={manualBusy}
                />
              </div>

              <div className="feature-actions">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={manualBusy || !manualStudent}
                >
                  Mark Manually
                </button>
              </div>
              {attendanceMsg ? <p className="attendance-hint">{attendanceMsg}</p> : null}
            </form>
          )}
        </Card>

        {/* ── Session History Table ── */}
        <Card title="Session History">
          <div className="students-toolbar" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button
              type="button"
              className="btn btn-ghost btn-xs"
              onClick={() => load(attendanceEndpoint)}
              disabled={loading}
            >
              {loading ? 'Loading…' : '↻ Refresh'}
            </button>
          </div>
          {loading ? <p className="muted">Loading sessions…</p> : null}
          {!loading && error ? <p className="feature-error">{error}</p> : null}
          {!loading && !error ? (
            <div className="feature-table-wrap">
              <table className="feature-table attendance-sessions-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Class / Subject</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Marked</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length ? (
                    items.map((session) => {
                      const isCurrent = activeSession && String(session.id) === String(activeSession.id)
                      return (
                        <tr key={session.id} className={isCurrent ? 'is-current-session' : ''}>
                          <td>{session.id}</td>
                          <td>{session.class_name || '—'}</td>
                          <td>{session.date || '—'}</td>
                          <td>
                            <span className={`status-chip status-${session.status || 'unknown'}`}>
                              {session.status === 'active' ? 'Active' : session.status === 'completed' ? 'Finished' : session.status || '—'}
                            </span>
                          </td>
                          <td>{session.total_attendance_marked ?? 0}</td>
                        </tr>
                      )
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} style={{ textAlign: 'center', padding: '1.5rem 0' }}>No sessions yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          ) : null}
        </Card>

      </div>
    </>
  )
}


