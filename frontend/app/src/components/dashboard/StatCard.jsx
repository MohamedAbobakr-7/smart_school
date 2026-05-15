import { StatIcon } from './StatIcons'

const TONES = new Set(['indigo', 'violet', 'emerald', 'amber'])

export function StatCard({ icon = 'spark', label, value, hint, tone = 'indigo', loading = false }) {
  const safeTone = TONES.has(tone) ? tone : 'indigo'
  return (
    <article className={`dash-stat dash-stat--${safeTone}${loading ? ' dash-stat--loading' : ''}`}>
      <div className="dash-stat-top">
        <div className="dash-stat-icon-wrap" aria-hidden="true">
          <StatIcon name={icon} />
        </div>
        <span className="dash-stat-label">{label}</span>
      </div>
      <p className="dash-stat-value">
        {loading ? <span className="dash-skeleton" style={{ width: '4rem', height: '1.65rem', display: 'block' }} /> : value}
      </p>
      {hint ? (
        <p className="dash-stat-hint">
          {loading ? <span className="dash-skeleton" style={{ width: '7rem', height: '0.8rem', display: 'block', marginTop: '0.35rem' }} /> : hint}
        </p>
      ) : null}
    </article>
  )
}
