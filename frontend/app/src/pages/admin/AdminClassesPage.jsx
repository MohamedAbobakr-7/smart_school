import { useEffect, useMemo, useState } from 'react'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch, apiFetchAll } from '../../lib/api'

/* ─── helpers ──────────────────────────────────────────────────── */
const EMPTY = { name: '', section: '', description: '' }

function fullName(user) {
  if (!user) return '—'
  const n = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
  return n || user.username || '—'
}

/* ─── component ────────────────────────────────────────────────── */
export function AdminClassesPage() {
  const [loading, setLoading]   = useState(true)
  const [busy, setBusy]         = useState(false)
  const [error, setError]       = useState('')
  const [message, setMessage]   = useState('')

  const [classes, setClasses]   = useState([])
  const [teachers, setTeachers] = useState([])
  const [students, setStudents] = useState([])
  const [users, setUsers]       = useState([])

  const [form, setForm]         = useState(EMPTY)
  const [editing, setEditing]   = useState(null)
  const [search, setSearch]     = useState('')

  /* ── load ───────────────────────────────────────────────────── */
  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const [classesData, teachersData, studentsData, usersData] = await Promise.all([
        apiFetchAll('/classes/'),
        apiFetchAll('/teachers/'),
        apiFetchAll('/students/'),
        apiFetchAll('/users/'),
      ])
      setClasses(classesData)
      setTeachers(teachersData)
      setStudents(studentsData)
      setUsers(usersData)
    } catch (e) {
      setError(e.message || 'Failed to load classes.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  /* ── derived maps ───────────────────────────────────────────── */
  const userById = useMemo(() => new Map(users.map((u) => [u.id, u])), [users])

  // teachers per class: Map<classId, Teacher[]>
  const teachersByClass = useMemo(() => {
    const map = new Map()
    teachers.forEach((t) => {
      const classDefs = Array.isArray(t.assigned_classes_display) ? t.assigned_classes_display : []
      classDefs.forEach(({ id }) => {
        if (!map.has(id)) map.set(id, [])
        map.get(id).push(t)
      })
    })
    return map
  }, [teachers])

  // students per class: Map<classId, Student[]>
  const studentsByClass = useMemo(() => {
    const map = new Map()
    students.forEach((s) => {
      if (s.school_class != null) {
        if (!map.has(s.school_class)) map.set(s.school_class, [])
        map.get(s.school_class).push(s)
      }
    })
    return map
  }, [students])

  /* ── filtered + grouped ─────────────────────────────────────── */
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return classes
    return classes.filter((c) => {
      const hay = `${c.name} ${c.section} ${c.description}`.toLowerCase()
      return hay.includes(q)
    })
  }, [classes, search])

  const grouped = useMemo(() => {
    const map = new Map()
    filtered.forEach((c) => {
      if (!map.has(c.name)) map.set(c.name, [])
      map.get(c.name).push(c)
    })
    return [...map.entries()]
  }, [filtered])

  /* ── form helpers ───────────────────────────────────────────── */
  function setField(key, val) { setForm((prev) => ({ ...prev, [key]: val })) }

  function startEdit(cls) {
    setEditing(cls)
    setForm({ name: cls.name, section: cls.section, description: cls.description })
    setMessage('')
    document.getElementById('class-name-input')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  function cancelEdit() { setEditing(null); setForm(EMPTY) }

  /* ── CRUD ───────────────────────────────────────────────────── */
  async function saveClass(e) {
    e.preventDefault()
    setMessage('')
    if (!form.name.trim()) { setMessage('Class name is required.'); return }
    setBusy(true)
    try {
      const body = { name: form.name.trim(), section: form.section.trim(), description: form.description.trim() }
      const res = editing
        ? await apiFetch(`/classes/${editing.id}/`, { method: 'PATCH', body })
        : await apiFetch('/classes/', { method: 'POST', body })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(json.detail || JSON.stringify(json) || `Save failed (${res.status})`)
      setMessage(editing ? `Updated: ${json.display_name}` : `Created: ${json.display_name}`)
      cancelEdit()
      await loadData()
    } catch (err) { setMessage(err.message || 'Save failed.') }
    finally { setBusy(false) }
  }

  async function deleteClass(cls) {
    if (!window.confirm(`Delete class "${cls.display_name}"?`)) return
    setBusy(true)
    setMessage('')
    try {
      const res = await apiFetch(`/classes/${cls.id}/`, { method: 'DELETE' })
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail || `Delete failed (${res.status})`)
      }
      setMessage(`Deleted: ${cls.display_name}`)
      if (editing?.id === cls.id) cancelEdit()
      await loadData()
    } catch (err) { setMessage(err.message || 'Delete failed.') }
    finally { setBusy(false) }
  }

  /* ── render ─────────────────────────────────────────────────── */
  return (
    <>
      <PageHeader
        title="Classes"
        subtitle="Manage class groups. Each class shows its assigned teachers and students."
      />

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', alignItems: 'center' }}>
        <button type="button" className="btn btn-ghost btn-xs" onClick={loadData} disabled={loading} id="classes-refresh-btn">
          {loading ? 'Refreshing…' : '↻ Refresh'}
        </button>
        {editing && (
          <button type="button" className="btn btn-ghost btn-xs" onClick={cancelEdit}>✕ Cancel edit</button>
        )}
      </div>

      {message && <p className="teaching-msg">{message}</p>}
      {loading && <p className="muted">Loading classes…</p>}
      {!loading && error && <p className="teaching-error">{error}</p>}

      <div className="admin-form-container">
        {/* ── Create / Edit form ── */}
        <Card title={editing ? `Edit: ${editing.display_name}` : 'Create Class'}>
          <form className="teaching-form" onSubmit={saveClass}>
            <label className="login-label" htmlFor="class-name-input">
              Class Name <span className="field-required">*</span>
            </label>
            <input
              id="class-name-input"
              className="login-input login-input--plain teaching-input-wide"
              placeholder="e.g. Grade 5, Year 10"
              value={form.name}
              onChange={(e) => setField('name', e.target.value)}
              required
            />

            <label className="login-label" htmlFor="class-section-input">
              Section <span className="field-optional">(optional)</span>
            </label>
            <input
              id="class-section-input"
              className="login-input login-input--plain teaching-input-wide"
              placeholder="e.g. A, B, C"
              value={form.section}
              onChange={(e) => setField('section', e.target.value)}
            />

            {form.name && (
              <div className="class-preview">
                Preview: <strong>{[form.name.trim(), form.section.trim()].filter(Boolean).join(' - ')}</strong>
              </div>
            )}

            <label className="login-label" htmlFor="class-desc-input">
              Description <span className="field-optional">(optional)</span>
            </label>
            <textarea
              id="class-desc-input"
              className="login-input login-input--plain teaching-input-wide class-textarea"
              placeholder="Notes about this class…"
              value={form.description}
              onChange={(e) => setField('description', e.target.value)}
              rows={3}
            />

            <div className="feature-actions">
              <button type="submit" className="btn btn-primary" disabled={busy}>
                {editing ? 'Save Changes' : 'Create Class'}
              </button>
              {editing && (
                <button type="button" className="btn btn-ghost" disabled={busy} onClick={cancelEdit}>Cancel</button>
              )}
            </div>
          </form>
        </Card>

      </div>

      {/* ── Visual grouped cards ── */}
      {!loading && !error && (
        <>
          <div className="students-toolbar" style={{ marginBottom: '1.25rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
            <div className="topbar-search-label" style={{ flex: '1', minWidth: '240px', maxWidth: '400px', margin: 0 }}>
              <span className="topbar-search-icon" style={{ pointerEvents: 'none' }}>🔍</span>
              <input
                type="search"
                className="topbar-search"
                placeholder="Search name, section, description…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="class-stats" style={{ margin: 0 }}>
              <span className="class-stat-chip">{classes.length} classes</span>
              <span className="class-stat-chip">{teachers.length} teachers</span>
              <span className="class-stat-chip">{students.length} students</span>
            </div>
          </div>

          {grouped.length === 0 ? (
            <div className="students-empty" style={{ padding: '2rem 0', textAlign: 'center' }}>
              <p className="muted">No classes match your search, or none created yet.</p>
            </div>
          ) : (
            <div className="classes-groups">
              {grouped.map(([gradeName, sections]) => (
                <div key={gradeName} className="class-group-card">
                  <div className="class-group-header">
                    <span className="class-group-name">{gradeName}</span>
                    <span className="class-group-count">
                      {sections.length} section{sections.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="class-sections-row">
                    {sections.map((cls) => {
                      const clsTeachers = teachersByClass.get(cls.id) || []
                      const clsStudents = studentsByClass.get(cls.id) || []
                      return (
                        <div key={cls.id} className="class-section-card class-section-card--wide">
                          <div className="class-section-top">
                            <div className="class-section-badge">
                              {cls.section || <span style={{ fontSize: '0.7rem' }}>—</span>}
                            </div>
                            <div className="class-section-name">{cls.display_name}</div>
                            {cls.description && (
                              <div className="class-section-desc">{cls.description}</div>
                            )}
                          </div>

                          {/* Teachers */}
                          <div className="class-member-section">
                            <div className="class-member-label">
                              👨‍🏫 Teachers ({clsTeachers.length})
                            </div>
                            {clsTeachers.length === 0 ? (
                              <span className="muted" style={{ fontSize: '0.75rem' }}>None assigned</span>
                            ) : (
                              <div className="class-member-list">
                                {clsTeachers.map((t) => {
                                  const u = userById.get(t.user)
                                  return (
                                    <span key={t.id} className="class-member-chip class-member-chip--teacher">
                                      {fullName(u)}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>

                          {/* Students */}
                          <div className="class-member-section">
                            <div className="class-member-label">
                              🎓 Students ({clsStudents.length})
                            </div>
                            {clsStudents.length === 0 ? (
                              <span className="muted" style={{ fontSize: '0.75rem' }}>None enrolled</span>
                            ) : (
                              <div className="class-member-list">
                                {clsStudents.map((s) => {
                                  const u = userById.get(s.user)
                                  return (
                                    <span key={s.id} className="class-member-chip class-member-chip--student">
                                      {fullName(u)}
                                    </span>
                                  )
                                })}
                              </div>
                            )}
                          </div>

                          <div className="class-section-actions">
                            <button type="button" className="btn btn-ghost btn-xs" onClick={() => startEdit(cls)}>Edit</button>
                            <button type="button" className="btn btn-primary btn-xs" onClick={() => deleteClass(cls)} disabled={busy}>Delete</button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── Table view ── */}
          {filtered.length > 0 && (
            <Card title={`All Classes (${filtered.length})`} style={{ marginTop: '1.5rem' }}>
              <div className="feature-table-wrap">
                <table className="feature-table admin-classes-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Class</th>
                      <th>Section</th>
                      <th>Teachers</th>
                      <th>Students</th>
                      <th>Description</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((cls, idx) => {
                      const clsTeachers = teachersByClass.get(cls.id) || []
                      const clsStudents = studentsByClass.get(cls.id) || []
                      return (
                        <tr key={cls.id}>
                          <td className="muted">{idx + 1}</td>
                          <td><span className="class-display-chip">{cls.display_name}</span></td>
                          <td>
                            {cls.section
                              ? <span className="badge badge-class">{cls.section}</span>
                              : <span className="muted">—</span>}
                          </td>
                          <td>
                            <span className="exam-count-chip">{clsTeachers.length}</span>
                          </td>
                          <td>
                            <span className="exam-count-chip">{clsStudents.length}</span>
                          </td>
                          <td className="class-table-desc">{cls.description || <span className="muted">—</span>}</td>
                          <td>
                            <div className="table-actions">
                              <button type="button" className="btn btn-ghost btn-xs" onClick={() => startEdit(cls)}>Edit</button>
                              <button type="button" className="btn btn-primary btn-xs" onClick={() => deleteClass(cls)} disabled={busy}>Delete</button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}
    </>
  )
}
