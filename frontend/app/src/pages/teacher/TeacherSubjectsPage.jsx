import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'
import { useTeacherProfile } from '../../hooks/useTeacherProfile'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

export function TeacherSubjectsPage() {
  const navigate = useNavigate()
  const { teacher, mySubjectIds, loading: profileLoading, error: profileError } = useTeacherProfile()

  const [allSubjects, setAllSubjects] = useState([])
  const [examsBySubject, setExamsBySubject] = useState({})
  const [dataLoading, setDataLoading] = useState(true)
  const [dataError, setDataError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    let disposed = false
    ;(async () => {
      setDataLoading(true)
      setDataError('')
      try {
        const [subjectsRes, examsRes] = await Promise.all([
          apiFetch('/subjects/'),
          apiFetch('/exams/'),
        ])
        const subjectsPayload = subjectsRes.ok ? await subjectsRes.json().catch(() => []) : []
        const examsPayload = examsRes.ok ? await examsRes.json().catch(() => []) : []

        const subjectsList = parseList(subjectsPayload)
        const examsList = parseList(examsPayload)

        // Count exams per subject — only MY exams
        const counts = {}
        for (const exam of examsList) {
          if (!exam.subject) continue
          // Only count exams that belong to this teacher
          if (teacher && exam.teacher !== teacher.id) continue
          counts[exam.subject] = (counts[exam.subject] || 0) + 1
        }

        if (!disposed) {
          setAllSubjects(subjectsList)
          setExamsBySubject(counts)
        }
      } catch (e) {
        if (!disposed) setDataError(e.message || 'Failed to load subjects.')
      } finally {
        if (!disposed) setDataLoading(false)
      }
    })()
    return () => {
      disposed = true
    }
  }, [teacher]) // re-run when teacher profile resolves

  // Filter to only this teacher's assigned subjects
  const subjects = useMemo(() => {
    if (mySubjectIds.length === 0) return []
    return allSubjects.filter((s) => mySubjectIds.includes(Number(s.id)))
  }, [allSubjects, mySubjectIds])

  const loading = profileLoading || dataLoading
  const error = profileError || dataError

  function viewStudents(subject) {
    navigate(`/teacher/students?subject=${subject.id}`)
  }

  function viewExams(subject) {
    navigate(`/teacher/exams?subject=${subject.id}`)
  }

  function addVideo(subject) {
    navigate(`/teacher/videos?subject=${subject.id}`)
    setMessage(`Opened Videos. You can upload for ${subject.name}.`)
  }

  return (
    <>
      <PageHeader
        title="My Subjects"
        subtitle="Subjects assigned to you. Click to view students, assessments, or upload videos."
      />

      {message ? <p className="teaching-msg">{message}</p> : null}

      {loading ? <p className="muted">Loading subjects...</p> : null}
      {!loading && error ? <p className="teaching-error">{error}</p> : null}

      {!loading && !error ? (
        subjects.length ? (
          <div className="grid-cards subjects-grid">
            {subjects.map((subject) => (
              <Card key={subject.id} className="subject-card">
                <h3 className="subject-card-name">{subject.name || 'Untitled subject'}</h3>
                <p className="subject-card-code">
                  Code: <code>{subject.code || '—'}</code>
                </p>
                <div className="subject-card-stats">
                  <span className="subject-stat">
                    Exams: <strong>{examsBySubject[subject.id] || 0}</strong>
                  </span>
                </div>
                <div className="table-actions subject-card-actions">
                  <button type="button" className="btn btn-ghost btn-xs" onClick={() => viewStudents(subject)}>
                    View Students
                  </button>
                  <button type="button" className="btn btn-ghost btn-xs" onClick={() => viewExams(subject)}>
                    View Exams
                  </button>
                  <button type="button" className="btn btn-primary btn-xs" onClick={() => addVideo(subject)}>
                    Add Video
                  </button>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <div className="subjects-empty">
            {teacher
              ? <p className="muted">No subjects have been assigned to you yet. Please contact an administrator.</p>
              : <p className="muted">Could not find your teacher profile. Please contact an administrator.</p>
            }
          </div>
        )
      ) : null}
    </>
  )
}
