import { useCallback, useEffect, useState, useMemo } from 'react'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch, apiFetchAll } from '../../lib/api'
import { useAuthStore } from '../../stores/authStore'
import { useTeacherProfile } from '../../hooks/useTeacherProfile'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

export function TeacherExamsPage() {
  const user = useAuthStore((s) => s.user)
  const {
    teacher: teacherProfile,
    mySubjectIds,
    myClassIds,
    myClassObjects,
    loading: profileLoading,
    error: profileError,
  } = useTeacherProfile()

  const [teacherId, setTeacherId] = useState(null)
  const [loadError, setLoadError] = useState('')
  const [allSubjects, setAllSubjects] = useState([])
  const [exams, setExams] = useState([])
  const [students, setStudents] = useState([])
  const [grades, setGrades] = useState([])
  const [tab, setTab] = useState('exam')
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  const [examName, setExamName] = useState('')
  const [examType, setExamType] = useState('quiz')
  const [examSubject, setExamSubject] = useState('')
  const [examTotalGrade, setExamTotalGrade] = useState(100)
  const [examDuration, setExamDuration] = useState(60)

  // Bulk Grading States
  const [bSubject, setBSubject] = useState('')
  const [bClass, setBClass] = useState('')
  const [bExam, setBExam] = useState('')
  const [bMax, setBMax] = useState(null)
  const [draftGrades, setDraftGrades] = useState({}) // { studentId: score (string) }

  const refreshData = useCallback(async () => {
    try {
      const [exRes, stRes, grRes] = await Promise.all([
        apiFetchAll('/exams/'),
        apiFetchAll('/students/'),
        apiFetchAll('/grades/'),
      ])
      setExams(exRes)
      setStudents(stRes)
      setGrades(grRes)
    } catch (e) {
      console.error('Failed to load data', e)
    }
  }, [])

  // Fetch all subjects once on mount — filtered to assigned ones in the `subjects` memo below
  useEffect(() => {
    apiFetchAll('/subjects/').then(setAllSubjects).catch(console.error)
  }, [])

  // Set teacherId from the shared profile hook
  useEffect(() => {
    if (profileLoading) return
    if (profileError) { setLoadError(profileError); return }
    if (!teacherProfile) {
      setLoadError('No teacher row linked to your user. Ask an admin to link your account.')
      return
    }
    setTeacherId(teacherProfile.id)
    refreshData()
  }, [profileLoading, profileError, teacherProfile, refreshData])

  // Subjects filtered to only this teacher's assigned subjects
  const subjects = useMemo(() => {
    if (mySubjectIds.length === 0) return []
    return allSubjects.filter((s) => mySubjectIds.includes(Number(s.id)))
  }, [allSubjects, mySubjectIds])

  // Only this teacher's exams
  const myExams = useMemo(() => {
    if (!teacherId) return []
    return exams.filter((x) => x.teacher === teacherId)
  }, [exams, teacherId])

  useEffect(() => {
    if (!bExam) {
      setBMax(null)
      return
    }
    let cancelled = false
      ; (async () => {
        const res = await apiFetch(`/exams/${bExam}/`)
        if (!res.ok || cancelled) return
        const detail = await res.json()
        // Use total_grade first, fall back to questions count
        const tg = detail.total_grade
        const n = tg ? Number(tg) : (Array.isArray(detail.questions) ? detail.questions.length : 0)
        if (!cancelled) setBMax(n)
      })()
    return () => {
      cancelled = true
    }
  }, [bExam])

  async function submitExam(e) {
    e.preventDefault()
    setMsg('')
    if (!teacherId) return
    if (!examName.trim() || !examSubject) {
      setMsg('Name and subject are required.')
      return
    }
    setBusy(true)
    try {
      const res = await apiFetch('/exams/', {
        method: 'POST',
        body: {
          name: examName.trim(),
          exam_type: examType,
          subject: Number(examSubject),
          teacher: teacherId,
          total_grade: Math.max(1, Number(examTotalGrade) || 100),
          duration: Math.max(1, Number(examDuration) || 60),
        },
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(JSON.stringify(data) || `HTTP ${res.status}`)
      setMsg(`Assessment created (id ${data.id}).`)
      setExamName('')
      setExamType('quiz')
      await refreshData()
    } catch (err) {
      setMsg(typeof err.message === 'string' ? err.message : 'Create assessment failed')
    } finally {
      setBusy(false)
    }
  }

  // Filter students based on class and subject
  const filteredStudents = useMemo(() => {
    if (!bSubject || !bClass) return []
    return students.filter((s) => {
      const matchClass = s.school_class === Number(bClass)
      const matchSubject = Array.isArray(s.subjects) && s.subjects.includes(Number(bSubject))
      return matchClass && matchSubject
    })
  }, [students, bSubject, bClass])

  // Pre-fill draft grades when the selection changes or grades/students update
  useEffect(() => {
    if (!bExam) {
      setDraftGrades({})
      return
    }
    const newDrafts = {}
    filteredStudents.forEach((student) => {
      const existingGrade = grades.find(
        (g) => g.student === student.id && g.exam === Number(bExam)
      )
      if (existingGrade) {
        newDrafts[student.id] = String(existingGrade.score)
      } else {
        newDrafts[student.id] = ''
      }
    })
    setDraftGrades(newDrafts)
  }, [bExam, filteredStudents, grades])

  function handleDraftChange(studentId, val) {
    setDraftGrades((prev) => ({ ...prev, [studentId]: val }))
  }

  async function saveAllGrades() {
    setMsg('')
    if (!bExam || filteredStudents.length === 0) return
    setBusy(true)
    
    let successCount = 0
    let errorCount = 0
    
    try {
      const promises = filteredStudents.map(async (student) => {
        const rawVal = draftGrades[student.id]
        if (!rawVal || rawVal.trim() === '') return // skip empty
        
        const scoreVal = Number(rawVal)
        const existingGrade = grades.find((g) => g.student === student.id && g.exam === Number(bExam))
        
        if (existingGrade) {
          // Update existing
          if (Number(existingGrade.score) === scoreVal) return // no change
          const res = await apiFetch(`/grades/${existingGrade.id}/`, {
            method: 'PATCH',
            body: { score: scoreVal }
          })
          if (res.ok) successCount++
          else errorCount++
        } else {
          // Create new
          const res = await apiFetch('/grades/', {
            method: 'POST',
            body: {
              student: student.id,
              exam: Number(bExam),
              score: scoreVal
            }
          })
          if (res.ok) successCount++
          else errorCount++
        }
      })
      
      await Promise.allSettled(promises)
      await refreshData()
      
      if (errorCount > 0) {
        setMsg(`Saved ${successCount} grade(s), but ${errorCount} failed.`)
      } else if (successCount > 0) {
        setMsg(`Successfully saved ${successCount} grade(s).`)
      } else {
        setMsg('No new or changed grades to save.')
      }
    } catch (err) {
      setMsg(typeof err.message === 'string' ? err.message : 'Save all grades failed')
    } finally {
      setBusy(false)
    }
  }

  if (loadError) {
    return (
      <>
        <PageHeader title="Assessments & Grades" subtitle="Create assessments and enter grades." />
        <p className="teaching-error">{loadError}</p>
      </>
    )
  }

  return (
    <>
      <PageHeader
        title="Assessments & Grades"
        subtitle="Create an assessment, then record student scores. Subject lists come from your school data."
      />

      <div className="teaching-tabs" role="tablist" aria-label="Assessment tools">
        <button
          type="button"
          className={`teaching-tab${tab === 'exam' ? ' is-active' : ''}`}
          onClick={() => setTab('exam')}
        >
          Create Assessment
        </button>
        <button
          type="button"
          className={`teaching-tab${tab === 'grade' ? ' is-active' : ''}`}
          onClick={() => setTab('grade')}
        >
          Grade Entry
        </button>
      </div>

      {msg ? <p className="teaching-msg">{msg}</p> : null}

      {tab === 'exam' ? (
        <Card title="Create Assessment">
          <form className="teaching-form" onSubmit={submitExam}>
            <label className="login-label" htmlFor="te-exam-name">
              Assessment Title
            </label>
            <input
              id="te-exam-name"
              className="login-input login-input--plain teaching-input-wide"
              value={examName}
              onChange={(e) => setExamName(e.target.value)}
              placeholder="e.g. Unit 3 Quiz"
              required
            />
            <label className="login-label" htmlFor="te-exam-type">
              Assessment Type
            </label>
            <select
              id="te-exam-type"
              className="login-input login-input--plain teaching-input-wide"
              value={examType}
              onChange={(e) => setExamType(e.target.value)}
              required
            >
              <option value="quiz">Quiz</option>
              <option value="assignment">Assignment</option>
              <option value="midterm">Midterm</option>
              <option value="final">Final</option>
            </select>
            <label className="login-label" htmlFor="te-exam-subject">
              Subject
            </label>
            <select
              id="te-exam-subject"
              className="login-input login-input--plain teaching-input-wide"
              value={examSubject}
              onChange={(e) => setExamSubject(e.target.value)}
              required
            >
              <option value="">Select subject…</option>
              {subjects.length === 0
                ? <option disabled>No subjects assigned to you yet</option>
                : subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.code ? `${s.code} — ` : ''}{s.name}
                    </option>
                  ))
              }
            </select>
            <label className="login-label" htmlFor="te-exam-total-grade">
              Total Grade
            </label>
            <input
              id="te-exam-total-grade"
              type="number"
              min={1}
              step="0.01"
              className="login-input login-input--plain teaching-input-narrow"
              value={examTotalGrade}
              onChange={(e) => setExamTotalGrade(e.target.value)}
            />
            <label className="login-label" htmlFor="te-exam-duration">
              Duration (minutes)
            </label>
            <input
              id="te-exam-duration"
              type="number"
              min={1}
              className="login-input login-input--plain teaching-input-narrow"
              value={examDuration}
              onChange={(e) => setExamDuration(e.target.value)}
            />
            <div className="feature-actions">
              <button type="submit" className="btn btn-primary" disabled={busy || !teacherId}>
                Create Assessment
              </button>
            </div>
          </form>
        </Card>
      ) : null}

      {tab === 'grade' ? (
        <Card title="Grade Entry">
          <div className="teaching-form">
            <div className="grade-filters" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <div style={{ flex: '1 1 200px' }}>
                <label className="login-label" htmlFor="te-b-subject">Subject</label>
                <select
                  id="te-b-subject"
                  className="login-input login-input--plain teaching-input-wide"
                  value={bSubject}
                  onChange={(e) => setBSubject(e.target.value)}
                >
                  <option value="">Select subject…</option>
                  {subjects.length === 0
                    ? <option disabled>No subjects assigned to you yet</option>
                    : subjects.map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))
                  }
                </select>
              </div>

              <div style={{ flex: '1 1 200px' }}>
                <label className="login-label" htmlFor="te-b-class">Class</label>
                <select
                  id="te-b-class"
                  className="login-input login-input--plain teaching-input-wide"
                  value={bClass}
                  onChange={(e) => setBClass(e.target.value)}
                >
                  <option value="">Select class…</option>
                  {myClassObjects.length === 0
                    ? <option disabled>No classes assigned to you yet</option>
                    : myClassObjects.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))
                  }
                </select>
              </div>

              <div style={{ flex: '1 1 200px' }}>
                <label className="login-label" htmlFor="te-b-exam">Assessment</label>
                <select
                  id="te-b-exam"
                  className="login-input login-input--plain teaching-input-wide"
                  value={bExam}
                  onChange={(e) => setBExam(e.target.value)}
                >
                  <option value="">Select assessment…</option>
                  {myExams
                    .filter((x) => !bSubject || x.subject === Number(bSubject))
                    .map((x) => (
                      <option key={x.id} value={x.id}>{x.name} ({x.exam_type_display})</option>
                    ))}
                </select>
              </div>
            </div>

            {bMax != null ? (
              <p className="muted teaching-hint" style={{ marginBottom: '1rem' }}>
                Max score for this assessment: <strong>{bMax}</strong>
              </p>
            ) : null}

            {bSubject && bClass && bExam ? (
              filteredStudents.length > 0 ? (
                <div className="feature-table-wrap">
                  <table className="feature-table">
                    <thead>
                      <tr>
                        <th style={{ width: '60px' }}>Photo</th>
                        <th>Student Name</th>
                        <th>Student ID</th>
                        <th style={{ width: '120px' }}>Score</th>
                        <th style={{ width: '100px' }}>Percentage</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredStudents.map((s) => {
                        const valStr = draftGrades[s.id] || ''
                        const valNum = Number(valStr)
                        let pct = null
                        if (valStr !== '' && bMax > 0) {
                          pct = (valNum / bMax) * 100
                        }
                        const isFailed = pct !== null && pct < 60
                        
                        return (
                          <tr key={s.id} style={isFailed ? { backgroundColor: 'rgba(239, 68, 68, 0.05)' } : {}}>
                            <td>
                              {s.photo_url ? (
                                <img src={s.photo_url} alt={s.student_id} className="student-table-avatar" style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover' }} />
                              ) : (
                                <div className="student-table-avatar student-table-avatar--empty" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>📷</div>
                              )}
                            </td>
                            <td>{s.user_display_name || `Student #${s.id}`}</td>
                            <td>{s.student_id || '—'}</td>
                            <td>
                              <input
                                type="number"
                                min={0}
                                max={bMax || undefined}
                                className="login-input login-input--plain teaching-input-narrow"
                                value={valStr}
                                onChange={(e) => handleDraftChange(s.id, e.target.value)}
                                style={{ margin: 0, padding: '0.25rem 0.5rem', width: '100%' }}
                              />
                            </td>
                            <td>
                              {pct !== null ? (
                                <span style={{ fontWeight: 600, color: isFailed ? 'var(--color-danger)' : 'var(--color-success)' }}>
                                  {pct.toFixed(1)}%
                                </span>
                              ) : (
                                <span className="muted">—</span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                  
                  <div className="feature-actions" style={{ 
                    position: 'sticky', 
                    bottom: '-1rem', 
                    background: 'var(--color-card)', 
                    padding: '1rem', 
                    borderTop: '1px solid var(--border-color)', 
                    borderRadius: '0 0 var(--radius) var(--radius)',
                    marginTop: '1rem',
                    boxShadow: '0 -4px 12px rgba(0,0,0,0.05)'
                  }}>
                    <button type="button" className="btn btn-primary" style={{ width: '100%' }} onClick={saveAllGrades} disabled={busy}>
                      Save All Grades
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ padding: '2rem', textAlign: 'center', background: 'var(--bg-muted)', borderRadius: 'var(--radius)' }}>
                  <p className="muted">No students found for this class and subject combination.</p>
                </div>
              )
            ) : (
              <div style={{ padding: '2rem', textAlign: 'center', background: 'var(--bg-muted)', borderRadius: 'var(--radius)' }}>
                <p className="muted">Please select a Subject, Class, and Exam to enter grades.</p>
              </div>
            )}
          </div>
        </Card>
      ) : null}

      <Card title="Your Assessments (refresh)">
        <p className="muted">{exams.length ? `${exams.length} assessment(s) loaded.` : 'No assessments yet.'}</p>
        <button type="button" className="btn btn-ghost" disabled={busy || !teacherId} onClick={() => refreshData()}>
          Reload lists
        </button>
      </Card>
    </>
  )
}
