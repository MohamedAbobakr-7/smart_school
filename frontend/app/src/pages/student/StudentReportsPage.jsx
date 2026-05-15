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

function prettyType(value) {
  if (!value) return 'General'
  return value.charAt(0).toUpperCase() + value.slice(1)
}

export function StudentReportsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reports, setReports] = useState([])
  const [activeReport, setActiveReport] = useState(null)

  useEffect(() => {
    let disposed = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const res = await apiFetch('/reports/')
        const json = await res.json().catch(() => [])
        if (!res.ok) throw new Error(json.detail || `Failed to load reports (${res.status})`)
        if (!disposed) setReports(parseList(json))
      } catch (e) {
        if (!disposed) setError(e.message || 'Failed to load reports.')
      } finally {
        if (!disposed) setLoading(false)
      }
    })()
    return () => {
      disposed = true
    }
  }, [])

  const cards = useMemo(() => reports, [reports])

  return (
    <>
      <PageHeader title="Reports" subtitle="View your generated academic, attendance, and general reports." />

      {loading ? <p className="muted">Loading reports...</p> : null}
      {!loading && error ? <p className="teaching-error">{error}</p> : null}

      {!loading && !error ? (
        cards.length ? (
          <div className="grid-cards student-reports-grid">
            {cards.map((report) => (
              <Card key={report.id} className="student-report-card">
                <h3 className="student-report-title">{report.title || 'Untitled report'}</h3>
                <p className="student-report-date">Date: {formatDate(report.generated_at)}</p>
                <p className="student-report-type">Type: {prettyType(report.report_type)}</p>
                <div className="feature-actions">
                  <button type="button" className="btn btn-primary btn-xs" onClick={() => setActiveReport(report)}>
                    View
                  </button>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <div className="student-reports-empty">
            <p className="muted">No reports available yet.</p>
          </div>
        )
      ) : null}

      {activeReport ? (
        <div className="report-modal-backdrop" role="dialog" aria-modal="true" aria-label="Report details">
          <div className="report-modal-card">
            <div className="report-modal-head">
              <div>
                <h3 className="report-modal-title">{activeReport.title || 'Report'}</h3>
                <p className="report-modal-sub">
                  {prettyType(activeReport.report_type)} · {formatDate(activeReport.generated_at)}
                </p>
              </div>
              <button type="button" className="btn btn-ghost btn-xs" onClick={() => setActiveReport(null)}>
                Close
              </button>
            </div>
            <div className="report-modal-body">
              {activeReport.content ? (
                <p className="report-modal-content">{activeReport.content}</p>
              ) : (
                <p className="muted">No details in this report.</p>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </>
  )
}
