import { useEffect, useMemo, useState, useCallback } from 'react'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch, apiFetchAll } from '../../lib/api'

// Helpers
function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

function fullName(user) {
  if (!user) return '—'
  const n = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
  return n || user.username || user.email || '—'
}

export function AdminStudentsPage() {
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [students, setStudents] = useState([])
  const [users, setUsers] = useState([])
  const [parents, setParents] = useState([])
  const [subjects, setSubjects] = useState([])
  const [classes, setClasses] = useState([])

  const [search, setSearch] = useState('')
  const [classFilter, setClassFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [backfillResult, setBackfillResult] = useState(null)
  const pageSize = 10

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createEmail, setCreateEmail] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [createClassId, setCreateClassId] = useState('')
  const [createParentId, setCreateParentId] = useState('')
  const [createSubjectIds, setCreateSubjectIds] = useState([])
  const [createPhotoFile, setCreatePhotoFile] = useState(null)
  const [createPhotoPreview, setCreatePhotoPreview] = useState(null)

  // Edit Modal
  const [editing, setEditing] = useState(null)
  const [editName, setEditName] = useState('')
  const [editEmail, setEditEmail] = useState('')
  const [editPassword, setEditPassword] = useState('')
  const [editStudentId, setEditStudentId] = useState('')
  const [editParentId, setEditParentId] = useState('')
  const [editSubjectIds, setEditSubjectIds] = useState([])
  const [editSchoolClassId, setEditSchoolClassId] = useState('')
  const [editPhotoFile, setEditPhotoFile] = useState(null)
  const [editPhotoPreview, setEditPhotoPreview] = useState(null)

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const [studentsData, usersData, parentsData, subjectsData, classesData] = await Promise.all([
        apiFetchAll('/students/'),
        apiFetchAll('/users/'),
        apiFetchAll('/parents/'),
        apiFetchAll('/subjects/'),
        apiFetchAll('/classes/'),
      ])
      setStudents(studentsData)
      setUsers(usersData)
      setParents(parentsData)
      setSubjects(subjectsData)
      setClasses(classesData)
    } catch (e) {
      setError(e.message || 'Failed to load student module.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const userById = useMemo(() => new Map(users.map((u) => [Number(u.id), u])), [users])
  const parentById = useMemo(() => new Map(parents.map((p) => [p.id, p])), [parents])
  const subjectById = useMemo(() => new Map(subjects.map((s) => [s.id, s])), [subjects])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return students.filter((s) => {
      if (classFilter !== 'all' && String(s.school_class) !== classFilter) return false

      if (q) {
        const u = userById.get(Number(s.user))
        const hay = `${s.student_id || ''} ${u?.username || ''} ${u?.email || ''} ${u?.first_name || ''} ${u?.last_name || ''}`.toLowerCase()
        if (!hay.includes(q)) return false
      }
      return true
    })
  }, [students, search, classFilter, userById])

  const pageCount = Math.ceil(filtered.length / pageSize)
  const paginatedStudents = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filtered.slice(start, start + pageSize)
  }, [filtered, currentPage, pageSize])

  // Reset page if filtered results change
  useEffect(() => {
    setCurrentPage(1)
  }, [search, classFilter])

  function handlePhotoChange(file, setFile, setPreview) {
    if (!file) return
    setFile(file)
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target.result)
    reader.readAsDataURL(file)
  }

  async function registerFaceAfterSave(studentId, file) {
    if (!file || !studentId) return
    try {
      const fd = new FormData()
      fd.append('photo', file)
      await apiFetch(`/students/${studentId}/register-face/`, {
        method: 'POST',
        body: fd,
      })
    } catch (err) {
      console.error('Face service error:', err)
    }
  }

  /**
   * Fetch the auto-enrolled subject IDs for a given class from the backend.
   * Returns an array of subject IDs (numbers), or [] if no class selected.
   */
  const fetchSubjectsForClass = useCallback(async (classId) => {
    if (!classId) return []
    try {
      const res = await apiFetch(`/students/subjects-for-class/?class_id=${classId}`)
      if (!res.ok) return []
      const json = await res.json()
      return (json.subjects || []).map(s => Number(s.id))
    } catch (err) {
      console.error('Failed to fetch subjects for class:', err)
      return []
    }
  }, [])

  async function handleCreateStudent(e) {
    e.preventDefault()
    setMessage('')
    setBusy(true)

    try {
      // 1. Create User
      const nameParts = createName.trim().split(' ')
      const firstName = nameParts[0] || ''
      const lastName = nameParts.slice(1).join(' ') || ''
      const username = createEmail.split('@')[0] + Math.floor(Math.random() * 1000)

      const userRes = await apiFetch('/users/', {
        method: 'POST',
        body: {
          username: username,
          email: createEmail,
          password: createPassword,
          first_name: firstName,
          last_name: lastName,
          role: 'STUDENT'
        }
      })
      const userJson = await userRes.json().catch(() => ({}))
      if (!userRes.ok) {
        const errMsg = userJson.detail || (userJson.email && userJson.email[0]) || (typeof userJson === 'object' ? Object.values(userJson).flat()[0] : 'User creation failed.')
        throw new Error(errMsg)
      }

      // 2. Create Student — student_id auto-generated by backend
      const studentRes = await apiFetch('/students/', {
        method: 'POST',
        body: {
          user: userJson.id,
          defer_student_id: true,
          school_class_id: createClassId ? Number(createClassId) : null,
          parent_id: createParentId ? Number(createParentId) : null,
          subject_ids: createSubjectIds,
        },
      })
      const studentJson = await studentRes.json().catch(() => ({}))
      if (!studentRes.ok) {
        const errMsg = studentJson.detail || (typeof studentJson === 'object' ? Object.values(studentJson).flat()[0] : 'Student creation failed.')
        throw new Error(errMsg)
      }

      // 3. Register Face if image provided
      if (createPhotoFile) {
        await registerFaceAfterSave(studentJson.id, createPhotoFile)
      }

      setMessage('Student created without ID. Click Generate ID to assign numbers to all students missing one.')
      setShowCreateModal(false)
      // reset form
      setCreateName('')
      setCreateEmail('')
      setCreatePassword('')
      setCreateClassId('')
      setCreateParentId('')
      setCreateSubjectIds([])
      setCreatePhotoFile(null)
      setCreatePhotoPreview(null)

      await loadData()
    } catch (err) {
      setMessage(err.message || 'Create student failed.')
      alert(err.message || 'Create student failed.')
    } finally {
      setBusy(false)
    }
  }

  async function startEdit(s) {
    const u = userById.get(Number(s.user))
    setEditing(s)
    setEditName(u ? [u.first_name, u.last_name].filter(Boolean).join(' ') : '')
    setEditEmail(u?.email || '')
    setEditPassword('')
    setEditStudentId(s.student_id || '')
    setEditParentId(s.parent ? String(s.parent) : '')
    setEditSchoolClassId(s.school_class ? String(s.school_class) : '')
    setEditPhotoFile(null)
    setEditPhotoPreview(s.photo_url || null)
    // Auto-fetch subjects for the student's current class
    if (s.school_class) {
      const ids = await fetchSubjectsForClass(String(s.school_class))
      setEditSubjectIds(ids)
    } else {
      setEditSubjectIds([])
    }
  }

  function cancelEdit() {
    setEditing(null)
    setEditName('')
    setEditEmail('')
    setEditPassword('')
    setEditStudentId('')
    setEditParentId('')
    setEditSubjectIds([])
    setEditSchoolClassId('')
    setEditPhotoFile(null)
    setEditPhotoPreview(null)
  }

  async function saveEdit(e) {
    e.preventDefault()
    if (!editing) return
    setBusy(true)
    setMessage('')
    try {
      // 1. Update linked User (name, email, optional password)
      const nameParts = editName.trim().split(' ')
      const userPatch = {
        first_name: nameParts[0] || '',
        last_name: nameParts.slice(1).join(' ') || '',
        email: editEmail.trim(),
      }
      if (editPassword.trim()) userPatch.password = editPassword.trim()

      const userRes = await apiFetch(`/users/${editing.user}/`, { method: 'PATCH', body: userPatch })
      const userJson = await userRes.json().catch(() => ({}))
      if (!userRes.ok) {
        const errMsg = userJson.detail || (typeof userJson === 'object' ? Object.values(userJson).flat()[0] : `User update failed (${userRes.status})`)
        throw new Error(errMsg)
      }

      // 2. Update Student profile
      const res = await apiFetch(`/students/${editing.id}/`, {
        method: 'PATCH',
        body: {
          student_id: editStudentId.trim(),   // empty string is intentional (clears for re-generation)
          school_class_id: editSchoolClassId ? Number(editSchoolClassId) : null,
          parent_id: editParentId ? Number(editParentId) : null,
          subject_ids: editSubjectIds,
        },
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) {
        const errMsg = json.detail || (typeof json === 'object' ? Object.values(json).flat()[0] : `Update failed (${res.status})`)
        throw new Error(errMsg)
      }

      if (editPhotoFile) {
        await registerFaceAfterSave(editing.id, editPhotoFile)
      }

      setMessage(`Student updated: ${json.student_id || editStudentId}`)
      cancelEdit()
      await loadData()
    } catch (err) {
      alert(err.message || 'Update student failed.')
    } finally {
      setBusy(false)
    }
  }

  async function deleteStudent(s) {
    const ok = window.confirm(`Delete student "${s.student_id}"?\nThis will also delete the linked user account.`)
    if (!ok) return
    setBusy(true)
    setMessage('')
    try {
      // 1. Delete Student profile first (CASCADE-safe)
      const res = await apiFetch(`/students/${s.id}/`, { method: 'DELETE' })
      if (!res.ok) throw new Error(`Delete student failed (${res.status})`)

      // 2. Delete the linked User account
      if (s.user) {
        const userRes = await apiFetch(`/users/${s.user}/`, { method: 'DELETE' })
        if (!userRes.ok) {
          const j = await userRes.json().catch(() => ({}))
          console.warn('User delete warning:', j.detail || userRes.status)
        }
      }

      setMessage(`Student deleted: ${s.student_id}`)
      if (editing?.id === s.id) cancelEdit()
      await loadData()
    } catch (err) {
      alert(err.message || 'Delete student failed.')
    } finally {
      setBusy(false)
    }
  }


  async function handleBackfillIds() {
    if (!window.confirm('Generate a Student ID for every student who has a blank ID now?')) return
    setBusy(true)
    setMessage('')
    setBackfillResult(null)
    try {
      const res = await apiFetch('/students/backfill-ids/', { method: 'POST' })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(json.detail || 'Backfill failed.')
      setBackfillResult(json)
      setMessage(json.message)
      await loadData()
    } catch (err) {
      alert(err.message || 'Failed to generate IDs.')
    } finally {
      setBusy(false)
    }
  }

  function renderStatusBadges(s) {
    const missing = []

    if (!s.photo_url) missing.push('Image')
    if (!s.parent) missing.push('Parent')
    if (!s.school_class) missing.push('Class')

    if (missing.length === 0) {
      return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'var(--ss-success-bg)', color: 'var(--ss-success-text)', border: '1px solid var(--ss-success-border)' }}>Complete</span>
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', alignItems: 'flex-start' }}>
        {missing.map((m) => (
          <span key={m} style={{ padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600, background: 'var(--ss-danger-bg)', color: 'var(--ss-danger-text)', border: '1px solid var(--ss-danger-border)' }}>
            Missing {m}
          </span>
        ))}
      </div>
    )
  }

  return (
    <>
      <PageHeader
        title="Student Management"
        subtitle="Manage all student profiles and accounts."
      />

      {message && <div style={{ padding: '1rem', background: 'var(--ss-success-banner-bg)', color: 'var(--ss-success-banner-text)', borderRadius: '8px', border: '1px solid var(--ss-success-banner-border)', marginBottom: '1.5rem', fontWeight: 500 }}>{message}</div>}

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', flex: 1 }}>
            <input
              type="search"
              placeholder="Search by ID, name, email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--ss-border)', width: '300px', fontSize: '0.9rem' }}
            />
            <select
              value={classFilter}
              onChange={(e) => setClassFilter(e.target.value)}
              style={{ padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--ss-border)', fontSize: '0.9rem', width: '200px' }}
            >
              <option value="all">All Classes</option>
              {classes.map(c => <option key={c.id} value={c.id}>{c.display_name}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <button
              className="btn btn-ghost"
              onClick={handleBackfillIds}
              disabled={busy}
              title="Assign auto-generated IDs to all students with a blank Student ID"
              style={{ border: '1px dashed var(--ss-primary)', color: 'var(--ss-primary)', fontSize: '0.85rem' }}
            >
              Generate ID
            </button>
            <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
              + Create Student
            </button>
          </div>
        </div>

        {loading ? <p className="muted">Loading students...</p> : null}
        {!loading && error ? <p className="feature-error">{error}</p> : null}

        {/* Backfill Results Panel */}
        {backfillResult && backfillResult.updated > 0 ? (
          <div style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem', background: 'var(--ss-info-banner-bg)', border: '1px solid var(--ss-info-banner-border)', borderRadius: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <strong style={{ color: 'var(--ss-info-banner-text)' }}>Generated {backfillResult.updated} student ID(s)</strong>
              <button type="button" className="btn btn-ghost btn-xs" onClick={() => setBackfillResult(null)}>✕ Close</button>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {backfillResult.students.map(s => (
                <div key={s.id} style={{ padding: '0.4rem 0.8rem', background: 'var(--ss-bg-card)', border: '1px solid var(--ss-info-banner-border)', borderRadius: '6px', fontSize: '0.82rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--ss-info-banner-text)', fontFamily: 'monospace' }}>{s.student_id}</span>
                  <span style={{ color: 'var(--ss-text-muted)', marginLeft: '0.5rem' }}>→ {s.name}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {!loading && !error && (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table className="feature-table">
                <thead>
                  <tr>
                    <th>Profile</th>
                    <th>Full Name</th>
                    <th>Email</th>
                    <th>Student ID</th>
                    <th>Class</th>
                    <th>Parent</th>
                    <th>Subjects</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedStudents.length === 0 ? (
                    <tr>
                      <td colSpan="9" style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--ss-text-muted)' }}>
                        No students found.
                      </td>
                    </tr>
                  ) : (
                    paginatedStudents.map((s) => {
                      const user = userById.get(Number(s.user))
                      const parent = parentById.get(s.parent)
                      const subjNames = (s.subjects || []).map(id => subjectById.get(id)?.name).filter(Boolean)

                      return (
                        <tr key={s.id}>
                          <td>
                            {s.photo_url ? (
                              <img src={s.photo_url} alt="Profile" style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--ss-border)' }} />
                            ) : (
                              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--ss-bg-active)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>👤</div>
                            )}
                          </td>
                          <td>
                            <div style={{ fontWeight: 600 }}>{fullName(user)}</div>
                          </td>
                          <td className="muted">
                            {user?.email || '—'}
                          </td>
                          <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{s.student_id || '—'}</td>
                          <td>{s.school_class_display || '—'}</td>
                          <td>{parent ? (fullName(userById.get(Number(parentById.get(s.parent)?.user))) || parentById.get(s.parent)?.parent_id || `#${parent.id}`) : '—'}</td>
                          <td style={{ maxWidth: '150px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {subjNames.length ? subjNames.join(', ') : '—'}
                          </td>
                          <td>{renderStatusBadges(s)}</td>
                          <td>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                              <button className="btn btn-ghost btn-xs" onClick={() => startEdit(s)}>Edit</button>
                              <button className="btn btn-ghost btn-xs" style={{ color: 'var(--ss-danger-bold)' }} onClick={() => deleteStudent(s)}>Delete</button>
                            </div>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {pageCount > 1 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--ss-border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--ss-text-muted)' }}>
                  Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filtered.length)} of {filtered.length} students
                </span>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="btn btn-ghost btn-xs" disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)}>Previous</button>
                  <button className="btn btn-ghost btn-xs" disabled={currentPage === pageCount} onClick={() => setCurrentPage(p => p + 1)}>Next</button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>

      {/* --- CREATE MODAL --- */}
      {showCreateModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'var(--ss-modal-overlay)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ background: 'var(--ss-bg-card)', borderRadius: '16px', width: 'min(600px, 100%)', maxHeight: '90vh', overflowY: 'auto', padding: '2rem', boxShadow: 'var(--ss-modal-shadow)' }}>
            <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.25rem' }}>Create New Student</h2>
            <form onSubmit={handleCreateStudent} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Full Name *</label>
                <input required className="login-input login-input--plain" value={createName} onChange={e => setCreateName(e.target.value)} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Email *</label>
                  <input type="email" required className="login-input login-input--plain" value={createEmail} onChange={e => setCreateEmail(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Password *</label>
                  <input type="password" required className="login-input login-input--plain" value={createPassword} onChange={e => setCreatePassword(e.target.value)} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Class</label>
                  <select className="login-input login-input--plain" value={createClassId} onChange={async e => {
                    const val = e.target.value
                    setCreateClassId(val)
                    const ids = await fetchSubjectsForClass(val)
                    setCreateSubjectIds(ids)
                  }}>
                    <option value="">— No class —</option>
                    {classes.map(c => <option key={c.id} value={c.id}>{c.display_name}</option>)}
                  </select>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Parent</label>
                  <select className="login-input login-input--plain" value={createParentId} onChange={e => setCreateParentId(e.target.value)}>
                    <option value="">— No parent link —</option>
                    {parents.map(p => <option key={p.id} value={p.id}>{fullName(userById.get(Number(p.user))) || p.parent_id || `#${p.id}`}</option>)}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Face Photo (Optional)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  {createPhotoPreview ? (
                    <img src={createPhotoPreview} alt="Preview" style={{ width: '60px', height: '60px', borderRadius: '8px', objectFit: 'cover' }} />
                  ) : (
                    <div style={{ width: '60px', height: '60px', borderRadius: '8px', background: 'var(--ss-bg-active)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>📷</div>
                  )}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <input id="create-photo" type="file" accept="image/*" style={{ display: 'none' }} onChange={e => handlePhotoChange(e.target.files[0], setCreatePhotoFile, setCreatePhotoPreview)} />
                    <label htmlFor="create-photo" className="btn btn-ghost btn-xs" style={{ cursor: 'pointer', alignSelf: 'flex-start', background: 'var(--ss-border)' }}>Choose Photo</label>
                    {createPhotoFile && <span style={{ fontSize: '0.75rem', color: 'var(--ss-text-muted)' }}>{createPhotoFile.name}</span>}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--ss-border)' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Saving...' : 'Create Student'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- EDIT MODAL --- */}
      {editing && (
        <div style={{ position: 'fixed', inset: 0, background: 'var(--ss-modal-overlay)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ background: 'var(--ss-bg-card)', borderRadius: '16px', width: 'min(600px, 100%)', maxHeight: '90vh', overflowY: 'auto', padding: '2rem', boxShadow: 'var(--ss-modal-shadow)' }}>
            <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.25rem' }}>Edit Student{editing.student_id ? `: ${editing.student_id}` : ''}</h2>
            <form onSubmit={saveEdit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Full Name *</label>
                  <input required className="login-input login-input--plain" value={editName} onChange={e => setEditName(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Student ID <span style={{ fontWeight: 400, color: 'var(--ss-text-faint)' }}>(clear field, save, then use Generate ID)</span></label>
                  <input
                    className="login-input login-input--plain"
                    value={editStudentId}
                    onChange={e => setEditStudentId(e.target.value)}
                    placeholder="Leave blank, save, then Generate ID"
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Email *</label>
                  <input type="email" required className="login-input login-input--plain" value={editEmail} onChange={e => setEditEmail(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>New Password <span style={{ fontWeight: 400, color: 'var(--ss-text-faint)' }}>(leave blank to keep)</span></label>
                  <input type="password" className="login-input login-input--plain" value={editPassword} onChange={e => setEditPassword(e.target.value)} placeholder="••••••••" />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Class</label>
                  <select className="login-input login-input--plain" value={editSchoolClassId} onChange={async e => {
                    const val = e.target.value
                    setEditSchoolClassId(val)
                    const ids = await fetchSubjectsForClass(val)
                    setEditSubjectIds(ids)
                  }}>
                    <option value="">— No class —</option>
                    {classes.map(c => <option key={c.id} value={c.id}>{c.display_name}</option>)}
                  </select>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Parent</label>
                  <select className="login-input login-input--plain" value={editParentId} onChange={e => setEditParentId(e.target.value)}>
                    <option value="">— No parent link —</option>
                    {parents.map(p => <option key={p.id} value={p.id}>{fullName(userById.get(Number(p.user))) || p.parent_id || `#${p.id}`}</option>)}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Face Photo (Replace)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  {editPhotoPreview ? (
                    <img src={editPhotoPreview} alt="Preview" style={{ width: '60px', height: '60px', borderRadius: '8px', objectFit: 'cover' }} />
                  ) : (
                    <div style={{ width: '60px', height: '60px', borderRadius: '8px', background: 'var(--ss-bg-active)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>📷</div>
                  )}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <input id="edit-photo" type="file" accept="image/*" style={{ display: 'none' }} onChange={e => handlePhotoChange(e.target.files[0], setEditPhotoFile, setEditPhotoPreview)} />
                    <label htmlFor="edit-photo" className="btn btn-ghost btn-xs" style={{ cursor: 'pointer', alignSelf: 'flex-start', background: 'var(--ss-border)' }}>Choose New Photo</label>
                    {editPhotoFile && <span style={{ fontSize: '0.75rem', color: 'var(--ss-text-muted)' }}>{editPhotoFile.name}</span>}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--ss-border)' }}>
                <button type="button" className="btn btn-ghost" onClick={cancelEdit}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Saving...' : 'Save Changes'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}

