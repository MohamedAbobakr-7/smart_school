import { useCallback, useEffect, useState } from 'react'
import { DashboardCharts } from '../../components/dashboard/DashboardCharts'
import { RecentActivity } from '../../components/dashboard/RecentActivity'
import { StatCard } from '../../components/dashboard/StatCard'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

// ── stat card definitions ──────────────────────────────────────────────────────
const STAT_DEFS = [
  { key: 'children',  label: 'My Children',      icon: 'users',  tone: 'indigo' },
  { key: 'att',       label: 'Avg Attendance',    icon: 'camera', tone: 'emerald' },
  { key: 'score',     label: 'Avg Score',         icon: 'chart',  tone: 'violet' },
  { key: 'notifs',    label: 'Notifications',     icon: 'spark',  tone: 'amber' },
]

function resolveStats(data) {
  if (!data) return STAT_DEFS.map((d) => ({ ...d, value: '—', hint: '' }))
  return [
    { ...STAT_DEFS[0], value: String(data.children_count),   hint: 'Enrolled children' },
    {
      ...STAT_DEFS[1],
      value: data.avg_attendance_rate != null ? `${data.avg_attendance_rate}%` : 'N/A',
      hint: data.avg_attendance_rate != null ? 'Across all children' : 'No records yet',
    },
    {
      ...STAT_DEFS[2],
      value: data.avg_score != null ? `${data.avg_score}%` : 'N/A',
      hint: data.avg_score != null ? 'Across all children' : 'No grades yet',
    },
    {
      ...STAT_DEFS[3],
      value: String(data.unread_notifications ?? 0),
      hint: 'Unread messages',
    },
  ]
}

// ── per-child summary cards ───────────────────────────────────────────────────
function ChildCard({ child }) {
  const attColor = child.attendance_rate == null
    ? 'var(--ss-text-muted)'
    : child.attendance_rate >= 80 ? 'var(--ss-success-bold)'
    : child.attendance_rate >= 60 ? 'var(--ss-warning-bold)'
    : 'var(--ss-danger-bold)'

  const scoreColor = child.avg_score == null
    ? 'var(--ss-text-muted)'
    : child.avg_score >= 75 ? 'var(--ss-success-bold)'
    : child.avg_score >= 50 ? 'var(--ss-warning-bold)'
    : 'var(--ss-danger-bold)'

  return (
    <div style={{
      background: 'var(--ss-bg-card)',
      border: '1px solid var(--ss-border-medium)',
      borderRadius: '14px',
      padding: '1.25rem 1.5rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
      boxShadow: '0 1px 6px rgba(0,0,0,0.05)',
    }}>
      {/* Avatar + name */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          width: '38px', height: '38px', borderRadius: '50%',
          background: 'var(--ss-auth-brand-gradient)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 700, fontSize: '1rem', flexShrink: 0,
        }}>
          {child.name?.[0]?.toUpperCase() ?? '?'}
        </div>
        <div>
          <p style={{ margin: 0, fontWeight: 700, fontSize: '0.92rem', color: 'var(--ss-text)' }}>{child.name}</p>
          <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--ss-text-faint)' }}>{child.student_id}</p>
        </div>
      </div>

      {/* Metrics */}
      <div style={{ display: 'flex', gap: '1.5rem' }}>
        <div>
          <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--ss-text-muted)', fontWeight: 500 }}>Attendance</p>
          <p style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: attColor }}>
            {child.attendance_rate != null ? `${child.attendance_rate}%` : 'N/A'}
          </p>
        </div>
        <div>
          <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--ss-text-muted)', fontWeight: 500 }}>Avg Score</p>
          <p style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: scoreColor }}>
            {child.avg_score != null ? `${child.avg_score}%` : 'N/A'}
          </p>
        </div>
      </div>
    </div>
  )
}

function ChildCardSkeleton() {
  return (
    <div style={{
      background: 'var(--ss-bg-card)', border: '1px solid var(--ss-border-medium)', borderRadius: '14px',
      padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <span className="dash-skeleton" style={{ width: 38, height: 38, borderRadius: '50%', display: 'block' }} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          <span className="dash-skeleton" style={{ width: '55%', height: '0.85rem', display: 'block' }} />
          <span className="dash-skeleton" style={{ width: '35%', height: '0.7rem',  display: 'block' }} />
        </div>
      </div>
      <div style={{ display: 'flex', gap: '1.5rem' }}>
        <span className="dash-skeleton" style={{ width: '4rem', height: '1.5rem', display: 'block' }} />
        <span className="dash-skeleton" style={{ width: '4rem', height: '1.5rem', display: 'block' }} />
      </div>
    </div>
  )
}

// ── main component ────────────────────────────────────────────────────────────
export function ParentDashboard() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const fetchDashboard = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch('/parents/dashboard/')
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
  const children = data?.children ?? []
  const activity = data?.recent_activity ?? []

  return (
    <>
      <PageHeader
        title="Parent portal"
        subtitle="Monitor your children's attendance, scores, and recent activity."
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

        {/* ── Per-child cards ── */}
        <section aria-label="Children overview">
          <h3 style={{ margin: '0 0 1rem', fontSize: '0.92rem', fontWeight: 700, color: 'var(--ss-text-secondary)', letterSpacing: '0.03em', textTransform: 'uppercase' }}>
            Children Overview
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
            {loading
              ? [0, 1].map((i) => <ChildCardSkeleton key={i} />)
              : children.length === 0
                ? <p style={{ color: 'var(--ss-text-faint)', fontSize: '0.85rem', gridColumn: '1/-1' }}>No children linked to your account.</p>
                : children.map((c) => <ChildCard key={c.id} child={c} />)
            }
          </div>
        </section>

        {/* ── Charts ── */}
        <DashboardCharts
          trend={data?.attendance_trend ?? []}
          bars={data?.subject_scores    ?? []}
          areaTitle="Attendance this week (combined)"
          barTitle="Score by subject (combined)"
          loading={loading}
        />

        {/* ── Recent Activity ── */}
        <RecentActivity
          title="Recent grades"
          items={activity}
          loading={loading}
        />

      </div>
    </>
  )
}
