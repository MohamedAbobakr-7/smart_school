import { Card } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'

export function PlaceholderPage({ title, apiHint, children }) {
  return (
    <>
      <PageHeader title={title} subtitle="UI shell — wire to Django REST when ready." />
      <Card title="API">
        {apiHint ? (
          <p className="muted">{apiHint}</p>
        ) : (
          <p className="muted">Use <code>apiFetch</code> from <code>src/lib/api.js</code> with the matching endpoint.</p>
        )}
        {children}
      </Card>
    </>
  )
}
