const toneDot = {
  indigo: 'dash-activity-dot--indigo',
  violet: 'dash-activity-dot--violet',
  emerald: 'dash-activity-dot--emerald',
  amber: 'dash-activity-dot--amber',
}

function SkeletonRow() {
  return (
    <li className="dash-activity-item" aria-hidden="true">
      <span className="dash-activity-dot dash-activity-dot--indigo" style={{ opacity: 0.2 }} />
      <div className="dash-activity-body" style={{ gap: '0.35rem', display: 'flex', flexDirection: 'column' }}>
        <span className="dash-skeleton" style={{ width: '55%', height: '0.85rem', display: 'block' }} />
        <span className="dash-skeleton" style={{ width: '35%', height: '0.75rem', display: 'block', marginTop: '0.25rem' }} />
      </div>
      <span className="dash-skeleton" style={{ width: '3.5rem', height: '0.75rem', display: 'block', flexShrink: 0 }} />
    </li>
  )
}

export function RecentActivity({ title = 'Recent activity', items = [], loading = false }) {
  return (
    <section className="dash-activity">
      <div className="dash-activity-head">
        <h3 className="dash-activity-title">{title}</h3>
        {!loading && (
          <span className="dash-activity-badge">{items.length} item{items.length !== 1 ? 's' : ''}</span>
        )}
      </div>

      {loading ? (
        <ul className="dash-activity-list">
          {[0, 1, 2, 3].map((i) => <SkeletonRow key={i} />)}
        </ul>
      ) : items.length === 0 ? (
        <p className="dash-activity-empty">No recent activity yet.</p>
      ) : (
        <ul className="dash-activity-list">
          {items.map((row) => (
            <li key={row.id} className="dash-activity-item">
              <span className={`dash-activity-dot ${toneDot[row.tone] || toneDot.indigo}`} aria-hidden="true" />
              <div className="dash-activity-body">
                <p className="dash-activity-item-title">{row.title}</p>
                <p className="dash-activity-item-sub">{row.subtitle}</p>
              </div>
              <time className="dash-activity-time">{row.time}</time>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
