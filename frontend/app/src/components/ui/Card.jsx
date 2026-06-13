export function Card({ title, children, className = '', style }) {
  return (
    <section className={`ui-card ${className}`.trim()} style={style}>
      {title ? <h2 className="ui-card-title">{title}</h2> : null}
      <div className="ui-card-body">{children}</div>
    </section>
  )
}
