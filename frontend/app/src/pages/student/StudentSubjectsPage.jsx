import { useEffect, useState } from 'react'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetchAll, apiFetch } from '../../lib/api'

const SUBJECT_ICONS = {
  math: '📐',
  maths: '📐',
  mathematics: '📐',
  eng: '📖',
  english: '📖',
  sci: '🔬',
  science: '🔬',
  phys: '⚡',
  physics: '⚡',
  chem: '🧪',
  chemistry: '🧪',
  bio: '🧬',
  biology: '🧬',
  hist: '📜',
  history: '📜',
  geo: '🌍',
  geography: '🌍',
  art: '🎨',
  arts: '🎨',
  music: '🎵',
  pe: '🏃',
  sport: '🏃',
  sports: '🏃',
  cs: '💻',
  computer: '💻',
  computing: '💻',
  it: '💻',
  arabic: '📝',
  islamic: '🕌',
  religion: '🕌',
  french: '🇫🇷',
  spanish: '🇪🇸',
  default: '📚',
}

function getSubjectIcon(name) {
  if (!name) return SUBJECT_ICONS.default
  const lower = name.toLowerCase()
  for (const [key, icon] of Object.entries(SUBJECT_ICONS)) {
    if (key !== 'default' && lower.includes(key)) {
      return icon
    }
  }
  return SUBJECT_ICONS.default
}

const EXAM_TYPE_BADGES = {
  quiz: { label: 'Quiz', color: '#3b82f6', bg: '#dbeafe' },
  midterm: { label: 'Midterm', color: '#f59e0b', bg: '#fef3c7' },
  final: { label: 'Final', color: '#ef4444', bg: '#fee2e2' },
  assignment: { label: 'Assignment', color: '#10b981', bg: '#d1fae5' },
}

function formatExamDate(dateStr) {
  if (!dateStr) return 'Date TBD'
  const d = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diffMs = d.getTime() - today.getTime()
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))

  const formatted = d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })

  if (diffDays === 0) return `Today — ${formatted}`
  if (diffDays === 1) return `Tomorrow — ${formatted}`
  if (diffDays > 1 && diffDays <= 7) return `In ${diffDays} days — ${formatted}`
  return formatted
}

function daysUntilExam(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Math.ceil((d.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
}

export function StudentSubjectsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [subjects, setSubjects] = useState([])
  const [upcomingExams, setUpcomingExams] = useState([])

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      // The backend SubjectViewSet restricts the student to see only their enrolled subjects
      const subjectsData = await apiFetchAll('/subjects/')

      // Fetch upcoming exams for the student
      const examsRes = await apiFetch('/exams/upcoming/')
      let examsData = []
      if (examsRes.ok) {
        const examsJson = await examsRes.json()
        examsData = Array.isArray(examsJson) ? examsJson : examsJson.results || []
      }

      setSubjects(subjectsData)
      setUpcomingExams(examsData)
    } catch (e) {
      setError(e.message || 'Failed to load subjects.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Group upcoming exams by subject id
  const examsBySubject = {}
  for (const exam of upcomingExams) {
    const sid = exam.subject
    if (!examsBySubject[sid]) examsBySubject[sid] = []
    examsBySubject[sid].push(exam)
  }

  // Separate upcoming exams not matched to any displayed subject
  const subjectIds = new Set(subjects.map((s) => s.id))
  const unmatchedExams = upcomingExams.filter((e) => !subjectIds.has(e.subject))

  return (
    <>
      <PageHeader
        title="My Subjects"
        subtitle="View the subjects you are enrolled in, your assigned teachers, and upcoming exams."
      />

      <Card>
        {loading ? <p className="muted">Loading subjects...</p> : null}
        {!loading && error ? <p className="feature-error">{error}</p> : null}

        {!loading && !error && subjects.length === 0 && (
          <div style={{ padding: '4rem 2rem', textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.5 }}>📚</div>
            <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.1rem' }}>No subjects enrolled</h3>
            <p style={{ color: '#6b7280', margin: 0 }}>
              You haven't been enrolled in any subjects yet. Contact your school administrator.
            </p>
          </div>
        )}

        {!loading && !error && subjects.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {subjects.map((s) => {
              const subjectExams = examsBySubject[s.id] || []
              return (
                <div
                  key={s.id}
                  style={{
                    border: '1px solid #eaeaea',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    background: '#fafafa',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                    transition: 'box-shadow 0.2s ease',
                  }}
                >
                  {/* Subject header */}
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                    <div style={{
                      fontSize: '2rem',
                      width: '3rem',
                      height: '3rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: '8px',
                      background: 'var(--primary-color-light, #e0e7ff)',
                    }}>
                      {getSubjectIcon(s.name)}
                    </div>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ margin: '0 0 0.25rem', fontSize: '1rem', color: 'var(--text-color)' }}>
                        {s.name}
                      </h3>
                      <div style={{ fontSize: '0.8rem', color: 'var(--primary-color)', fontWeight: 600 }}>
                        {s.code}
                      </div>
                    </div>
                  </div>

                  {s.description && (
                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#6b7280', lineHeight: 1.5 }}>
                      {s.description}
                    </p>
                  )}

                  {/* Teachers */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    paddingTop: '0.5rem',
                    borderTop: '1px solid #eaeaea',
                  }}>
                    <div>
                      {s.teacher_names && s.teacher_names.length > 0 ? (
                        <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                          <span style={{ fontWeight: 600, color: '#374151' }}>Teachers:</span>{' '}
                          {s.teacher_names.join(', ')}
                        </div>
                      ) : (
                        <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>No teacher assigned</div>
                      )}
                    </div>

                    {s.teachers_count != null && (
                      <span style={{
                        fontSize: '0.75rem',
                        background: 'var(--primary-color-light, #e0e7ff)',
                        color: 'var(--primary-color-dark, #4338ca)',
                        padding: '0.25rem 0.75rem',
                        borderRadius: '999px',
                        fontWeight: 600,
                      }}>
                        {s.teachers_count} teacher(s)
                      </span>
                    )}
                  </div>

                  {/* Upcoming exams for this subject */}
                  {subjectExams.length > 0 && (
                    <div style={{
                      marginTop: '0.25rem',
                      paddingTop: '0.75rem',
                      borderTop: '1px solid #eaeaea',
                    }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#374151', marginBottom: '0.5rem' }}>
                        📝 Upcoming Exams ({subjectExams.length})
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {subjectExams.map((exam) => {
                          const badge = EXAM_TYPE_BADGES[exam.exam_type] || { label: exam.exam_type_display || exam.exam_type, color: '#6b7280', bg: '#f3f4f6' }
                          const days = daysUntilExam(exam.exam_date)
                          const urgency = days != null && days <= 3 ? '#ef4444' : days != null && days <= 7 ? '#f59e0b' : '#6b7280'
                          return (
                            <div
                              key={exam.id}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                padding: '0.5rem 0.75rem',
                                borderRadius: '8px',
                                background: '#fff',
                                border: '1px solid #e5e7eb',
                              }}
                            >
                              <span style={{
                                fontSize: '0.7rem',
                                fontWeight: 600,
                                color: badge.color,
                                background: badge.bg,
                                padding: '0.2rem 0.5rem',
                                borderRadius: '4px',
                                whiteSpace: 'nowrap',
                              }}>
                                {badge.label}
                              </span>
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ fontSize: '0.85rem', fontWeight: 500, color: '#1f2937', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                  {exam.name}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: urgency, fontWeight: days != null && days <= 3 ? 600 : 400 }}>
                                  {formatExamDate(exam.exam_date)}
                                  {exam.duration ? ` · ${exam.duration} min` : ''}
                                </div>
                              </div>
                              {exam.teacher_name && (
                                <span style={{ fontSize: '0.7rem', color: '#9ca3af', whiteSpace: 'nowrap' }}>
                                  {exam.teacher_name}
                                </span>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {subjectExams.length === 0 && (
                    <div style={{
                      marginTop: '0.25rem',
                      paddingTop: '0.75rem',
                      borderTop: '1px solid #eaeaea',
                      fontSize: '0.8rem',
                      color: '#9ca3af',
                      textAlign: 'center',
                    }}>
                      No upcoming exams
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </Card>

      {/* Standalone upcoming exams section — exams not matched to displayed subjects */}
      {!loading && !error && unmatchedExams.length > 0 && (
        <Card title="📝 Other Upcoming Exams" style={{ marginTop: '1.5rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {unmatchedExams.map((exam) => {
              const badge = EXAM_TYPE_BADGES[exam.exam_type] || { label: exam.exam_type_display || exam.exam_type, color: '#6b7280', bg: '#f3f4f6' }
              return (
                <div
                  key={exam.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    background: '#fafafa',
                    border: '1px solid #e5e7eb',
                  }}
                >
                  <span style={{
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    color: badge.color,
                    background: badge.bg,
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    whiteSpace: 'nowrap',
                  }}>
                    {badge.label}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 500, color: '#1f2937' }}>
                      {exam.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                      {exam.subject_name || `Subject #${exam.subject}`} · {formatExamDate(exam.exam_date)}
                      {exam.duration ? ` · ${exam.duration} min` : ''}
                    </div>
                  </div>
                  {exam.teacher_name && (
                    <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                      {exam.teacher_name}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        </Card>
      )}
    </>
  )
}