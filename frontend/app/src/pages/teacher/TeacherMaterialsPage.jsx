import { useEffect, useState, useMemo } from 'react'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch, apiFetchAll } from '../../lib/api'
import { useTeacherProfile } from '../../hooks/useTeacherProfile'

export function TeacherMaterialsPage() {
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [materials, setMaterials] = useState([])
  const { teacher: teacherProfile, mySubjectIds } = useTeacherProfile()
  const [allSubjects, setAllSubjects] = useState([])

  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadDescription, setUploadDescription] = useState('')
  const [uploadSubjectId, setUploadSubjectId] = useState('')
  const [uploadFile, setUploadFile] = useState(null)

  const subjects = useMemo(() => {
    if (mySubjectIds.length === 0) return []
    return allSubjects.filter((s) => mySubjectIds.includes(Number(s.id)))
  }, [allSubjects, mySubjectIds])

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const [materialsData, subjectsData] = await Promise.all([
        apiFetchAll('/materials/'),
        apiFetchAll('/subjects/')
      ])
      setMaterials(materialsData)
      setAllSubjects(subjectsData)
    } catch (e) {
      setError(e.message || 'Failed to load materials.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  function handleFileChange(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploadFile(file)
  }

  async function handleUpload(e) {
    e.preventDefault()
    if (!uploadFile) {
      alert('Please select a file to upload.')
      return
    }
    if (!uploadSubjectId) {
      alert('Please select a subject.')
      return
    }
    setBusy(true)

    try {
      const fd = new FormData()
      fd.append('title', uploadTitle.trim())
      fd.append('description', uploadDescription.trim())
      fd.append('subject', uploadSubjectId)
      fd.append('file', uploadFile)

      const res = await apiFetch('/materials/', {
        method: 'POST',
        body: fd,
      })

      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail || 'Upload failed')
      }

      setShowUploadModal(false)
      setUploadTitle('')
      setUploadDescription('')
      setUploadSubjectId('')
      setUploadFile(null)
      
      await loadData()
    } catch (err) {
      alert(err.message || 'Failed to upload material.')
    } finally {
      setBusy(false)
    }
  }

  async function deleteMaterial(id) {
    if (!window.confirm('Are you sure you want to delete this material?')) return
    setBusy(true)
    try {
      const res = await apiFetch(`/materials/${id}/`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Delete failed')
      await loadData()
    } catch (err) {
      alert(err.message || 'Failed to delete material.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Educational Materials"
        subtitle="Upload and manage PDF lectures and documents for your subjects."
      />

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Your Uploaded Materials</h2>
          <button className="btn btn-primary" onClick={() => setShowUploadModal(true)}>
            + Upload Material
          </button>
        </div>

        {loading ? <p className="muted">Loading materials...</p> : null}
        {!loading && error ? <p className="feature-error">{error}</p> : null}

        {!loading && !error && materials.length === 0 && (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#6b7280', background: '#f9fafb', borderRadius: '8px', border: '1px dashed #d1d5db' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📄</div>
            <p style={{ margin: 0 }}>No materials uploaded yet. Click "Upload Material" to share files with your students.</p>
          </div>
        )}

        {!loading && !error && materials.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table className="feature-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Subject</th>
                  <th>Description</th>
                  <th>Date Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {materials.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{m.title}</div>
                      <a href={m.file_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.8rem', color: 'var(--primary-color)', textDecoration: 'none' }}>
                        View File ↗
                      </a>
                    </td>
                    <td>{m.subject_name || m.subject}</td>
                    <td style={{ maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {m.description || '—'}
                    </td>
                    <td>{new Date(m.created_at).toLocaleDateString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn btn-ghost btn-xs" style={{ color: '#dc2626' }} onClick={() => deleteMaterial(m.id)} disabled={busy}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* UPLOAD MODAL */}
      {showUploadModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ background: '#fff', borderRadius: '16px', width: 'min(500px, 100%)', padding: '2rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}>
            <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.25rem' }}>Upload Educational Material</h2>
            <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Title *</label>
                <input required className="login-input login-input--plain" value={uploadTitle} onChange={e => setUploadTitle(e.target.value)} placeholder="e.g. Chapter 1: Introduction" />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Subject *</label>
                <select required className="login-input login-input--plain" value={uploadSubjectId} onChange={e => setUploadSubjectId(e.target.value)}>
                  <option value="">— Select Subject —</option>
                  {subjects.map(s => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Description (Optional)</label>
                <textarea className="login-input login-input--plain" value={uploadDescription} onChange={e => setUploadDescription(e.target.value)} rows={3} placeholder="Add any notes about this file..." />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Document File (PDF, DOCX) *</label>
                <div style={{ border: '1px solid #eaeaea', borderRadius: '8px', padding: '0.5rem', background: '#f9fafb' }}>
                  <input type="file" required accept=".pdf,.doc,.docx,.ppt,.pptx" onChange={handleFileChange} />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #eaeaea' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowUploadModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Uploading...' : 'Upload'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
