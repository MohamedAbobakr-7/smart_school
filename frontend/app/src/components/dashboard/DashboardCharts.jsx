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
import { useChartColors } from '../../hooks/useChartColors'

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
  const colors = useChartColors()
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
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={trend} margin={{ top: 20, right: 30, left: 10, bottom: 50 }}>
                <defs>
                  <linearGradient id="dashAreaFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor={colors.areaFill} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={colors.areaFill} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.gridStroke} vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: colors.tickFill }} axisLine={false} tickLine={false} angle={-30} textAnchor="end" height={50} tickMargin={12} />
                <YAxis tick={{ fontSize: 11, fill: colors.tickFill }} axisLine={false} tickLine={false} width={36} allowDecimals={false} />
                <Tooltip content={(props) => <ChartTooltip {...props} />} cursor={{ stroke: colors.cursorStroke, strokeWidth: 1 }} />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={colors.areaStroke}
                  strokeWidth={2.5}
                  fill="url(#dashAreaFill)"
                  dot={{ fill: colors.areaStroke, strokeWidth: 0, r: 3 }}
                  activeDot={{ r: 5, stroke: colors.dotStroke, strokeWidth: 2 }}
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
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={bars} margin={{ top: 20, right: 30, left: 10, bottom: 70 }} barCategoryGap="18%">
                <CartesianGrid strokeDasharray="3 3" stroke={colors.gridStroke} vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: colors.tickFill }} axisLine={false} tickLine={false} angle={-40} textAnchor="end" height={70} tickMargin={18} interval={0} />
                <YAxis tick={{ fontSize: 11, fill: colors.tickFill }} axisLine={false} tickLine={false} width={36} allowDecimals={false} />
                <Tooltip content={(props) => <ChartTooltip {...props} />} cursor={{ fill: colors.cursorFill }} />
                <Bar dataKey="value" fill={colors.barFill} radius={[8, 8, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
