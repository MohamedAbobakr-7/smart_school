import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
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
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString()
}

function formatPct(value) {
  if (value == null || Number.isNaN(value)) return '—'
  return `${Math.round(value)}%`
}

export function ParentGradesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const studentIdParam = searchParams.get('student_id')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [grades, setGrades] = useState([])
  const [childrenList, setChildrenList] = useState([])
  
  const [selectedChildId, setSelectedChildId] = useState(studentIdParam || '')

  useEffect(() => {
    let disposed = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const [gradesRes, studentsRes] = await Promise.all([
          apiFetch('/grades/'),
          apiFetch('/students/')
        ])

        const gradesData = gradesRes.ok ? await gradesRes.json().catch(() => []) : []
        const studentsData = studentsRes.ok ? await studentsRes.json().catch(() => []) : []

        if (!gradesRes.ok && !studentsRes.ok) {
          throw new Error('Failed to load grades and children data.')
        }

        const parsedGrades = parseList(gradesData)
        const parsedChildren = parseList(studentsData)

        if (!disposed) {
          setGrades(parsedGrades)
          setChildrenList(parsedChildren)
          
          if (!studentIdParam && parsedChildren.length > 0) {
            setSelectedChildId(String(parsedChildren[0].id))
          } else if (studentIdParam) {
            setSelectedChildId(studentIdParam)
          }
        }
      } catch (e) {
        if (!disposed) setError(e.message || 'Failed to load grades.')
      } finally {
        if (!disposed) setLoading(false)
      }
    })()
    return () => {
      disposed = true
    }
  }, []) // run once on mount

  // Sync state when URL param changes
  useEffect(() => {
    if (studentIdParam && studentIdParam !== selectedChildId) {
      setSelectedChildId(studentIdParam)
    }
  }, [studentIdParam])

  const handleChildChange = (e) => {
    const val = e.target.value
    setSelectedChildId(val)
    setSearchParams(val ? { student_id: val } : {})
  }

  const filteredGrades = useMemo(() => {
    if (!selectedChildId) return []
    return grades.filter((g) => String(g.student) === selectedChildId)
  }, [grades, selectedChildId])

  const averagePct = useMemo(() => {
    if (!filteredGrades.length) return null
    const values = filteredGrades
      .map((g) => {
        if (typeof g.percentage === 'number') return g.percentage
        const total = Number(g.total_grade || g.total_questions || 0)
        const score = Number(g.score || 0)
        if (total > 0) return (score / total) * 100
        return null
      })
      .filter((v) => v != null && !Number.isNaN(v))
    if (!values.length) return null
    return values.reduce((a, b) => a + b, 0) / values.length
  }, [filteredGrades])

  return (
    <>
      <PageHeader 
        title="Children's Grades" 
        subtitle="Track exam results and academic performance." 
      />

      <div className="grid-cards" style={{ marginBottom: '1.5rem' }}>
        <Card title="Select Child">
          {loading ? (
            <p className="muted">Loading children...</p>
          ) : (
            <select 
              className="login-input" 
              value={selectedChildId} 
              onChange={handleChildChange}
              style={{ maxWidth: '300px', cursor: 'pointer' }}
            >
              {childrenList.length === 0 && <option value="">No children found</option>}
              {childrenList.map(child => {
                const dn = (child.user_display_name || '').trim()
                const name =
                  dn ||
                  (child.user?.first_name
                    ? `${child.user.first_name} ${child.user.last_name || ''}`.trim()
                    : '') ||
                  child.user?.username ||
                  `Student #${child.student_id}`
                return (
                  <option key={child.id} value={String(child.id)}>
                    {name}
                  </option>
                )
              })}
            </select>
          )}
        </Card>

        <Card title="Average Grade">
          {loading ? (
            <p className="muted">Calculating average...</p>
          ) : selectedChildId ? (
            <p className="student-grade-average" style={{ 
              color: averagePct != null && averagePct < 50 ? 'var(--ss-danger-bold)' : 'inherit'
            }}>
              {formatPct(averagePct)}
            </p>
          ) : (
            <p className="muted">—</p>
          )}
        </Card>
      </div>

      <Card title="Grades Table">
        {loading ? <p className="muted">Loading grades...</p> : null}
        {!loading && error ? <p className="teaching-error">{error}</p> : null}

        {!loading && !error ? (
          !selectedChildId ? (
            <div className="student-grades-empty">
              <p className="muted">Please select a child to view their grades.</p>
            </div>
          ) : filteredGrades.length ? (
            <div className="feature-table-wrap">
              <table className="feature-table student-grades-table">
                <thead>
                  <tr>
                    <th>Subject</th>
                    <th>Exam</th>
                    <th>Score</th>
                    <th>Total</th>
                    <th>Percentage</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredGrades.map((g) => {
                    const isLow = g.percentage != null ? g.percentage < 50 : ((g.total_grade || g.total_questions) > 0 && g.score / (g.total_grade || g.total_questions) < 0.5)
                    return (
                      <tr key={g.id} style={{ 
                        background: isLow ? 'var(--ss-danger-bg)' : 'transparent'
                      }}>
                        <td>{g.subject_name || '—'}</td>
                        <td>{g.exam_name || '—'}</td>
                        <td style={{ color: isLow ? 'var(--ss-danger-bold)' : 'inherit', fontWeight: isLow ? 600 : 'normal' }}>
                          {g.score ?? '—'}
                        </td>
                        <td>{g.total_grade ?? g.total_questions ?? '—'}</td>
                        <td style={{ color: isLow ? 'var(--ss-danger-bold)' : 'inherit', fontWeight: isLow ? 600 : 'normal' }}>
                          {formatPct(g.percentage)}
                        </td>
                        <td>{formatDate(g.created_at)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="student-grades-empty">
              <p className="muted">No grades available for this child.</p>
            </div>
          )
        ) : null}
      </Card>
    </>
  )
}
