import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

function getInitials(name) {
  if (!name) return 'S'
  const parts = name.trim().split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.substring(0, 2).toUpperCase()
}

export function ParentChildrenPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [children, setChildren] = useState([])

  useEffect(() => {
    let disposed = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const res = await apiFetch('/students/')
        const json = await res.json().catch(() => [])
        if (!res.ok) throw new Error(json.detail || 'Failed to load children')
        
        const list = parseList(json)
        if (!disposed) setChildren(list)
      } catch (err) {
        if (!disposed) setError(err.message || 'Failed to fetch children')
      } finally {
        if (!disposed) setLoading(false)
      }
    })()
    return () => { disposed = true }
  }, [])

  return (
    <>
      <PageHeader
        title="My Children"
        subtitle="Manage your children's profiles, attendance, and grades."
      />

      {loading && <p className="muted">Loading children...</p>}
      {!loading && error && <p className="teaching-error">{error}</p>}
      
      {!loading && !error && children.length === 0 && (
        <Card>
          <p className="muted" style={{ padding: '2rem 1rem', textAlign: 'center', margin: 0 }}>
            No children profiles found linked to your account.
          </p>
        </Card>
      )}

      {!loading && !error && children.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {children.map((child) => {
            const dn = (child.user_display_name || '').trim()
            const childName =
              dn ||
              (child.user?.first_name
                ? `${child.user.first_name} ${child.user.last_name || ''}`.trim()
                : '') ||
              child.user?.username ||
              `Student #${child.student_id}`
            
            const classLabel = child.class_level || child.class_id || 'Class not assigned'

            return (
              <Card 
                key={child.id} 
                className="hoverable-card"
              >
                <div 
                  style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer', marginBottom: '1.25rem' }}
                  onClick={() => navigate(`/parent/children/${child.id}`)}
                >
                  {child.photo ? (
                    <img 
                      src={child.photo} 
                      alt={childName} 
                      style={{ width: '60px', height: '60px', borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--border-color)' }}
                    />
                  ) : (
                    <div style={{ 
                      width: '60px', height: '60px', borderRadius: '50%', 
                      background: 'var(--ss-primary-light)', color: 'var(--ss-primary)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '1.5rem', fontWeight: 'bold', border: '2px solid var(--ss-primary-border)'
                    }}>
                      {getInitials(childName)}
                    </div>
                  )}
                  
                  <div>
                    <h3 style={{ margin: '0 0 0.25rem', fontSize: '1.1rem', color: 'var(--text-color)' }}>
                      {childName}
                    </h3>
                    <div style={{ fontSize: '0.85rem', color: 'var(--ss-text-muted)', display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
                      <span>ID: {child.student_id}</span>
                      <span>Class: {classLabel}</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                  <button 
                    className="btn btn-secondary" 
                    style={{ flex: 1, padding: '0.4rem' }}
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(`/parent/attendance?student_id=${child.id}`)
                    }}
                  >
                    View Attendance
                  </button>
                  <button 
                    className="btn btn-secondary" 
                    style={{ flex: 1, padding: '0.4rem' }}
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(`/parent/grades?student_id=${child.id}`)
                    }}
                  >
                    View Grades
                  </button>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </>
  )
}
