export function PageHeader({ title, subtitle }) {
  return (
    <header className="page-header">
      <h1 className="page-header-title">{title}</h1>
      {subtitle ? <p className="page-header-sub">{subtitle}</p> : null}
    </header>
  )
}
