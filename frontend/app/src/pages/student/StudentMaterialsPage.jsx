import { useEffect, useState } from 'react'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetchAll } from '../../lib/api'

export function StudentMaterialsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [materials, setMaterials] = useState([])

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      // The backend MaterialViewSet restricts the student to see only their subjects' & class materials
      const materialsData = await apiFetchAll('/materials/')
      setMaterials(materialsData)
    } catch (e) {
      setError(e.message || 'Failed to load materials.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  return (
    <>
      <PageHeader
        title="Educational Materials"
        subtitle="Download PDF lectures and study documents for your enrolled subjects and class."
      />

      <Card>
        {loading ? <p className="muted">Loading materials...</p> : null}
        {!loading && error ? <p className="feature-error">{error}</p> : null}

        {!loading && !error && materials.length === 0 && (
          <div style={{ padding: '4rem 2rem', textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.5 }}>📚</div>
            <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.1rem' }}>No materials available</h3>
            <p style={{ color: 'var(--ss-text-muted)', margin: 0 }}>Your teachers haven't uploaded any documents for your class yet.</p>
          </div>
        )}

        {!loading && !error && materials.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
            {materials.map((m) => (
              <div 
                key={m.id} 
                style={{ 
                  border: '1px solid var(--ss-border)',
                  borderRadius: '12px',
                  padding: '1.25rem',
                  background: 'var(--ss-bg-main)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem'
                }}
              >
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                  <div style={{ fontSize: '2rem' }}>📄</div>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ margin: '0 0 0.25rem', fontSize: '1rem', color: 'var(--text-color)' }}>{m.title}</h3>
                    <div style={{ fontSize: '0.8rem', color: 'var(--primary-color)', fontWeight: 600 }}>{m.subject_name || m.subject}</div>
                    {m.target_classes_display && m.target_classes_display.length > 0 && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--ss-text-muted)', marginTop: '0.25rem' }}>
                        🏫 {m.target_classes_display.map((c) => c.name).join(', ')}
                      </div>
                    )}
                  </div>
                </div>
                
                {m.description && (
                  <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--ss-text-muted)', lineHeight: 1.5 }}>
                    {m.description}
                  </p>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--ss-border)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--ss-text-faint)' }}>
                    Uploaded {new Date(m.created_at).toLocaleDateString()}
                    <br />
                    by {m.uploaded_by_name}
                  </span>
                  
                  <a 
                    href={m.file_url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="btn btn-primary btn-xs"
                    style={{ textDecoration: 'none' }}
                  >
                    Download
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </>
  )
}
