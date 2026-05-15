import { useEffect, useMemo, useState } from 'react'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch, apiFetchAll } from '../../lib/api'

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

function toggleId(list, id) {
  const n = Number(id)
  return list.includes(n) ? list.filter((x) => x !== n) : [...list, n]
}

function usernameFromEmail(email) {
  const v = (email || '').trim().toLowerCase()
  if (!v.includes('@')) return v
  return v.split('@')[0].replace(/[^a-z0-9._-]/g, '')
}

function splitClasses(text) {
  return text.split(',').map((x) => x.trim()).filter(Boolean)
}

export function AdminTeachersPage() {
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [teachers, setTeachers] = useState([])
  const [users, setUsers] = useState([])
  const [subjects, setSubjects] = useState([])
  const [classes, setClasses] = useState([])

  const [search, setSearch] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 10

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createEmail, setCreateEmail] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [teacherId, setTeacherId] = useState('')
  const [subjectIds, setSubjectIds] = useState([])
  const [assignedClassIds, setAssignedClassIds] = useState([])

  const [editing, setEditing] = useState(null)
  const [editName, setEditName] = useState('')
  const [editEmail, setEditEmail] = useState('')
  const [editPassword, setEditPassword] = useState('')
  const [editTeacherId, setEditTeacherId] = useState('')
  const [editSubjectIds, setEditSubjectIds] = useState([])
  const [editAssignedClassIds, setEditAssignedClassIds] = useState([])

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const [teachersData, usersData, subjectsData, classesData] = await Promise.all([
        apiFetchAll('/teachers/'),
        apiFetchAll('/users/'),
        apiFetchAll('/subjects/'),
        apiFetchAll('/classes/'),
      ])
      setTeachers(teachersData)
      setUsers(usersData)
      setSubjects(subjectsData)
      setClasses(classesData)
    } catch (e) {
      setError(e.message || 'Failed to load teacher module.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const userById = useMemo(() => new Map(users.map((u) => [Number(u.id), u])), [users])
  const subjectById = useMemo(() => new Map(subjects.map((s) => [s.id, s])), [subjects])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return teachers
    return teachers.filter((t) => {
      const u = userById.get(Number(t.user))
      const classesStr = Array.isArray(t.class_ids) ? t.class_ids.join(' ') : ''
      const hay = `${t.teacher_id || ''} ${classesStr} ${u?.username || ''} ${u?.email || ''} ${u?.first_name || ''} ${u?.last_name || ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [teachers, search, userById])

  const pageCount = Math.ceil(filtered.length / pageSize)
  const paginatedTeachers = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filtered.slice(start, start + pageSize)
  }, [filtered, currentPage, pageSize])

  useEffect(() => {
    setCurrentPage(1)
  }, [search])

  async function createTeacher(e) {
    e.preventDefault()
    setMessage('')
    if (!createName.trim() || !createEmail.trim() || !createPassword.trim() || !teacherId.trim()) {
      alert('Name, Email, Password, and Teacher ID are required.')
      return
    }
    const username = usernameFromEmail(createEmail)
    if (!username) {
      alert('Could not generate username from email.')
      return
    }
    setBusy(true)
    try {
      const nameParts = createName.trim().split(' ')
      const firstName = nameParts[0]
      const lastName = nameParts.slice(1).join(' ')

      const userRes = await apiFetch('/users/', {
        method: 'POST',
        body: {
          username: username,
          email: createEmail.trim(),
          password: createPassword.trim(),
          first_name: firstName,
          last_name: lastName,
          role: 'TEACHER'
        }
      })
      const userJson = await userRes.json().catch(() => ({}))
      if (!userRes.ok) {
        const errMsg = userJson.detail || (userJson.email && userJson.email[0]) || (typeof userJson === 'object' ? Object.values(userJson).flat()[0] : 'User creation failed.')
        throw new Error(errMsg)
      }

      const payload = {
        user: userJson.id,
        teacher_id: teacherId.trim(),
        subject_ids: subjectIds,
        assigned_class_ids: assignedClassIds,
      }
      const res = await apiFetch('/teachers/', { method: 'POST', body: payload })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) {
        const errMsg = json.detail || (typeof json === 'object' ? Object.values(json).flat()[0] : `Teacher creation failed (${res.status})`)
        throw new Error(errMsg)
      }

      setMessage(`Teacher created: ${json.teacher_id}`)
      setShowCreateModal(false)
      setCreateName('')
      setCreateEmail('')
      setCreatePassword('')
      setTeacherId('')
      setSubjectIds([])
      setAssignedClassIds([])
      await loadData()
    } catch (err) {
      alert(err.message || 'Create teacher failed.')
    } finally {
      setBusy(false)
    }
  }

  function startEdit(t) {
    const u = userById.get(Number(t.user))
    setEditing(t)
    setEditName(u ? [u.first_name, u.last_name].filter(Boolean).join(' ') : '')
    setEditEmail(u?.email || '')
    setEditPassword('')
    setEditTeacherId(t.teacher_id || '')
    setEditSubjectIds(Array.isArray(t.subject_ids) ? t.subject_ids.map(Number) : [])
    setEditAssignedClassIds(
      Array.isArray(t.assigned_classes_display)
        ? t.assigned_classes_display.map((c) => Number(c.id))
        : []
    )
  }

  function cancelEdit() {
    setEditing(null)
    setEditName('')
    setEditEmail('')
    setEditPassword('')
    setEditTeacherId('')
    setEditSubjectIds([])
    setEditAssignedClassIds([])
  }

  async function saveEdit(e) {
    e.preventDefault()
    if (!editing) return
    setBusy(true)
    setMessage('')
    try {
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

      const res = await apiFetch(`/teachers/${editing.id}/`, {
        method: 'PATCH',
        body: {
          teacher_id: editTeacherId.trim(),
          subject_ids: editSubjectIds,
          assigned_class_ids: editAssignedClassIds,
        },
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) {
        const errMsg = json.detail || (typeof json === 'object' ? Object.values(json).flat()[0] : `Update failed (${res.status})`)
        throw new Error(errMsg)
      }
      setMessage(`Teacher updated: ${json.teacher_id || editTeacherId}`)
      cancelEdit()
      await loadData()
    } catch (err) {
      alert(err.message || 'Update teacher failed.')
    } finally {
      setBusy(false)
    }
  }

  async function deleteTeacher(t) {
    const ok = window.confirm(`Delete teacher "${t.teacher_id}"?\nThis will also delete the linked user account.`)
    if (!ok) return
    setBusy(true)
    setMessage('')
    try {
      const res = await apiFetch(`/teachers/${t.id}/`, { method: 'DELETE' })
      if (!res.ok) throw new Error(`Delete teacher failed (${res.status})`)

      if (t.user) {
        const userRes = await apiFetch(`/users/${t.user}/`, { method: 'DELETE' })
        if (!userRes.ok) {
          const j = await userRes.json().catch(() => ({}))
          console.warn('User delete warning:', j.detail || userRes.status)
        }
      }

      setMessage(`Teacher deleted: ${t.teacher_id}`)
      if (editing?.id === t.id) cancelEdit()
      await loadData()
    } catch (err) {
      alert(err.message || 'Delete teacher failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Teacher Management"
        subtitle="Manage teacher profiles and class assignments."
      />

      {message && <div style={{ padding: '1rem', background: '#ecfdf5', color: '#065f46', borderRadius: '8px', border: '1px solid #a7f3d0', marginBottom: '1.5rem', fontWeight: 500 }}>{message}</div>}

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', flex: 1 }}>
            <input
              type="search"
              placeholder="Search by ID, name, email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid #eaeaea', width: '300px', fontSize: '0.9rem' }}
            />
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            + Create Teacher
          </button>
        </div>

        {loading ? <p className="muted">Loading teachers...</p> : null}
        {!loading && error ? <p className="feature-error">{error}</p> : null}

        {!loading && !error && (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table className="feature-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Teacher ID</th>
                    <th>Subjects</th>
                    <th>Classes</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedTeachers.length === 0 ? (
                    <tr>
                      <td colSpan="8" style={{ textAlign: 'center', padding: '3rem 1rem', color: '#6b7280' }}>
                        No teachers found.
                      </td>
                    </tr>
                  ) : (
                    paginatedTeachers.map((t) => {
                      const user = userById.get(Number(t.user))
                      const subjNames = (t.subject_ids || [])
                        .map((id) => subjectById.get(id))
                        .filter(Boolean)
                        .map((x) => x.name)

                      let classNames = []
                      if (t.assigned_classes_display && t.assigned_classes_display.length > 0) {
                        classNames = t.assigned_classes_display.map(c => c.name)
                      } else if (Array.isArray(t.class_ids)) {
                        classNames = t.class_ids
                      }

                      return (
                        <tr key={t.id}>
                          <td>
                            <div style={{ fontWeight: 600 }}>{fullName(user)}</div>
                          </td>
                          <td className="muted">
                            {user?.email || '—'}
                          </td>
                          <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{t.teacher_id || '—'}</td>
                          <td style={{ maxWidth: '150px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {subjNames.length ? subjNames.join(', ') : '—'}
                          </td>
                          <td style={{ maxWidth: '150px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={classNames.join(', ')}>
                            {classNames.length ? classNames.join(', ') : '—'}
                          </td>
                          <td>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                              <button className="btn btn-ghost btn-xs" onClick={() => startEdit(t)}>Edit</button>
                              <button className="btn btn-ghost btn-xs" style={{ color: '#dc2626' }} onClick={() => deleteTeacher(t)}>Delete</button>
                            </div>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>

            {pageCount > 1 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid #eaeaea' }}>
                <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                  Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filtered.length)} of {filtered.length} teachers
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

      {/* CREATE MODAL */}
      {showCreateModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ background: '#fff', borderRadius: '16px', width: 'min(600px, 100%)', maxHeight: '90vh', overflowY: 'auto', padding: '2rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}>
            <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.25rem' }}>Create New Teacher</h2>
            <form onSubmit={createTeacher} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Full Name *</label>
                  <input required className="login-input login-input--plain" value={createName} onChange={e => setCreateName(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Teacher ID *</label>
                  <input required className="login-input login-input--plain" value={teacherId} onChange={e => setTeacherId(e.target.value)} />
                </div>
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

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Assign Subjects</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: '#f9fafb', padding: '1rem', borderRadius: '8px', border: '1px solid #eaeaea' }}>
                  {subjects.length === 0 && <span className="muted">No subjects.</span>}
                  {subjects.map((s) => (
                    <label key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                      <input type="checkbox" checked={subjectIds.includes(Number(s.id))} onChange={() => setSubjectIds(prev => toggleId(prev, s.id))} />
                      {s.name}
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Assign Classes</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: '#f9fafb', padding: '1rem', borderRadius: '8px', border: '1px solid #eaeaea' }}>
                  {classes.length === 0 && <span className="muted">No classes.</span>}
                  {classes.map((c) => (
                    <label key={c.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                      <input type="checkbox" checked={assignedClassIds.includes(Number(c.id))} onChange={() => setAssignedClassIds(prev => toggleId(prev, c.id))} />
                      {c.display_name}
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #eaeaea' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Saving...' : 'Create Teacher'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT MODAL */}
      {editing && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ background: '#fff', borderRadius: '16px', width: 'min(600px, 100%)', maxHeight: '90vh', overflowY: 'auto', padding: '2rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}>
            <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.25rem' }}>Edit Teacher: {editing.teacher_id}</h2>
            <form onSubmit={saveEdit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Full Name *</label>
                  <input required className="login-input login-input--plain" value={editName} onChange={e => setEditName(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Teacher ID *</label>
                  <input required className="login-input login-input--plain" value={editTeacherId} onChange={e => setEditTeacherId(e.target.value)} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Email *</label>
                  <input type="email" required className="login-input login-input--plain" value={editEmail} onChange={e => setEditEmail(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>New Password <span style={{ fontWeight: 400, color: '#9ca3af' }}>(leave blank to keep)</span></label>
                  <input type="password" className="login-input login-input--plain" value={editPassword} onChange={e => setEditPassword(e.target.value)} placeholder="••••••••" />
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Assign Subjects</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: '#f9fafb', padding: '1rem', borderRadius: '8px', border: '1px solid #eaeaea' }}>
                  {subjects.length === 0 && <span className="muted">No subjects.</span>}
                  {subjects.map((s) => (
                    <label key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                      <input type="checkbox" checked={editSubjectIds.includes(Number(s.id))} onChange={() => setEditSubjectIds(prev => toggleId(prev, s.id))} />
                      {s.name}
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Assign Classes</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: '#f9fafb', padding: '1rem', borderRadius: '8px', border: '1px solid #eaeaea' }}>
                  {classes.length === 0 && <span className="muted">No classes.</span>}
                  {classes.map((c) => (
                    <label key={c.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                      <input type="checkbox" checked={editAssignedClassIds.includes(Number(c.id))} onChange={() => setEditAssignedClassIds(prev => toggleId(prev, c.id))} />
                      {c.display_name}
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #eaeaea' }}>
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
