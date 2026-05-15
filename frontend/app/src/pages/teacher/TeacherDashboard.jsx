import { useCallback, useEffect, useState } from 'react'
import { DashboardCharts } from '../../components/dashboard/DashboardCharts'
import { RecentActivity } from '../../components/dashboard/RecentActivity'
import { StatCard } from '../../components/dashboard/StatCard'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

// Tone cycle for the activity dot colours
const TONES = ['indigo', 'violet', 'emerald', 'amber']

/**
 * Map the recent_exams payload from the API into the shape
 * that <RecentActivity> expects.
 */
function buildActivityItems(recentExams = []) {
  return recentExams.map((exam, idx) => ({
    id: String(exam.id),
    title: exam.name,
    subtitle: `${exam.exam_type_display} · ${exam.subject_name}${exam.class_id ? ` · ${exam.class_id}` : ''}`,
    time: formatRelative(exam.created_at),
    tone: TONES[idx % TONES.length],
  }))
}

function formatRelative(isoString) {
  if (!isoString) return '—'
  const diff = Date.now() - new Date(isoString).getTime()
  const mins  = Math.floor(diff / 60_000)
  const hours = Math.floor(diff / 3_600_000)
  const days  = Math.floor(diff / 86_400_000)
  if (mins  < 1)   return 'Just now'
  if (mins  < 60)  return `${mins} min ago`
  if (hours < 24)  return `${hours} hr ago`
  if (days  === 1) return 'Yesterday'
  return `${days} days ago`
}

// Static card definitions — only values change at runtime
const STAT_DEFS = [
  { key: 'classes',  label: 'My Classes',       icon: 'layers',   tone: 'indigo' },
  { key: 'students', label: 'Students Taught',   icon: 'users',    tone: 'violet' },
  { key: 'sessions', label: 'Sessions This Week',icon: 'camera',   tone: 'emerald' },
  { key: 'avg',      label: 'Avg. Score',        icon: 'chart',    tone: 'amber' },
]

function resolveStats(data) {
  if (!data) return STAT_DEFS.map((d) => ({ ...d, value: '—', hint: '' }))
  return [
    { ...STAT_DEFS[0], value: String(data.my_classes),       hint: 'Assigned classes' },
    { ...STAT_DEFS[1], value: String(data.students_taught),  hint: 'Across your classes' },
    { ...STAT_DEFS[2], value: String(data.sessions_this_week), hint: 'Attendance sessions' },
    {
      ...STAT_DEFS[3],
      value: data.avg_score !== null && data.avg_score !== undefined
        ? `${data.avg_score}%`
        : 'N/A',
      hint: data.avg_score !== null ? 'From graded assessments' : 'No grades recorded yet',
    },
  ]
}

export function TeacherDashboard() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const fetchDashboard = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch('/teachers/dashboard/')
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Server error ${res.status}`)
      }
      const json = await res.json()
      setData(json)
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data.')
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch on mount; re-fetch whenever the tab becomes visible again
  useEffect(() => {
    fetchDashboard()

    const handleVisibility = () => {
      if (document.visibilityState === 'visible') fetchDashboard()
    }
    document.addEventListener('visibilitychange', handleVisibility)
    return () => document.removeEventListener('visibilitychange', handleVisibility)
  }, [fetchDashboard])

  const stats    = resolveStats(data)
  const activity = buildActivityItems(data?.recent_exams)

  return (
    <>
      <PageHeader
        title="Teacher workspace"
        subtitle="Your teaching load, sessions, and latest actions at a glance."
      />

      {/* Error banner — shown above the rest so the user can retry */}
      {error && !loading && (
        <div className="dash-error-card" role="alert">
          <span className="dash-error-icon">⚠️</span>
          <div className="dash-error-body">
            <p className="dash-error-title">Could not load dashboard</p>
            <p className="dash-error-message">{error}</p>
            <button className="dash-error-retry" onClick={fetchDashboard}>
              ↺ Retry
            </button>
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
          trend={data?.weekly_activity ?? []}
          bars={data?.assessment_mix   ?? []}
          areaTitle="Weekly activity"
          barTitle="Assessment mix"
          loading={loading}
        />

        {/* ── Recent Activity ── */}
        <RecentActivity
          title="Recent assessments"
          items={activity}
          loading={loading}
        />
      </div>
    </>
  )
}
