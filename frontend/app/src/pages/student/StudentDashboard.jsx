import { useCallback, useEffect, useState } from 'react'
import { DashboardCharts } from '../../components/dashboard/DashboardCharts'
import { RecentActivity } from '../../components/dashboard/RecentActivity'
import { StatCard } from '../../components/dashboard/StatCard'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

// ── stat card definitions ──────────────────────────────────────────────────────
const STAT_DEFS = [
  { key: 'attendance', label: 'Attendance Rate',  icon: 'camera',  tone: 'indigo' },
  { key: 'avg',        label: 'Avg. Score',        icon: 'chart',   tone: 'violet' },
  { key: 'subjects',   label: 'My Subjects',       icon: 'layers',  tone: 'emerald' },
  { key: 'exams',      label: 'Exams Taken',       icon: 'spark',   tone: 'amber' },
]

function resolveStats(data) {
  if (!data) return STAT_DEFS.map((d) => ({ ...d, value: '—', hint: '' }))
  return [
    {
      ...STAT_DEFS[0],
      value: data.attendance_rate != null ? `${data.attendance_rate}%` : 'N/A',
      hint: data.attendance_rate != null ? 'Overall attendance' : 'No records yet',
    },
    {
      ...STAT_DEFS[1],
      value: data.avg_score != null ? `${data.avg_score}%` : 'N/A',
      hint: data.avg_score != null ? 'Across all exams' : 'No grades yet',
    },
    { ...STAT_DEFS[2], value: String(data.subjects_count), hint: 'Enrolled subjects' },
    { ...STAT_DEFS[3], value: String(data.exams_taken),    hint: 'Graded assessments' },
  ]
}

// ── main component ────────────────────────────────────────────────────────────
export function StudentDashboard() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const fetchDashboard = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch('/students/dashboard/')
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Server error ${res.status}`)
      }
      setData(await res.json())
    } catch (err) {
      setError(err.message || 'Failed to load dashboard.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboard()
    const onVisible = () => {
      if (document.visibilityState === 'visible') fetchDashboard()
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [fetchDashboard])

  const stats    = resolveStats(data)
  const activity = data?.recent_grades ?? []

  return (
    <>
      <PageHeader
        title="Student portal"
        subtitle="Track your attendance, scores, and learning progress."
      />

      {/* Error banner */}
      {error && !loading && (
        <div className="dash-error-card" role="alert">
          <span className="dash-error-icon">⚠️</span>
          <div className="dash-error-body">
            <p className="dash-error-title">Could not load dashboard</p>
            <p className="dash-error-message">{error}</p>
            <button className="dash-error-retry" onClick={fetchDashboard}>↺ Retry</button>
          </div>
        </div>
      )}

      <div className="dash-analytics">

        {/* ── Stat Cards ── */}
        <section className="dash-stats-grid" aria-label="Key metrics">
          {stats.map((s) => (
            <StatCard
              key={s.key}
              icon={s.icon}
              label={s.label}
              value={s.value}
              hint={s.hint}
              tone={s.tone}
              loading={loading}
            />
          ))}
        </section>

        {/* ── Charts ── */}
        <DashboardCharts
          trend={data?.attendance_trend ?? []}
          bars={data?.subject_scores    ?? []}
          areaTitle="Attendance (last 7 days)"
          barTitle="Score by subject"
          loading={loading}
        />

        {/* ── Recent Grades ── */}
        <RecentActivity
          title="Recent grades"
          items={activity}
          loading={loading}
        />

      </div>
    </>
  )
}
