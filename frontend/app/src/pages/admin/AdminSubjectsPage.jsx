import { useEffect, useMemo, useState } from 'react'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'

/* ─── helpers ─────────────────────────────────────────────────── */
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

function splitClasses(text) {
  return text
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)
}

/**
 * Return teacher PKs that are currently assigned to a given subject id.
 * We derive this from teachers whose `assigned_subjects` array contains the subject id.
 */
function teachersForSubject(teachers, subjectId) {
  return teachers
    .filter((t) => (t.subject_ids || []).map(Number).includes(Number(subjectId)))
    .map((t) => t.id)
}

/* ─── component ───────────────────────────────────────────────── */
export function AdminSubjectsPage() {
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [subjects, setSubjects] = useState([])
  const [teachers, setTeachers] = useState([])
  const [users, setUsers] = useState([])

  const [search, setSearch] = useState('')

  /* ── create-form state ─────────────────────────────────────── */
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [description, setDescription] = useState('')
  // Per-teacher assignment: { teacherId: classIdsText }
  const [teacherAssignments, setTeacherAssignments] = useState({})

  /* ── edit state ────────────────────────────────────────────── */
  const [editing, setEditing] = useState(null)
  const [editName, setEditName] = useState('')
  const [editCode, setEditCode] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editTeacherAssignments, setEditTeacherAssignments] = useState({})

  /* ── data loading ─────────────────────────────────────────── */
  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const [subjectsRes, teachersRes, usersRes] = await Promise.all([
        apiFetch('/subjects/'),
        apiFetch('/teachers/'),
        apiFetch('/users/'),
      ])
      const [subjectsJson, teachersJson, usersJson] = await Promise.all([
        subjectsRes.json().catch(() => []),
        teachersRes.json().catch(() => []),
        usersRes.json().catch(() => []),
      ])
      if (!subjectsRes.ok) throw new Error(subjectsJson.detail || `Failed subjects (${subjectsRes.status})`)
      if (!teachersRes.ok) throw new Error(teachersJson.detail || `Failed teachers (${teachersRes.status})`)
      if (!usersRes.ok)    throw new Error(usersJson.detail    || `Failed users (${usersRes.status})`)

      setSubjects(parseList(subjectsJson))
      setTeachers(parseList(teachersJson))
      setUsers(parseList(usersJson))
    } catch (e) {
      setError(e.message || 'Failed to load subjects module.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  /* ── derived maps ─────────────────────────────────────────── */
  const userById = useMemo(() => new Map(users.map((u) => [u.id, u])), [users])

  /**
   * For a given subject (by id) return all teachers assigned + their class lists.
   * We look up TeacherSubjectClass via `teacher.subject_class_relations`.
   */
  function teacherRowsForSubject(subjectId) {
    const sid = Number(subjectId)
    return teachers
      .filter((t) => (t.subject_ids || []).map(Number).includes(sid))
      .map((t) => {
        const rels = (t.subject_class_relations || []).filter(
          (r) => Number(r.subject) === sid
        )
        const classIds = rels.map((r) => r.class_id).filter(Boolean)
        return { teacher: t, classIds }
      })
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return subjects
    return subjects.filter((s) => {
      const hay = `${s.name || ''} ${s.code || ''} ${s.description || ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [subjects, search])

  /* ─────────────────────────────────────────────────────────────
     Teacher assignment helpers
     teacherAssignments = { [teacherId]: "G10-A, G10-B" }
     A teacher is "selected" when its key exists in the map.
  ───────────────────────────────────────────────────────────── */
  function toggleTeacher(assignments, setAssignments, teacherId) {
    const tid = String(teacherId)
    setAssignments((prev) => {
      if (tid in prev) {
        const next = { ...prev }
        delete next[tid]
        return next
      }
      return { ...prev, [tid]: '' }
    })
  }

  function setClassText(assignments, setAssignments, teacherId, text) {
    const tid = String(teacherId)
    setAssignments((prev) => ({ ...prev, [tid]: text }))
  }

  /**
   * After creating/updating a subject, sync teacher assignments.
   * For each teacher:
   *   - if selected → PATCH teacher: ensure subjectId is in their subject_ids
   *   - if not selected → PATCH teacher: remove subjectId from their subject_ids
   *   - always update class_ids (TeacherSubjectClass) via teacher PATCH
   */
  async function syncTeacherAssignments(subjectId, assignments) {
    const sid = Number(subjectId)

    await Promise.all(
      teachers.map(async (t) => {
        const tid = String(t.id)
        const currentSubjectIds = (t.subject_ids || []).map(Number)
        const isSelected = tid in assignments

        let newSubjectIds
        if (isSelected && !currentSubjectIds.includes(sid)) {
          newSubjectIds = [...currentSubjectIds, sid]
        } else if (!isSelected && currentSubjectIds.includes(sid)) {
          newSubjectIds = currentSubjectIds.filter((x) => x !== sid)
        } else {
          // No change in subject membership — but still may need class_ids update
          newSubjectIds = null
        }

        // Build class_ids: keep all existing teacher classes, then replace those
        // belonging to this subject (via subject_class_relations)
        const existingClassIdsText = (() => {
          // Get current class_ids for this teacher (all subjects)
          const allClassIds = (t.class_ids || [])
          return allClassIds
        })()

        if (isSelected) {
          const newClassIds = splitClasses(assignments[tid] || '')
          const body = {}
          if (newSubjectIds !== null) body.subject_ids = newSubjectIds
          // Merge class_ids: keep existing + add new ones for this subject
          // We re-derive the full set of class_ids from existing relations
          const existingOtherClassIds = (t.subject_class_relations || [])
            .filter((r) => Number(r.subject) !== sid)
            .map((r) => r.class_id)
            .filter(Boolean)
          const mergedClassIds = [...new Set([...existingOtherClassIds, ...newClassIds])]
          body.class_ids = mergedClassIds

          if (Object.keys(body).length) {
            await apiFetch(`/teachers/${t.id}/`, { method: 'PATCH', body })
          }
        } else if (newSubjectIds !== null) {
          // Unlink: remove subject + remove its class relations
          const existingOtherClassIds = (t.subject_class_relations || [])
            .filter((r) => Number(r.subject) !== sid)
            .map((r) => r.class_id)
            .filter(Boolean)
          await apiFetch(`/teachers/${t.id}/`, {
            method: 'PATCH',
            body: {
              subject_ids: newSubjectIds,
              class_ids: [...new Set(existingOtherClassIds)],
            },
          })
        }
      })
    )
  }

  /* ── create ───────────────────────────────────────────────── */
  async function createSubject(e) {
    e.preventDefault()
    setMessage('')
    if (!name.trim() || !code.trim()) {
      setMessage('Name and Code are required.')
      return
    }
    setBusy(true)
    try {
      const res = await apiFetch('/subjects/', {
        method: 'POST',
        body: { name: name.trim(), code: code.trim(), description: description.trim() },
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(json.detail || JSON.stringify(json) || `Create failed (${res.status})`)

      await syncTeacherAssignments(json.id, teacherAssignments)

      setMessage(`Subject created: ${json.code} — ${json.name}`)
      setName(''); setCode(''); setDescription(''); setTeacherAssignments({})
      await loadData()
    } catch (err) {
      setMessage(err.message || 'Create subject failed.')
    } finally {
      setBusy(false)
    }
  }

  /* ── edit helpers ─────────────────────────────────────────── */
  function startEdit(s) {
    setEditing(s)
    setEditName(s.name || '')
    setEditCode(s.code || '')
    setEditDescription(s.description || '')

    // Pre-populate teacher assignments from current data
    const initial = {}
    teacherRowsForSubject(s.id).forEach(({ teacher, classIds }) => {
      initial[String(teacher.id)] = classIds.join(', ')
    })
    setEditTeacherAssignments(initial)
    setMessage('')
  }

  function cancelEdit() {
    setEditing(null)
    setEditName(''); setEditCode(''); setEditDescription(''); setEditTeacherAssignments({})
  }

  async function saveEdit(e) {
    e.preventDefault()
    if (!editing) return
    setBusy(true)
    setMessage('')
    try {
      const res = await apiFetch(`/subjects/${editing.id}/`, {
        method: 'PATCH',
        body: {
          name: editName.trim(),
          code: editCode.trim(),
          description: editDescription.trim(),
        },
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(json.detail || JSON.stringify(json) || `Update failed (${res.status})`)

      await syncTeacherAssignments(editing.id, editTeacherAssignments)

      setMessage(`Subject updated: ${json.code || editCode} — ${json.name || editName}`)
      cancelEdit()
      await loadData()
    } catch (err) {
      setMessage(err.message || 'Update subject failed.')
    } finally {
      setBusy(false)
    }
  }

  /* ── delete ───────────────────────────────────────────────── */
  async function deleteSubject(s) {
    const ok = window.confirm(`Delete subject "${s.code} — ${s.name}"?\nThis will also remove all teacher assignments for this subject.`)
    if (!ok) return
    setBusy(true)
    setMessage('')
    try {
      const res = await apiFetch(`/subjects/${s.id}/`, { method: 'DELETE' })
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail || `Delete failed (${res.status})`)
      }
      setMessage(`Subject deleted: ${s.code}`)
      if (editing?.id === s.id) cancelEdit()
      await loadData()
    } catch (err) {
      setMessage(err.message || 'Delete subject failed.')
    } finally {
      setBusy(false)
    }
  }

  /* ─── teacher assignment panel (reusable render) ──────────── */
  function TeacherAssignmentPanel({ assignments, setAssignments }) {
    const assignedIds = Object.keys(assignments).map(Number)
    const availableTeachers = teachers.filter((t) => !assignedIds.includes(t.id))

    function addTeacher(teacherId) {
      if (!teacherId) return
      const tid = String(teacherId)
      setAssignments((prev) => ({ ...prev, [tid]: '' }))
    }

    function removeTeacher(teacherId) {
      const tid = String(teacherId)
      setAssignments((prev) => {
        const next = { ...prev }
        delete next[tid]
        return next
      })
    }

    if (teachers.length === 0) {
      return <span className="muted">No teacher profiles found.</span>
    }

    return (
      <div className="teacher-assign-panel">
        {/* ── Dropdown to add a teacher ── */}
        <div className="teacher-assign-dropdown-wrap">
          <select
            className="teacher-assign-dropdown"
            value=""
            onChange={(e) => {
              addTeacher(Number(e.target.value))
              e.target.value = ''
            }}
          >
            <option value="">Select a teacher to assign…</option>
            {availableTeachers.map((t) => {
              const u = userById.get(t.user)
              return (
                <option key={t.id} value={t.id}>
                  {t.teacher_id || `#${t.id}`} — {u ? fullName(u) : 'Unknown'}
                </option>
              )
            })}
          </select>
          {availableTeachers.length === 0 && assignedIds.length > 0 && (
            <span className="teacher-assign-all-msg">All teachers assigned</span>
          )}
        </div>

        {/* ── Selected teachers as styled cards ── */}
        {assignedIds.length > 0 && (
          <div className="teacher-assign-selected">
            {assignedIds.map((tid) => {
              const t = teachers.find((x) => x.id === Number(tid))
              if (!t) return null
              const u = userById.get(t.user)
              return (
                <div key={tid} className="teacher-assign-card">
                  <div className="teacher-assign-card-header">
                    <div className="teacher-assign-card-info">
                      <span className="teacher-assign-card-id">{t.teacher_id || `#${t.id}`}</span>
                      <span className="teacher-assign-card-name">{u ? fullName(u) : ''}</span>
                    </div>
                    <button
                      type="button"
                      className="teacher-assign-card-remove"
                      onClick={() => removeTeacher(Number(tid))}
                      title="Remove teacher"
                      aria-label={`Remove ${t.teacher_id || `#${t.id}`}`}
                    >
                      ✕
                    </button>
                  </div>
                  <input
                    className="login-input login-input--plain teacher-assign-classes"
                    placeholder="Classes (optional, e.g. G10-A, G10-B)"
                    value={assignments[String(tid)] || ''}
                    onChange={(ev) => setClassText(assignments, setAssignments, Number(tid), ev.target.value)}
                  />
                </div>
              )
            })}
          </div>
        )}
      </div>
    )
  }

  /* ── render ───────────────────────────────────────────────── */
  return (
    <>
      <PageHeader
        title="Subjects"
        subtitle="Create, edit, and delete subjects. Assign teachers and optionally tag class IDs per teacher."
      />

      <div className="admin-form-container">
        {/* ── Create Card ── */}
        <Card title="Create Subject">
          <form className="teaching-form" onSubmit={createSubject}>
            <label className="login-label" htmlFor="admin-subject-name">
              Name
            </label>
            <input
              id="admin-subject-name"
              className="login-input login-input--plain teaching-input-wide"
              placeholder="e.g. Mathematics"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />

            <label className="login-label" htmlFor="admin-subject-code">
              Code
            </label>
            <input
              id="admin-subject-code"
              className="login-input login-input--plain teaching-input-wide"
              placeholder="e.g. MATH101"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />

            <label className="login-label" htmlFor="admin-subject-description">
              Description <span className="field-optional">(optional)</span>
            </label>
            <textarea
              id="admin-subject-description"
              className="teaching-textarea"
              rows={3}
              placeholder="Brief description of this subject…"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />

            <label className="login-label">
              Assign Teachers <span className="field-optional">(optional — check teacher then add class IDs)</span>
            </label>
            <TeacherAssignmentPanel
              assignments={teacherAssignments}
              setAssignments={setTeacherAssignments}
            />

            <div className="feature-actions">
              <button type="submit" className="btn btn-primary" disabled={busy}>
                Create Subject
              </button>
            </div>
          </form>
        </Card>

        {/* ── Edit / Search Card ── */}
        {editing ? (
          <Card title={`Edit Subject: ${editing.code}`}>
            <form className="teaching-form" onSubmit={saveEdit}>
              <label className="login-label" htmlFor="edit-subject-name">
                Name
              </label>
              <input
                id="edit-subject-name"
                className="login-input login-input--plain teaching-input-wide"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                required
              />

              <label className="login-label" htmlFor="edit-subject-code">
                Code
              </label>
              <input
                id="edit-subject-code"
                className="login-input login-input--plain teaching-input-wide"
                value={editCode}
                onChange={(e) => setEditCode(e.target.value)}
                required
              />

              <label className="login-label" htmlFor="edit-subject-description">
                Description
              </label>
              <textarea
                id="edit-subject-description"
                className="teaching-textarea"
                rows={3}
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
              />

              <label className="login-label">
                Assigned Teachers <span className="field-optional">(toggle to link/unlink — add class IDs per teacher)</span>
              </label>
              <TeacherAssignmentPanel
                assignments={editTeacherAssignments}
                setAssignments={setEditTeacherAssignments}
              />

              <div className="feature-actions">
                <button type="submit" className="btn btn-primary" disabled={busy}>
                  Save
                </button>
                <button type="button" className="btn btn-ghost" disabled={busy} onClick={cancelEdit}>
                  Cancel
                </button>
              </div>
            </form>
          </Card>
        ) : null}
      </div>

      {message  ? <p className="teaching-msg">{message}</p>  : null}
      {loading  ? <p className="muted">Loading subjects…</p> : null}
      {!loading && error ? <p className="teaching-error">{error}</p> : null}

      {!loading && !error ? (
        <Card title="Subjects Directory">
          <div className="students-toolbar" style={{ marginBottom: '1.25rem' }}>
            <div className="topbar-search-label" style={{ maxWidth: '400px', margin: 0 }}>
              <span className="topbar-search-icon" style={{ pointerEvents: 'none' }}>🔍</span>
              <input
                type="search"
                className="topbar-search"
                placeholder="Search by name, code, description…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>

          {filtered.length ? (
            <div className="feature-table-wrap">
              <table className="feature-table admin-subjects-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Teachers &amp; Classes</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((s) => {
                    const rows = teacherRowsForSubject(s.id)
                    return (
                      <tr key={s.id}>
                        <td>
                          <span className="subject-code-badge">{s.code}</span>
                        </td>
                        <td>{s.name || '—'}</td>
                        <td className="subject-desc-cell">
                          {s.description ? (
                            <span title={s.description}>
                              {s.description.length > 60
                                ? `${s.description.slice(0, 60)}…`
                                : s.description}
                            </span>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td>
                          {rows.length ? (
                            <div className="teacher-class-list">
                              {rows.map(({ teacher, classIds }) => {
                                const u = userById.get(teacher.user)
                                return (
                                  <div key={teacher.id} className="teacher-class-row">
                                    <span className="badge badge-teacher">
                                      {teacher.teacher_id || `#${teacher.id}`}
                                    </span>
                                    {classIds.length ? (
                                      <span className="teacher-class-ids">
                                        {classIds.map((c) => (
                                          <span key={c} className="badge badge-class">
                                            {c}
                                          </span>
                                        ))}
                                      </span>
                                    ) : null}
                                  </div>
                                )
                              })}
                            </div>
                          ) : (
                            <span className="muted">—</span>
                          )}
                        </td>
                        <td>
                          <div className="table-actions">
                            <button
                              type="button"
                              className="btn btn-ghost btn-xs"
                              onClick={() => startEdit(s)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="btn btn-primary btn-xs"
                              onClick={() => deleteSubject(s)}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

            </div>
          ) : (
            <div className="students-empty" style={{ padding: '2rem 0', textAlign: 'center' }}>
              <p className="muted">No subjects match your search.</p>
            </div>
          )}
        </Card>
      ) : null}
    </>
  )
}
