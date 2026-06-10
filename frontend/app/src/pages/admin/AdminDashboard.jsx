import { useCallback, useEffect, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { RecentActivity } from '../../components/dashboard/RecentActivity'
import { StatCard } from '../../components/dashboard/StatCard'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

// ── tiny helpers ─────────────────────────────────────────────────────────────

function fmt(n, suffix = '') {
  if (n == null) return 'N/A'
  return `${n}${suffix}`
}

function ChartSkeleton() {
  return <div className="dash-chart-skeleton" aria-hidden="true" />
}

function ChartEmpty({ icon = '📊', text = 'No data yet' }) {
  return (
    <div className="dash-chart-empty">
      <span className="dash-chart-empty-icon">{icon}</span>
      <span className="dash-chart-empty-text">{text}</span>
    </div>
  )
}

function allZero(arr, key) {
  return arr.every((d) => !d[key] || d[key] === 0)
}

// ── stat card definitions ─────────────────────────────────────────────────────

const STAT_DEFS = [
  { key: 'students', label: 'Total Students',    icon: 'users',   tone: 'indigo' },
  { key: 'teachers', label: 'Total Teachers',    icon: 'layers',  tone: 'violet' },
  { key: 'classes',  label: 'Total Classes',     icon: 'camera',  tone: 'emerald' },
  { key: 'att',      label: 'Attendance (week)', icon: 'chart',   tone: 'amber' },
]

function resolveStats(data) {
  if (!data) return STAT_DEFS.map((d) => ({ ...d, value: '—', hint: '' }))
  return [
    { ...STAT_DEFS[0], value: fmt(data.total_students),  hint: 'Enrolled students' },
    { ...STAT_DEFS[1], value: fmt(data.total_teachers),  hint: 'Active teachers' },
    { ...STAT_DEFS[2], value: fmt(data.total_classes),   hint: `${data.total_subjects ?? 0} subjects` },
    {
      ...STAT_DEFS[3],
      value: data.attendance_rate != null ? `${data.attendance_rate}%` : 'N/A',
      hint: data.attendance_rate != null ? 'This week school-wide' : 'No attendance this week',
    },
  ]
}

// ── custom tooltip shared by both charts ──────────────────────────────────────

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="dash-chart-tooltip">
      <span className="dash-chart-tooltip-label">{label}</span>
      {payload.map((p) => (
        <span key={p.dataKey} className="dash-chart-tooltip-value" style={{ color: p.color }}>
          {p.name}: {p.value}
        </span>
      ))}
    </div>
  )
}

// ── main component ────────────────────────────────────────────────────────────

export function AdminDashboard() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const fetchDashboard = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch('/users/admin-dashboard/')
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Server error ${res.status}`)
      }
      setData(await res.json())
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data.')
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
  const weekAtt  = data?.weekly_attendance ?? []
  const subjScores = data?.subject_scores ?? []
  const activity = data?.recent_activity  ?? []

  const weekEmpty  = !loading && allZero(weekAtt, 'present') && allZero(weekAtt, 'absent')
  const subjEmpty  = !loading && subjScores.length === 0

  return (
    <>
      <PageHeader
        title="Admin overview"
        subtitle="School-wide metrics, attendance trends, and latest activity."
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

        {/* ── Charts row ── */}
        <div className="dash-charts-row">

          {/* Attendance dual-line chart */}
          <div className="dash-chart-card">
            <h3 className="dash-chart-card-title">Attendance this week</h3>
            <div className="dash-chart-inner">
              {loading ? <ChartSkeleton /> : weekEmpty ? (
                <ChartEmpty icon="📅" text="No attendance records this week" />
              ) : (
                <ResponsiveContainer width="100%" height={320}>
                  <AreaChart data={weekAtt} margin={{ top: 20, right: 30, left: 10, bottom: 50 }}>
                    <defs>
                      <linearGradient id="adminPresentFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#4f46e5" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#4f46e5" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="adminAbsentFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#dc2626" stopOpacity={0.2} />
                        <stop offset="100%" stopColor="#dc2626" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--dash-chart-grid, #e2e8f0)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} angle={-30} textAnchor="end" height={50} tickMargin={12} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} width={40} allowDecimals={false} />
                    <Tooltip content={(props) => <ChartTooltip {...props} />} />
                    <Legend iconSize={8} wrapperStyle={{ fontSize: '11px', paddingTop: '12px' }} />
                    <Area type="monotone" dataKey="present" name="Present" stroke="#4f46e5" strokeWidth={2.5} fill="url(#adminPresentFill)" dot={{ fill: '#4f46e5', r: 3, strokeWidth: 0 }} activeDot={{ r: 5 }} />
                    <Area type="monotone" dataKey="absent"  name="Absent"  stroke="#dc2626" strokeWidth={2} fill="url(#adminAbsentFill)"  dot={{ fill: '#dc2626', r: 3, strokeWidth: 0 }} activeDot={{ r: 5 }} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Subject score breakdown */}
          <div className="dash-chart-card">
            <h3 className="dash-chart-card-title">Avg score by subject</h3>
            <div className="dash-chart-inner">
              {loading ? <ChartSkeleton /> : subjEmpty ? (
                <ChartEmpty icon="📚" text="No grades recorded yet" />
              ) : (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={subjScores} margin={{ top: 20, right: 30, left: 10, bottom: 70 }} barCategoryGap="18%">
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--dash-chart-grid, #e2e8f0)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} angle={-40} textAnchor="end" height={70} tickMargin={18} interval={0} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} width={40} allowDecimals={false} domain={[0, 100]} />
                    <Tooltip content={(props) => <ChartTooltip {...props} />} cursor={{ fill: 'rgba(99,102,241,0.08)' }} />
                    <Bar dataKey="value" name="Avg %" fill="#7c3aed" radius={[8, 8, 0, 0]} maxBarSize={52} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        {/* ── Recent Activity ── */}
        <RecentActivity
          title="Recent activity"
          items={activity}
          loading={loading}
        />

      </div>
    </>
  )
}
