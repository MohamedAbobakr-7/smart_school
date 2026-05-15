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

export function AdminParentsPage() {
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [parents, setParents] = useState([])
  const [users, setUsers] = useState([])
  const [students, setStudents] = useState([])

  const [search, setSearch] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 10

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createEmail, setCreateEmail] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [parentId, setParentId] = useState('')
  const [occupation, setOccupation] = useState('')
  const [relationship, setRelationship] = useState('')
  const [childIds, setChildIds] = useState([])

  const [editing, setEditing] = useState(null)
  const [editName, setEditName] = useState('')
  const [editEmail, setEditEmail] = useState('')
  const [editPassword, setEditPassword] = useState('')
  const [editParentId, setEditParentId] = useState('')
  const [editOccupation, setEditOccupation] = useState('')
  const [editRelationship, setEditRelationship] = useState('')
  const [editChildIds, setEditChildIds] = useState([])

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const [parentsData, usersData, studentsData] = await Promise.all([
        apiFetchAll('/parents/'),
        apiFetchAll('/users/'),
        apiFetchAll('/students/'),
      ])
      setParents(parentsData)
      setUsers(usersData)
      setStudents(studentsData)
    } catch (e) {
      setError(e.message || 'Failed to load parents module.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const userById = useMemo(() => new Map(users.map((u) => [Number(u.id), u])), [users])
  const studentById = useMemo(() => new Map(students.map((s) => [s.id, s])), [students])

  function linkedStudentIds(parentPk) {
    return students
      .filter((s) => s.parent === parentPk)
      .map((s) => s.id)
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return parents
    return parents.filter((p) => {
      const u = userById.get(Number(p.user))
      const hay = `${p.parent_id || ''} ${p.occupation || ''} ${p.relationship || ''} ${u?.username || ''} ${u?.first_name || ''} ${u?.last_name || ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [parents, search, userById])

  const pageCount = Math.ceil(filtered.length / pageSize)
  const paginatedParents = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filtered.slice(start, start + pageSize)
  }, [filtered, currentPage, pageSize])

  useEffect(() => {
    setCurrentPage(1)
  }, [search])

  async function createParent(e) {
    e.preventDefault()
    setMessage('')
    if (!createName.trim() || !createEmail.trim() || !createPassword.trim() || !parentId.trim()) {
      alert('Name, Email, Password, and Parent ID are required.')
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
          role: 'PARENT'
        }
      })
      const userJson = await userRes.json().catch(() => ({}))
      if (!userRes.ok) {
        const errMsg = userJson.detail || (userJson.email && userJson.email[0]) || (typeof userJson === 'object' ? Object.values(userJson).flat()[0] : 'User creation failed.')
        throw new Error(errMsg)
      }

      const res = await apiFetch('/parents/', {
        method: 'POST',
        body: {
          user: userJson.id,
          parent_id: parentId.trim(),
          occupation: occupation.trim(),
          relationship: relationship.trim(),
        },
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) {
        const errMsg = json.detail || (typeof json === 'object' ? Object.values(json).flat()[0] : `Parent creation failed (${res.status})`)
        throw new Error(errMsg)
      }
      const newParentPk = json.id

      if (childIds.length) {
        await Promise.all(
          childIds.map((sid) =>
            apiFetch(`/students/${sid}/`, {
              method: 'PATCH',
              body: { parent_id: newParentPk },
            })
          )
        )
      }

      setMessage(`Parent created: ${json.parent_id}`)
      setShowCreateModal(false)
      setCreateName('')
      setCreateEmail('')
      setCreatePassword('')
      setParentId('')
      setOccupation('')
      setRelationship('')
      setChildIds([])
      await loadData()
    } catch (err) {
      alert(err.message || 'Create parent failed.')
    } finally {
      setBusy(false)
    }
  }

  function startEdit(p) {
    const u = userById.get(Number(p.user))
    setEditing(p)
    setEditName(u ? [u.first_name, u.last_name].filter(Boolean).join(' ') : '')
    setEditEmail(u?.email || '')
    setEditPassword('')
    setEditParentId(p.parent_id || '')
    setEditOccupation(p.occupation || '')
    setEditRelationship(p.relationship || '')
    setEditChildIds(linkedStudentIds(p.id))
  }

  function cancelEdit() {
    setEditing(null)
    setEditName('')
    setEditEmail('')
    setEditPassword('')
    setEditParentId('')
    setEditOccupation('')
    setEditRelationship('')
    setEditChildIds([])
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

      const res = await apiFetch(`/parents/${editing.id}/`, {
        method: 'PATCH',
        body: {
          parent_id: editParentId.trim(),
          occupation: editOccupation.trim(),
          relationship: editRelationship.trim(),
        },
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) {
        const errMsg = json.detail || (typeof json === 'object' ? Object.values(json).flat()[0] : `Update failed (${res.status})`)
        throw new Error(errMsg)
      }

      const prev = linkedStudentIds(editing.id)
      const toUnlink = prev.filter((id) => !editChildIds.includes(id))
      const toLink = editChildIds.filter((id) => !prev.includes(id))

      await Promise.all([
        ...toUnlink.map((sid) =>
          apiFetch(`/students/${sid}/`, { method: 'PATCH', body: { parent_id: null } })
        ),
        ...toLink.map((sid) =>
          apiFetch(`/students/${sid}/`, { method: 'PATCH', body: { parent_id: editing.id } })
        ),
      ])

      setMessage(`Parent updated: ${json.parent_id || editParentId}`)
      cancelEdit()
      await loadData()
    } catch (err) {
      alert(err.message || 'Update parent failed.')
    } finally {
      setBusy(false)
    }
  }

  async function deleteParent(p) {
    const ok = window.confirm(`Delete parent "${p.parent_id}"?\nLinked students will lose their parent reference.\nThis will also delete the linked user account.`)
    if (!ok) return
    setBusy(true)
    setMessage('')
    try {
      const res = await apiFetch(`/parents/${p.id}/`, { method: 'DELETE' })
      if (!res.ok) throw new Error(`Delete parent failed (${res.status})`)

      if (p.user) {
        const userRes = await apiFetch(`/users/${p.user}/`, { method: 'DELETE' })
        if (!userRes.ok) {
          const j = await userRes.json().catch(() => ({}))
          console.warn('User delete warning:', j.detail || userRes.status)
        }
      }

      setMessage(`Parent deleted: ${p.parent_id}`)
      if (editing?.id === p.id) cancelEdit()
      await loadData()
    } catch (err) {
      alert(err.message || 'Delete parent failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Parent Management"
        subtitle="Manage parent profiles and link them to one or more student children."
      />

      {message && <div style={{ padding: '1rem', background: '#ecfdf5', color: '#065f46', borderRadius: '8px', border: '1px solid #a7f3d0', marginBottom: '1.5rem', fontWeight: 500 }}>{message}</div>}

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', flex: 1 }}>
            <input
              type="search"
              placeholder="Search by ID, name, email, occupation..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid #eaeaea', width: '300px', fontSize: '0.9rem' }}
            />
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            + Create Parent
          </button>
        </div>

        {loading ? <p className="muted">Loading parents...</p> : null}
        {!loading && error ? <p className="feature-error">{error}</p> : null}

        {!loading && !error && (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table className="feature-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Parent ID</th>
                    <th>Occupation</th>
                    <th>Relationship</th>
                    <th>Children (Students)</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedParents.length === 0 ? (
                    <tr>
                      <td colSpan="7" style={{ textAlign: 'center', padding: '3rem 1rem', color: '#6b7280' }}>
                        No parents found.
                      </td>
                    </tr>
                  ) : (
                    paginatedParents.map((p) => {
                      const user = userById.get(Number(p.user))
                      const children = students.filter((s) => s.parent === p.id)

                      return (
                        <tr key={p.id}>
                          <td>
                            <div style={{ fontWeight: 600 }}>{fullName(user)}</div>
                          </td>
                          <td className="muted">
                            {user?.email || '—'}
                          </td>
                          <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{p.parent_id || '—'}</td>
                          <td>{p.occupation || '—'}</td>
                          <td>{p.relationship || '—'}</td>
                          <td>
                            {children.length ? (
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                                {children.map((s) => (
                                  <span key={s.id} style={{ padding: '0.15rem 0.5rem', background: '#f4f4f5', borderRadius: '4px', fontSize: '0.75rem', border: '1px solid #eaeaea' }}>
                                    {s.student_id || `#${s.id}`}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                              <button className="btn btn-ghost btn-xs" onClick={() => startEdit(p)}>Edit</button>
                              <button className="btn btn-ghost btn-xs" style={{ color: '#dc2626' }} onClick={() => deleteParent(p)}>Delete</button>
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
                  Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filtered.length)} of {filtered.length} parents
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
            <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.25rem' }}>Create New Parent</h2>
            <form onSubmit={createParent} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Full Name *</label>
                  <input required className="login-input login-input--plain" value={createName} onChange={e => setCreateName(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Parent ID *</label>
                  <input required className="login-input login-input--plain" value={parentId} onChange={e => setParentId(e.target.value)} />
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

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Occupation</label>
                  <input className="login-input login-input--plain" value={occupation} onChange={e => setOccupation(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Relationship</label>
                  <input className="login-input login-input--plain" value={relationship} onChange={e => setRelationship(e.target.value)} placeholder="e.g. Father, Mother" />
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Link Students (Children)</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: '#f9fafb', padding: '1rem', borderRadius: '8px', border: '1px solid #eaeaea', maxHeight: '150px', overflowY: 'auto' }}>
                  {students.length === 0 && <span className="muted">No students.</span>}
                  {students.map((s) => {
                    const u = userById.get(s.user)
                    return (
                      <label key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                        <input type="checkbox" checked={childIds.includes(s.id)} onChange={() => setChildIds(prev => toggleId(prev, s.id))} />
                        {s.student_id} {u ? `— ${fullName(u)}` : ''}
                      </label>
                    )
                  })}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #eaeaea' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Saving...' : 'Create Parent'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT MODAL */}
      {editing && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ background: '#fff', borderRadius: '16px', width: 'min(600px, 100%)', maxHeight: '90vh', overflowY: 'auto', padding: '2rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}>
            <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.25rem' }}>Edit Parent: {editing.parent_id}</h2>
            <form onSubmit={saveEdit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Full Name *</label>
                  <input required className="login-input login-input--plain" value={editName} onChange={e => setEditName(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Parent ID *</label>
                  <input required className="login-input login-input--plain" value={editParentId} onChange={e => setEditParentId(e.target.value)} />
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

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Occupation</label>
                  <input className="login-input login-input--plain" value={editOccupation} onChange={e => setEditOccupation(e.target.value)} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Relationship</label>
                  <input className="login-input login-input--plain" value={editRelationship} onChange={e => setEditRelationship(e.target.value)} />
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 500 }}>Link Students (Children)</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', background: '#f9fafb', padding: '1rem', borderRadius: '8px', border: '1px solid #eaeaea', maxHeight: '150px', overflowY: 'auto' }}>
                  {students.length === 0 && <span className="muted">No students.</span>}
                  {students.map((s) => {
                    const u = userById.get(s.user)
                    return (
                      <label key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                        <input type="checkbox" checked={editChildIds.includes(s.id)} onChange={() => setEditChildIds(prev => toggleId(prev, s.id))} />
                        {s.student_id} {u ? `— ${fullName(u)}` : ''}
                      </label>
                    )
                  })}
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
