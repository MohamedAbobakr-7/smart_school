import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

function getStatusColor(status) {
  switch (status?.toLowerCase()) {
    case 'present': return '#10b981' // green
    case 'absent': return '#ef4444' // red
    case 'late': return '#f97316' // orange
    default: return '#6b7280'
  }
}

export function ParentAttendancePage() {
  const [searchParams] = useSearchParams()
  const studentIdParam = searchParams.get('student_id')
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attendanceByStudent, setAttendanceByStudent] = useState({})

  useEffect(() => {
    let disposed = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const res = await apiFetch('/attendance/')
        const json = await res.json().catch(() => [])
        if (!res.ok) throw new Error(json.detail || 'Failed to load attendance')

        let records = parseList(json)
        
        // Filter by student_id if provided in URL
        if (studentIdParam) {
          records = records.filter(r => String(r.student) === studentIdParam)
        }
        
        // Group by student name
        const grouped = {}
        records.forEach((record) => {
          const name = record.student_name || `Student #${record.student}`
          if (!grouped[name]) grouped[name] = []
          grouped[name].push(record)
        })

        if (!disposed) setAttendanceByStudent(grouped)
      } catch (err) {
        if (!disposed) setError(err.message || 'Failed to fetch attendance')
      } finally {
        if (!disposed) setLoading(false)
      }
    })()
    return () => { disposed = true }
  }, [])

  return (
    <>
      <PageHeader
        title="Children's Attendance"
        subtitle="Track attendance records for all your children."
      />

      {loading && <p className="muted">Loading attendance data...</p>}
      {!loading && error && <p className="teaching-error">{error}</p>}

      {!loading && !error && Object.keys(attendanceByStudent).length === 0 && (
        <Card>
          <p className="muted">No attendance records found for your children.</p>
        </Card>
      )}

      {!loading && !error && Object.entries(attendanceByStudent).map(([studentName, records]) => (
        <Card key={studentName} title={studentName} style={{ marginBottom: '1.5rem' }}>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {records.map((r) => (
              <li 
                key={r.id} 
                style={{ 
                  padding: '0.75rem 0', 
                  borderBottom: '1px solid var(--border-color)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.95rem'
                }}
              >
                <span style={{ fontWeight: 500, color: 'var(--text-color)' }}>{studentName}</span>
                <span style={{ color: '#9ca3af' }}>—</span>
                <span style={{ color: 'var(--text-color)' }}>{r.date}</span>
                <span style={{ color: '#9ca3af' }}>—</span>
                <span style={{ 
                  fontWeight: 600, 
                  color: getStatusColor(r.status),
                  textTransform: 'capitalize' 
                }}>
                  {r.status_display || r.status}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </>
  )
}
