export function Card({ title, children, className = '' }) {
  return (
    <section className={`ui-card ${className}`.trim()}>
      {title ? <h2 className="ui-card-title">{title}</h2> : null}
      <div className="ui-card-body">{children}</div>
    </section>
  )
}
