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

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const row = payload[0]?.payload
  const displayLabel = label ?? row?.name ?? '—'
  return (
    <div className="dash-chart-tooltip">
      <span className="dash-chart-tooltip-label">{displayLabel}</span>
      <span className="dash-chart-tooltip-value">{payload[0].value}</span>
    </div>
  )
}

function ChartEmpty({ icon = '📊', text = 'No data yet' }) {
  return (
    <div className="dash-chart-empty" role="status" aria-label={text}>
      <span className="dash-chart-empty-icon">{icon}</span>
      <span className="dash-chart-empty-text">{text}</span>
    </div>
  )
}

function ChartSkeleton() {
  return <div className="dash-chart-skeleton" aria-hidden="true" />
}

/** Returns true when every value in the dataset is zero */
function allZero(data) {
  return data.every((d) => d.value === 0)
}

export function DashboardCharts({
  trend = [],
  bars = [],
  areaTitle = '7-day trend',
  barTitle = 'Breakdown',
  loading = false,
}) {
  const trendEmpty = !loading && (!trend.length || allZero(trend))
  const barsEmpty  = !loading && (!bars.length  || allZero(bars))

  return (
    <div className="dash-charts-row">
      {/* ── Weekly Activity ── */}
      <div className="dash-chart-card">
        <h3 className="dash-chart-card-title">{areaTitle}</h3>
        <div className="dash-chart-inner">
          {loading ? (
            <ChartSkeleton />
          ) : trendEmpty ? (
            <ChartEmpty icon="📅" text="No sessions recorded this week" />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={trend} margin={{ top: 12, right: 12, left: -8, bottom: 0 }}>
                <defs>
                  <linearGradient id="dashAreaFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor="#6366f1" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--dash-chart-grid, #e2e8f0)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} width={36} allowDecimals={false} />
                <Tooltip content={(props) => <ChartTooltip {...props} />} cursor={{ stroke: '#c7d2fe', strokeWidth: 1 }} />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#4f46e5"
                  strokeWidth={2.5}
                  fill="url(#dashAreaFill)"
                  dot={{ fill: '#4f46e5', strokeWidth: 0, r: 3 }}
                  activeDot={{ r: 5, stroke: '#fff', strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── Assessment Mix ── */}
      <div className="dash-chart-card">
        <h3 className="dash-chart-card-title">{barTitle}</h3>
        <div className="dash-chart-inner">
          {loading ? (
            <ChartSkeleton />
          ) : barsEmpty ? (
            <ChartEmpty icon="📝" text="No assessments created yet" />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={bars} margin={{ top: 12, right: 12, left: -8, bottom: 0 }} barCategoryGap="18%">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--dash-chart-grid, #e2e8f0)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} width={36} allowDecimals={false} />
                <Tooltip content={(props) => <ChartTooltip {...props} />} cursor={{ fill: 'rgba(99, 102, 241, 0.08)' }} />
                <Bar dataKey="value" fill="#7c3aed" radius={[8, 8, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
