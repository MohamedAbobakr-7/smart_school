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
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString()
}

function formatPct(value) {
  if (value == null || Number.isNaN(value)) return '—'
  return `${Math.round(value)}%`
}

export function StudentGradesPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [grades, setGrades] = useState([])

  useEffect(() => {
    let disposed = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const res = await apiFetch('/grades/')
        const data = await res.json().catch(() => [])
        if (!res.ok) {
          throw new Error(data.detail || `Failed to load grades (${res.status})`)
        }
        if (!disposed) setGrades(parseList(data))
      } catch (e) {
        if (!disposed) setError(e.message || 'Failed to load grades.')
      } finally {
        if (!disposed) setLoading(false)
      }
    })()
    return () => {
      disposed = true
    }
  }, [])

  const averagePct = useMemo(() => {
    if (!grades.length) return null
    const values = grades
      .map((g) => {
        if (typeof g.percentage === 'number') return g.percentage
        const total = Number(g.total_questions || 0)
        const score = Number(g.score || 0)
        if (total > 0) return (score / total) * 100
        return null
      })
      .filter((v) => v != null && !Number.isNaN(v))
    if (!values.length) return null
    return values.reduce((a, b) => a + b, 0) / values.length
  }, [grades])

  return (
    <>
      <PageHeader title="Grades" subtitle="Your exam results across subjects." />

      <div className="grid-cards">
        <Card title="Average Grade">
          {loading ? (
            <p className="muted">Calculating average...</p>
          ) : (
            <p className="student-grade-average">{formatPct(averagePct)}</p>
          )}
        </Card>
      </div>

      <Card title="Grades Table">
        {loading ? <p className="muted">Loading grades...</p> : null}
        {!loading && error ? <p className="teaching-error">{error}</p> : null}

        {!loading && !error ? (
          grades.length ? (
            <div className="feature-table-wrap">
              <table className="feature-table student-grades-table">
                <thead>
                  <tr>
                    <th>Subject</th>
                    <th>Exam</th>
                    <th>Score</th>
                    <th>Total</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {grades.map((g) => (
                    <tr key={g.id}>
                      <td>{g.subject_name || '—'}</td>
                      <td>{g.exam_name || '—'}</td>
                      <td>{g.score ?? '—'}</td>
                      <td>{g.total_questions ?? '—'}</td>
                      <td>{formatDate(g.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="student-grades-empty">
              <p className="muted">No grades available yet.</p>
            </div>
          )
        ) : null}
      </Card>
    </>
  )
}
