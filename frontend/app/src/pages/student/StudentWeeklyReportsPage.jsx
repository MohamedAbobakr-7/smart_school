import { useCallback, useEffect, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

/* ── helpers ─────────────────────────────────────────────────────────────── */

function formatPct(v) {
  if (v == null || isNaN(v)) return '—'
  return `${Math.round(v)}%`
}

function getGradeColor(pct) {
  if (pct == null) return '#6b7280'
  if (pct >= 85) return '#10b981'
  if (pct >= 60) return '#f97316'
  return '#ef4444'
}

function getInsightIcon(level) {
  switch (level) {
    case 'positive': return '✅'
    case 'warning':  return '⚠️'
    default:         return '💡'
  }
}

function getInsightColor(level) {
  switch (level) {
    case 'positive': return '#10b981'
    case 'warning':  return '#ef4444'
    default:         return '#6366f1'
  }
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="dash-chart-tooltip">
      <span className="dash-chart-tooltip-label">{label}</span>
      <span className="dash-chart-tooltip-value">{payload[0].value}</span>
    </div>
  )
}

/* ── sub-components ──────────────────────────────────────────────────────── */

function StatBadge({ label, value, color }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      background: 'var(--bg-hover, #f1f5f9)', borderRadius: '12px',
      padding: '0.85rem 1.25rem', minWidth: '110px', flex: 1,
    }}>
      <span style={{ fontSize: '1.5rem', fontWeight: 700, color: color || '#6366f1' }}>{value}</span>
      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #6b7280)', marginTop: '0.2rem' }}>{label}</span>
    </div>
  )
}

function InsightItem({ level, text }) {
  return (
    <li style={{
      display: 'flex', alignItems: 'flex-start', gap: '0.6rem',
      padding: '0.55rem 0', borderBottom: '1px solid var(--border-color, #eaeaea)',
      fontSize: '0.9rem',
    }}>
      <span style={{ fontSize: '1rem', flexShrink: 0 }}>{getInsightIcon(level)}</span>
      <span style={{ color: getInsightColor(level), fontWeight: 500 }}>{text}</span>
    </li>
  )
}

/* ── week picker ─────────────────────────────────────────────────────────── */

function WeekPicker({ weekStart, weekEnd, onPrev, onNext, canGoNext }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '0.75rem',
      marginBottom: '1.5rem',
    }}>
      <button
        className="btn btn-ghost btn-xs"
        onClick={onPrev}
        style={{ borderRadius: '999px', padding: '0.35rem 0.9rem' }}
      >
        ← Previous
      </button>
      <span style={{
        fontWeight: 600, fontSize: '0.95rem',
        color: 'var(--text-main, #111827)',
      }}>
        {weekStart} → {weekEnd}
      </span>
      <button
        className="btn btn-ghost btn-xs"
        onClick={onNext}
        disabled={!canGoNext}
        style={{ borderRadius: '999px', padding: '0.35rem 0.9rem', opacity: canGoNext ? 1 : 0.4 }}
      >
        Next →
      </button>
    </div>
  )
}

/* ── main component ──────────────────────────────────────────────────────── */

export function StudentWeeklyReportsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)

  // Week navigation state
  const [weekStart, setWeekStart] = useState(null)
  const [weekEnd, setWeekEnd] = useState(null)
  const [canGoNext, setCanGoNext] = useState(false)

  const fetchReport = useCallback(async (ws, we) => {
    setLoading(true)
    setError('')
    try {
      let url = '/students/weekly-report/'
      if (ws && we) {
        url += `?week_start=${ws}&week_end=${we}`
      }
      const res = await apiFetch(url)
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Server error ${res.status}`)
      }
      const json = await res.json()
      setData(json)
      setWeekStart(json.week_start)
      setWeekEnd(json.week_end)

      // Can go next only if next week's start is before current real week's Monday
      const nextStart = new Date(json.week_start)
      nextStart.setDate(nextStart.getDate() + 7)
      const today = new Date()
      const thisMonday = new Date(today)
      thisMonday.setDate(today.getDate() - today.getDay() + 1)
      thisMonday.setHours(0, 0, 0, 0)
      setCanGoNext(nextStart < thisMonday)
    } catch (err) {
      setError(err.message || 'Failed to load weekly report.')
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load — default week (no params = last completed ISO week)
  useEffect(() => {
    fetchReport()
  }, [fetchReport])

  const handlePrev = () => {
    if (!weekStart || !weekEnd) return
    const prevStart = new Date(weekStart)
    prevStart.setDate(prevStart.getDate() - 7)
    const prevEnd = new Date(weekEnd)
    prevEnd.setDate(prevEnd.getDate() - 7)
    fetchReport(prevStart.toISOString().slice(0, 10), prevEnd.toISOString().slice(0, 10))
  }

  const handleNext = () => {
    if (!weekStart || !weekEnd) return
    const nextStart = new Date(weekStart)
    nextStart.setDate(nextStart.getDate() + 7)
    const nextEnd = new Date(weekEnd)
    nextEnd.setDate(nextEnd.getDate() + 7)
    fetchReport(nextStart.toISOString().slice(0, 10), nextEnd.toISOString().slice(0, 10))
  }

  // ── derived chart data ──────────────────────────────────────────────
  const attByDay = data?.attendance_stats?.by_day
  const attendanceChartData = attByDay
    ? attByDay.labels.map((label, i) => ({
        name: label,
        Present: attByDay.present[i] || 0,
        Absent: attByDay.absent[i] || 0,
      }))
    : []

  const subjData = data?.academic_stats?.by_subject
  const subjectChartData = subjData
    ? subjData.labels.map((label, i) => ({
        name: label,
        value: subjData.averages[i] || 0,
      }))
    : []

  const attStats = data?.attendance_stats || {}
  const acadStats = data?.academic_stats || {}
  const insights = data?.insights || []

  return (
    <>
      <PageHeader
        title="Weekly Report"
        subtitle="Your attendance and academic performance summary for the week."
      />

      {loading && <p className="muted" style={{ padding: '2rem 0' }}>Loading weekly report…</p>}
      {!loading && error && <p className="teaching-error" style={{ marginBottom: '1.5rem' }}>{error}</p>}

      {!loading && !error && data && (
        <>
          {/* Week navigation */}
          <WeekPicker
            weekStart={weekStart}
            weekEnd={weekEnd}
            onPrev={handlePrev}
            onNext={handleNext}
            canGoNext={canGoNext}
          />

          {/* KPI Summary Row */}
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <StatBadge
              label="Attendance Rate"
              value={formatPct(attStats.rate_percent)}
              color={getGradeColor(attStats.rate_percent)}
            />
            <StatBadge label="Present" value={attStats.present || 0} color="#10b981" />
            <StatBadge label="Absent" value={attStats.absent || 0} color="#ef4444" />
            <StatBadge
              label="Avg Score"
              value={formatPct(acadStats.avg_score_percent)}
              color={getGradeColor(acadStats.avg_score_percent)}
            />
            <StatBadge label="Grades" value={acadStats.grades_count || 0} color="#6366f1" />
          </div>

          {/* Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            {/* Attendance by day */}
            <Card title="Attendance by Day">
              {attendanceChartData.length === 0 ? (
                <p className="muted" style={{ margin: 0 }}>No attendance data for this week.</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={attendanceChartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="Present" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Absent" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>

            {/* Score by subject */}
            <Card title="Average Score by Subject">
              {subjectChartData.length === 0 ? (
                <p className="muted" style={{ margin: 0 }}>No graded subjects for this week.</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={subjectChartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
                    <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 12 }} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>

          {/* Insights */}
          <Card title="Insights">
            {insights.length === 0 ? (
              <p className="muted" style={{ margin: 0 }}>No insights for this week.</p>
            ) : (
              <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                {insights.map((ins, i) => (
                  <InsightItem key={i} level={ins.level} text={ins.text} />
                ))}
              </ul>
            )}
          </Card>
        </>
      )}
    </>
  )
}