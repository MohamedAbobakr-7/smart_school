import { useEffect, useMemo, useState } from 'react'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetchAll } from '../../lib/api'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

function getStatusColor(status) {
  switch (status?.toLowerCase()) {
    case 'present': return '#10b981'
    case 'absent': return '#ef4444'
    case 'late': return '#f97316'
    default: return '#6b7280'
  }
}

function getGradeColor(pct) {
  if (pct == null) return '#6b7280'
  if (pct >= 85) return '#10b981'
  if (pct >= 60) return '#f97316'
  return '#ef4444'
}

function formatPct(v) {
  if (v == null || isNaN(v)) return '—'
  return `${Math.round(v)}%`
}

/** Student list API returns `user` as id or nested object; `user_display_name` when present. */
function displayChildName(c) {
  if (!c) return '—'
  const fromField = (c.user_display_name || '').trim()
  if (fromField) return fromField
  const u = typeof c.user === 'object' && c.user ? c.user : null
  if (u) {
    const n = [u.first_name, u.last_name].filter(Boolean).join(' ').trim()
    if (n) return n
    if (u.username) return u.username
  }
  return c.student_id ? `Student #${c.student_id}` : `Student #${c.id}`
}

function StatBadge({ label, value, color }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      background: 'var(--bg-hover, #f1f5f9)', borderRadius: '12px',
      padding: '0.85rem 1.25rem', minWidth: '110px', flex: 1
    }}>
      <span style={{ fontSize: '1.5rem', fontWeight: 700, color: color || '#6366f1' }}>{value}</span>
      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #6b7280)', marginTop: '0.2rem' }}>{label}</span>
    </div>
  )
}

export function ParentWeeklyReportsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [children, setChildren] = useState([])
  const [attendance, setAttendance] = useState([])
  const [grades, setGrades] = useState([])
  const [selectedChild, setSelectedChild] = useState(null)

  useEffect(() => {
    let disposed = false
    async function load() {
      try {
        const [childList, attList, gradeList] = await Promise.all([
          apiFetchAll('/students/'),
          apiFetchAll('/attendance/'),
          apiFetchAll('/grades/'),
        ])
        if (!disposed) {
          setError('')
          setChildren(Array.isArray(childList) ? childList : parseList(childList))
          setAttendance(Array.isArray(attList) ? attList : parseList(attList))
          setGrades(Array.isArray(gradeList) ? gradeList : parseList(gradeList))
          const list = Array.isArray(childList) ? childList : parseList(childList)
          if (list.length > 0) setSelectedChild(list[0].id)
        }
      } catch (e) {
        let msg = 'Failed to load weekly report data.'
        if (e?.response) {
          try {
            const j = await e.response.json()
            if (typeof j?.detail === 'string') msg = j.detail
            else if (Array.isArray(j?.detail)) msg = j.detail.map((x) => x?.string || JSON.stringify(x)).join(' ')
          } catch {
            /* ignore */
          }
        }
        if (!disposed) setError(msg)
      } finally {
        if (!disposed) setLoading(false)
      }
    }
    load()
    return () => { disposed = true }
  }, [])

  const child = useMemo(
    () => children.find(c => c.id === selectedChild),
    [children, selectedChild]
  )

  const childName = displayChildName(child)

  const childSchoolId = child?.student_id

  const childAttendance = useMemo(() => {
    if (selectedChild == null) return []
    return attendance.filter((a) => {
      if (a.student === selectedChild || Number(a.student) === Number(selectedChild)) return true
      if (childSchoolId && String(a.student_id_display || '') === String(childSchoolId)) return true
      return false
    })
  }, [attendance, selectedChild, childSchoolId])

  const childGrades = useMemo(() => {
    if (selectedChild == null) return []
    return grades.filter((g) => {
      if (String(g.student) === String(selectedChild)) return true
      if (childSchoolId && String(g.student_id || '') === String(childSchoolId)) return true
      return false
    })
  }, [grades, selectedChild, childSchoolId])

  const attStats = useMemo(() => {
    const total = childAttendance.length
    const present = childAttendance.filter(a => a.status?.toLowerCase() === 'present').length
    const absent = childAttendance.filter(a => a.status?.toLowerCase() === 'absent').length
    const pct = total > 0 ? Math.round((present / total) * 100) : null
    return { total, present, absent, pct }
  }, [childAttendance])

  const gradeStats = useMemo(() => {
    const scored = childGrades.map(g => {
      if (typeof g.percentage === 'number') return g.percentage
      const score = Number(g.score || 0)
      const total = Number(g.total_grade || g.total_questions || g.max_score || 0)
      if (total > 0) return (score / total) * 100
      return null
    }).filter(v => v !== null && !isNaN(v))

    const avg = scored.length > 0 ? scored.reduce((a, b) => a + b, 0) / scored.length : null
    return { count: childGrades.length, avg }
  }, [childGrades])

  // Last 7 days attendance
  const recentAtt = useMemo(() => {
    const cutoff = new Date()
    cutoff.setDate(cutoff.getDate() - 7)
    return childAttendance
      .filter(a => new Date(a.date) >= cutoff)
      .sort((a, b) => new Date(b.date) - new Date(a.date))
  }, [childAttendance])

  // Last 5 grades
  const recentGrades = useMemo(
    () => [...childGrades].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)).slice(0, 5),
    [childGrades]
  )

  return (
    <>
      <PageHeader
        title="Weekly Reports"
        subtitle="A summary of your children's attendance and academic performance."
      />

      {loading && <p className="muted" style={{ padding: '2rem 0' }}>Loading report data…</p>}
      {!loading && error && <p className="teaching-error" style={{ marginBottom: '1.5rem' }}>{error}</p>}

      {!loading && !error && children.length === 0 && (
        <Card>
          <p className="muted" style={{ padding: '2rem', textAlign: 'center' }}>
            No children linked to your account.
          </p>
        </Card>
      )}

      {!loading && !error && children.length > 0 && (
        <>
          {/* Child Selector */}
          {children.length > 1 && (
            <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
              {children.map(c => {
                const name = displayChildName(c)
                const isActive = c.id === selectedChild
                return (
                  <button
                    key={c.id}
                    onClick={() => setSelectedChild(c.id)}
                    style={{
                      padding: '0.45rem 1.1rem',
                      borderRadius: '999px',
                      border: isActive ? 'none' : '1px solid var(--border-color, #eaeaea)',
                      background: isActive ? '#6366f1' : 'var(--bg-card, #fff)',
                      color: isActive ? '#fff' : 'var(--text-muted, #6b7280)',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    {name}
                  </button>
                )
              })}
            </div>
          )}

          {/* KPI Summary Row */}
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <StatBadge label="Attendance Rate" value={formatPct(attStats.pct)} color={getGradeColor(attStats.pct)} />
            <StatBadge label="Sessions Present" value={attStats.present} color="#10b981" />
            <StatBadge label="Sessions Absent" value={attStats.absent} color="#ef4444" />
            <StatBadge label="Avg Grade" value={formatPct(gradeStats.avg)} color={getGradeColor(gradeStats.avg)} />
            <StatBadge label="Grades Recorded" value={gradeStats.count} color="#6366f1" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            {/* Recent Attendance */}
            <Card title={`${childName} — Last 7 Days Attendance`}>
              {recentAtt.length === 0 ? (
                <p className="muted" style={{ margin: 0 }}>No attendance records in the last 7 days.</p>
              ) : (
                <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                  {recentAtt.map((a) => (
                    <li key={a.id} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '0.6rem 0', borderBottom: '1px solid var(--border-color, #eaeaea)',
                      fontSize: '0.9rem'
                    }}>
                      <span style={{ color: 'var(--text-secondary, #374151)' }}>
                        {a.date}
                        {a.subject_name ? <span style={{ color: 'var(--text-muted, #6b7280)', marginLeft: '0.5rem', fontSize: '0.8rem' }}>· {a.subject_name}</span> : null}
                      </span>
                      <span style={{
                        fontWeight: 600,
                        color: getStatusColor(a.status),
                        textTransform: 'capitalize',
                        background: getStatusColor(a.status) + '18',
                        padding: '0.2rem 0.65rem',
                        borderRadius: '999px',
                        fontSize: '0.8rem',
                      }}>
                        {a.status_display || a.status}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            {/* Recent Grades */}
            <Card title={`${childName} — Recent Grades`}>
              {recentGrades.length === 0 ? (
                <p className="muted" style={{ margin: 0 }}>No grades recorded yet.</p>
              ) : (
                <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                  {recentGrades.map((g) => {
                    const pctValue = typeof g.percentage === 'number' ? g.percentage : (
                      (g.total_grade || g.total_questions || g.max_score) > 0 ? (g.score / (g.total_grade || g.total_questions || g.max_score)) * 100 : null
                    )
                    return (
                      <li key={g.id} style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '0.6rem 0', borderBottom: '1px solid var(--border-color, #eaeaea)',
                        fontSize: '0.9rem'
                      }}>
                        <div>
                          <span style={{ fontWeight: 600, color: 'var(--text-main, #111827)' }}>
                            {g.exam_title || g.exam_name || `Exam #${g.exam}`}
                          </span>
                          {g.subject_name && (
                            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted, #6b7280)', marginLeft: '0.5rem' }}>
                              · {g.subject_name}
                            </span>
                          )}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ color: 'var(--text-secondary, #374151)', fontSize: '0.85rem' }}>
                            {g.score}/{g.total_grade || g.total_questions || g.max_score || '—'}
                          </span>
                          <span style={{
                            fontWeight: 700,
                            color: getGradeColor(pctValue),
                            background: getGradeColor(pctValue) + '18',
                            padding: '0.2rem 0.65rem',
                            borderRadius: '999px',
                            fontSize: '0.8rem',
                          }}>
                            {formatPct(pctValue)}
                          </span>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              )}
            </Card>
          </div>


        </>
      )}
    </>
  )
}
