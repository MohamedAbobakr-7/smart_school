import { useEffect, useMemo, useState } from 'react'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch, apiFetchAll } from '../../lib/api'

/* ─── helpers ─────────────────────────────────────────────────── */
function fullName(user) {
  if (!user) return '—'
  const n = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
  return n || user.username || '—'
}

/**
 * Extract a grade-level label from a SchoolClass name.
 * Handles "Grade 5 - A", "G5", "KG-A", "Year 10 - B", etc.
 */
function extractGradeLabel(className) {
  if (!className) return null
  const name = className.trim()
  if (/\bKG\b|\bKindergarten\b/i.test(name)) return 'Kindergarten'
  const m = name.match(/\b(?:Grade|G)\s*(\d{1,2})\b/i)
  if (m) return `Grade ${m[1]}`
  const ym = name.match(/\bYear\s*(\d{1,2})\b/i)
  if (ym) return `Year ${ym[1]}`
  return null
}

/**
 * Extract a grade-level VALUE (matching Exam.GRADE_CHOICES) from a class name.
 * Returns 'KG', '1'–'12', or '' if no match.
 */
function extractGradeValue(className) {
  if (!className) return ''
  const name = className.trim()
  if (/\bKG\b|\bKindergarten\b/i.test(name)) return 'KG'
  const m = name.match(/\b(?:Grade|G)\s*(\d{1,2})\b/i)
  if (m) return m[1]
  const ym = name.match(/\bYear\s*(\d{1,2})\b/i)
  if (ym) return ym[1]
  return ''
}

const EMPTY_EXAM = {
  name: '',
  exam_type: 'quiz',
  subject: '',
  teacher: '',
  grade: '',
  school_class: '',
  total_grade: 100,
  duration: 60,
  exam_date: '',
}

/* ─── component ───────────────────────────────────────────────── */
export function AdminExamsPage() {
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [exams, setExams] = useState([])
  const [subjects, setSubjects] = useState([])
  const [teachers, setTeachers] = useState([])
  const [students, setStudents] = useState([])
  const [grades, setGrades] = useState([])
  const [users, setUsers] = useState([])
  const [classes, setClasses] = useState([])

  const [search, setSearch] = useState('')
  const [activeTab, setActiveTab] = useState('exams') // 'exams' | 'grades'

  /* ── exam form ───────────────────────────────────────────────── */
  const [examForm, setExamForm] = useState(EMPTY_EXAM)
  const [editing, setEditing] = useState(null)

  const [gradeSearch, setGradeSearch] = useState('')

  /* ── load ────────────────────────────────────────────────────── */
  async function loadData() {
    setLoading(true)
    setError('')
    try {
      const [examsData, subjectsData, teachersData, studentsData, gradesData, usersData, classesData] =
        await Promise.all([
          apiFetchAll('/exams/'),
          apiFetchAll('/subjects/'),
          apiFetchAll('/teachers/'),
          apiFetchAll('/students/'),
          apiFetchAll('/grades/'),
          apiFetchAll('/users/'),
          apiFetchAll('/classes/'),
        ])
      setExams(examsData)
      setSubjects(subjectsData)
      setTeachers(teachersData)
      setStudents(studentsData)
      setGrades(gradesData)
      setUsers(usersData)
      setClasses(classesData)
    } catch (e) {
      setError(e.message || 'Failed to load exams module.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  /* ── derived maps ─────────────────────────────────────────────── */
  const userById     = useMemo(() => new Map(users.map((u) => [u.id, u])), [users])
  const subjectById  = useMemo(() => new Map(subjects.map((s) => [s.id, s])), [subjects])
  const teacherById  = useMemo(() => new Map(teachers.map((t) => [t.id, t])), [teachers])
  const studentById  = useMemo(() => new Map(students.map((s) => [s.id, s])), [students])
  const examById     = useMemo(() => new Map(exams.map((e) => [e.id, e])), [exams])
  const classById    = useMemo(() => new Map(classes.map((c) => [c.id, c])), [classes])

  // Grade levels derived from all classes in the system
  const gradeOptions = useMemo(() => {
    if (classes.length === 0) return []
    const seen = new Map()
    for (const c of classes) {
      const val = extractGradeValue(c.name || c.display_name)
      const label = extractGradeLabel(c.name || c.display_name)
      if (val && label && !seen.has(val)) {
        seen.set(val, label)
      }
    }
    return Array.from(seen.entries())
      .map(([value, label]) => ({ value, label }))
      .sort((a, b) => {
        if (a.value === 'KG') return -1
        if (b.value === 'KG') return 1
        return Number(a.value) - Number(b.value)
      })
  }, [classes])

  const filteredExams = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return exams
    return exams.filter((e) => {
      const sub = subjectById.get(e.subject)
      const tch = teacherById.get(e.teacher)
      const hay = `${e.name} ${sub?.name || ''} ${sub?.code || ''} ${e.grade_name || e.grade || ''} ${tch?.teacher_id || ''} ${e.exam_date || ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [exams, search, subjectById, teacherById])

  const filteredGrades = useMemo(() => {
    const q = gradeSearch.trim().toLowerCase()
    const list = grades
    if (!q) return list
    return list.filter((g) => {
      const st = studentById.get(g.student)
      const stUser = st ? userById.get(st.user) : null
      const ex = examById.get(g.exam)
      const hay = `${st?.student_id || ''} ${fullName(stUser)} ${ex?.name || ''} ${g.score}`.toLowerCase()
      return hay.includes(q)
    })
  }, [grades, gradeSearch, studentById, userById, examById])

  /* ── exam CRUD ───────────────────────────────────────────────── */
  function startCreate() {
    setEditing(null)
    setExamForm(EMPTY_EXAM)
  }

  function startEdit(exam) {
    setEditing(exam)
    setExamForm({
      name: exam.name || '',
      exam_type: exam.exam_type || 'quiz',
      subject: exam.subject || '',
      teacher: exam.teacher || '',
      grade: exam.grade || '',
      school_class: exam.school_class || '',
      total_grade: exam.total_grade || 100,
      duration: exam.duration || 60,
      exam_date: exam.exam_date || '',
    })
    setMessage('')
  }

  function cancelEdit() {
    setEditing(null)
    setExamForm(EMPTY_EXAM)
  }

  function setField(key, val) {
    setExamForm((prev) => ({ ...prev, [key]: val }))
  }

  async function saveExam(e) {
    e.preventDefault()
    setMessage('')
    if (!examForm.name.trim() || !examForm.subject || !examForm.teacher || !examForm.grade) {
      setMessage('Name, Subject, Teacher and Grade are required.')
      return
    }
    setBusy(true)
    try {
      // Find a matching school_class for the selected grade level
      const matchingClass = classes.find((c) => extractGradeValue(c.name || c.display_name) === examForm.grade)
      const body = {
        name: examForm.name.trim(),
        exam_type: examForm.exam_type,
        subject: Number(examForm.subject),
        teacher: Number(examForm.teacher),
        grade: examForm.grade,
        school_class: matchingClass ? Number(matchingClass.id) : null,
        total_grade: Number(examForm.total_grade) || 100,
        duration: Number(examForm.duration) || 60,
        exam_date: examForm.exam_date || null,
      }
      const res = editing
        ? await apiFetch(`/exams/${editing.id}/`, { method: 'PATCH', body })
        : await apiFetch('/exams/', { method: 'POST', body })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(json.detail || JSON.stringify(json) || `Save failed (${res.status})`)
      setMessage(editing ? `Assessment updated: ${json.name}` : `Assessment created: ${json.name}`)
      cancelEdit()
      await loadData()
    } catch (err) {
      setMessage(err.message || 'Save assessment failed.')
    } finally {
      setBusy(false)
    }
  }

  async function deleteExam(exam) {
    if (!window.confirm(`Delete assessment "${exam.name}"? All associated grades will also be deleted.`)) return
    setBusy(true)
    setMessage('')
    try {
      const res = await apiFetch(`/exams/${exam.id}/`, { method: 'DELETE' })
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail || `Delete failed (${res.status})`)
      }
      setMessage(`Assessment deleted: ${exam.name}`)
      if (editing?.id === exam.id) cancelEdit()
      await loadData()
    } catch (err) {
      setMessage(err.message || 'Delete failed.')
    } finally {
      setBusy(false)
    }
  }

  /* ── grade CRUD ──────────────────────────────────────────────── */
  async function deleteGrade(grade) {
    const st = studentById.get(grade.student)
    const ex = examById.get(grade.exam)
    if (!window.confirm(`Delete grade for ${st?.student_id || 'student'} in "${ex?.name || 'exam'}"?`)) return
    setBusy(true)
    setMessage('')
    try {
      const res = await apiFetch(`/grades/${grade.id}/`, { method: 'DELETE' })
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail || `Delete failed (${res.status})`)
      }
      setMessage('Grade deleted.')
      await loadData()
    } catch (err) {
      setMessage(err.message || 'Delete failed.')
    } finally {
      setBusy(false)
    }
  }

  /* ── render ───────────────────────────────────────────────────── */
  return (
    <>
      <PageHeader
        title="Assessments & Grades"
        subtitle="Create and manage assessments linked to subjects, teachers and classes. Record student grades."
      />

      {/* tab bar */}
      <div className="exam-tab-bar">
        <button
          type="button"
          className={`exam-tab ${activeTab === 'exams' ? 'exam-tab--active' : ''}`}
          onClick={() => setActiveTab('exams')}
        >
          📋 Assessments
        </button>
        <button
          type="button"
          className={`exam-tab ${activeTab === 'grades' ? 'exam-tab--active' : ''}`}
          onClick={() => setActiveTab('grades')}
        >
          🎓 Grades
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-xs"
          style={{ marginLeft: 'auto' }}
          onClick={loadData}
          disabled={loading}
        >
          {loading ? 'Refreshing…' : '↻ Refresh'}
        </button>
      </div>

      {message  ? <p className="teaching-msg">{message}</p>   : null}
      {loading  ? <p className="muted">Loading…</p>           : null}
      {!loading && error ? <p className="teaching-error">{error}</p> : null}

      {/* ════════════════ EXAMS TAB ════════════════ */}
      {activeTab === 'exams' && !loading && !error && (
        <>
          <div className="admin-form-container">
            {/* ── Create / Edit Exam Card ── */}
            <Card title={editing ? `Edit Assessment: ${editing.name}` : 'Create Assessment'}>
              <form className="teaching-form" onSubmit={saveExam}>
                <label className="login-label" htmlFor="exam-name">Assessment Title</label>
                <input
                  id="exam-name"
                  className="login-input login-input--plain teaching-input-wide"
                  placeholder="e.g. Mathematics Midterm 2024"
                  value={examForm.name}
                  onChange={(e) => setField('name', e.target.value)}
                  required
                />

                <label className="login-label" htmlFor="exam-type">Assessment Type</label>
                <select
                  id="exam-type"
                  className="login-input login-input--plain teaching-input-wide"
                  value={examForm.exam_type}
                  onChange={(e) => setField('exam_type', e.target.value)}
                  required
                >
                  <option value="quiz">Quiz</option>
                  <option value="assignment">Assignment</option>
                  <option value="midterm">Midterm</option>
                  <option value="final">Final</option>
                </select>

                <label className="login-label" htmlFor="exam-subject">Subject</label>
                <select
                  id="exam-subject"
                  className="login-input login-input--plain teaching-input-wide"
                  value={examForm.subject}
                  onChange={(e) => setField('subject', e.target.value)}
                  required
                >
                  <option value="">Select subject…</option>
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>{s.code} — {s.name}</option>
                  ))}
                </select>

                <label className="login-label" htmlFor="exam-teacher">Teacher</label>
                <select
                  id="exam-teacher"
                  className="login-input login-input--plain teaching-input-wide"
                  value={examForm.teacher}
                  onChange={(e) => setField('teacher', e.target.value)}
                  required
                >
                  <option value="">Select teacher…</option>
                  {teachers.map((t) => {
                    const u = userById.get(t.user)
                    return (
                      <option key={t.id} value={t.id}>
                        {t.teacher_id} — {fullName(u)}
                      </option>
                    )
                  })}
                </select>

                <div className="exam-form-row">
                  <div className="exam-form-col">
                    <label className="login-label" htmlFor="exam-grade">
                      Grade
                    </label>
                    <select
                      id="exam-grade"
                      className="login-input login-input--plain"
                      value={examForm.grade}
                      onChange={(e) => setField('grade', e.target.value)}
                      required
                    >
                      <option value="">Select grade…</option>
                      {gradeOptions.map((g) => (
                        <option key={g.value} value={g.value}>{g.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="exam-form-col">
                    <label className="login-label" htmlFor="exam-total-grade">Total Grade</label>
                    <input
                      id="exam-total-grade"
                      type="number"
                      min="1"
                      step="0.01"
                      className="login-input login-input--plain"
                      value={examForm.total_grade}
                      onChange={(e) => setField('total_grade', e.target.value)}
                      required
                    />
                  </div>
                  <div className="exam-form-col">
                    <label className="login-label" htmlFor="exam-duration">Duration (min)</label>
                    <input
                      id="exam-duration"
                      type="number"
                      min="1"
                      className="login-input login-input--plain"
                      value={examForm.duration}
                      onChange={(e) => setField('duration', e.target.value)}
                      required
                    />
                  </div>
                </div>

                <label className="login-label" htmlFor="exam-date">
                  Assessment Date <span className="field-optional">(optional)</span>
                </label>
                <input
                  id="exam-date"
                  type="date"
                  className="login-input login-input--plain teaching-input-wide"
                  value={examForm.exam_date}
                  onChange={(e) => setField('exam_date', e.target.value)}
                />

                <div className="feature-actions">
                  <button type="submit" className="btn btn-primary" disabled={busy}>
                    {editing ? 'Save Changes' : 'Create Assessment'}
                  </button>
                  {editing && (
                    <button type="button" className="btn btn-ghost" disabled={busy} onClick={cancelEdit}>
                      Cancel
                    </button>
                  )}
                </div>
              </form>
            </Card>

          </div>

          {/* Exams Table */}
          {!loading && !error && (
            <Card title={`Assessments Directory (${filteredExams.length})`}>
              <div className="students-toolbar" style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                <div className="topbar-search-label" style={{ flex: '1', minWidth: '240px', maxWidth: '400px', margin: 0 }}>
                  <span className="topbar-search-icon" style={{ pointerEvents: 'none' }}>🔍</span>
                  <input
                    type="search"
                    className="topbar-search"
                    placeholder="Search name, subject, teacher, class, date…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                <div className="muted" style={{ margin: 0, fontSize: '0.82rem' }}>
                  {filteredExams.length} of {exams.length} assessments
                </div>
              </div>

              {filteredExams.length ? (
                <div className="feature-table-wrap">
                  <table className="feature-table admin-exams-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Subject</th>
                      <th>Teacher</th>
                      <th>Grade</th>
                      <th>Total Grade</th>
                      <th>Date</th>
                      <th>Duration</th>
                      <th>Questions</th>
                      <th>Grades</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredExams.map((exam) => {
                      const sub = subjectById.get(exam.subject)
                      const tch = teacherById.get(exam.teacher)
                      const tUser = tch ? userById.get(tch.user) : null
                      return (
                        <tr key={exam.id}>
                          <td><strong>{exam.name}</strong></td>
                          <td>
                            <span className="status-chip" style={{ backgroundColor: 'var(--bg-muted)', color: 'var(--text)' }}>
                              {exam.exam_type_display || '—'}
                            </span>
                          </td>
                          <td>
                            {sub ? (
                              <span className="subject-code-badge">{sub.code}</span>
                            ) : '—'}
                          </td>
                          <td>
                            {tch ? (
                              <div className="exam-teacher-cell">
                                <span className="username-chip">@{tUser?.username || `#${tch.id}`}</span>
                                <span className="muted" style={{ fontSize: '0.78rem' }}>{tch.teacher_id}</span>
                              </div>
                            ) : '—'}
                          </td>
                          <td>
                            {exam.grade_name || exam.grade ? (
                              <span className="badge badge-class">{exam.grade_name || exam.grade}</span>
                            ) : <span className="muted">—</span>}
                          </td>
                          <td>{exam.total_grade ?? '—'}</td>
                          <td>{exam.exam_date || <span className="muted">—</span>}</td>
                          <td>{exam.duration} min</td>
                          <td>
                            <span className="exam-count-chip">{exam.questions_count ?? '—'}</span>
                          </td>
                          <td>
                            <span className="exam-count-chip">{exam.grades_count ?? '—'}</span>
                          </td>
                          <td>
                            <div className="table-actions">
                              <button
                                type="button"
                                className="btn btn-ghost btn-xs"
                                onClick={() => startEdit(exam)}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="btn btn-primary btn-xs"
                                onClick={() => deleteExam(exam)}
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
                <p className="muted">No assessments match your search.</p>
              </div>
            )}
          </Card>
        )}
        </>
      )}

      {/* ════════════════ GRADES TAB ════════════════ */}
      {activeTab === 'grades' && !loading && !error && (
        <>

          {/* Grades table */}
          {!loading && !error && (
            <Card title={`Grades Directory (${filteredGrades.length})`}>
              <div className="students-toolbar" style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                <div className="topbar-search-label" style={{ flex: '1', minWidth: '240px', maxWidth: '400px', margin: 0 }}>
                  <span className="topbar-search-icon" style={{ pointerEvents: 'none' }}>🔍</span>
                  <input
                    type="search"
                    className="topbar-search"
                    placeholder="Search by student, exam, score…"
                    value={gradeSearch}
                    onChange={(e) => setGradeSearch(e.target.value)}
                  />
                </div>
                <div className="muted" style={{ margin: 0, fontSize: '0.82rem' }}>
                  {filteredGrades.length} of {grades.length} grade records
                </div>
              </div>

              {filteredGrades.length ? (
                <div className="feature-table-wrap">
                  <table className="feature-table admin-grades-table">
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Student ID</th>
                      <th>Exam</th>
                      <th>Subject</th>
                      <th>Grade</th>
                      <th>Score</th>
                      <th>%</th>
                      <th>Grade</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredGrades.map((g) => {
                      const st = studentById.get(g.student)
                      const stUser = st ? userById.get(st.user) : null
                      const ex = examById.get(g.exam)
                      const sub = ex ? subjectById.get(ex.subject) : null
                      return (
                        <tr key={g.id}>
                          <td>{fullName(stUser)}</td>
                          <td>
                            <span className="username-chip">{st?.student_id || `#${g.student}`}</span>
                          </td>
                          <td>{ex?.name || `#${g.exam}`}</td>
                          <td>
                            {sub ? <span className="subject-code-badge">{sub.code}</span> : '—'}
                          </td>
                          <td>
                            {ex?.grade_name || ex?.grade ? (
                              <span className="badge badge-class">{ex?.grade_name || ex?.grade}</span>
                            ) : <span className="muted">—</span>}
                          </td>
                          <td><strong>{g.score}</strong></td>
                          <td>
                            <span className={`grade-pct-chip grade-pct--${g.grade_letter?.toLowerCase() || 'f'}`}>
                              {g.percentage != null ? `${g.percentage}%` : '—'}
                            </span>
                          </td>
                          <td>
                            <span className={`grade-letter-chip grade-letter--${g.grade_letter?.toLowerCase() || 'f'}`}>
                              {g.grade_letter || '—'}
                            </span>
                          </td>
                          <td>
                            <div className="table-actions">
                              <button
                                type="button"
                                className="btn btn-primary btn-xs"
                                onClick={() => deleteGrade(g)}
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
                <p className="muted">No grades match your search.</p>
              </div>
            )}
          </Card>
        )}
        </>
      )}
    </>
  )
}
