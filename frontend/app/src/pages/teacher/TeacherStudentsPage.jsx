import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetchAll } from '../../lib/api'
import { useTeacherProfile } from '../../hooks/useTeacherProfile'

function fullName(user) {
  if (!user) return '—'
  const n = [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
  return n || user.username || '—'
}

function formatPct(value) {
  if (value == null || Number.isNaN(value)) return '—'
  return `${Math.round(value)}%`
}

export function TeacherStudentsPage() {
  const navigate = useNavigate()
  const {
    teacher,
    mySubjectIds,
    myClassIds,
    myClassObjects,
    loading: profileLoading,
    error: profileError,
  } = useTeacherProfile()

  const [dataLoading, setDataLoading] = useState(true)
  const [dataError, setDataError] = useState('')
  const [message, setMessage] = useState('')

  const [allSubjects, setAllSubjects] = useState([])
  const [studentsData, setStudentsData] = useState([])

  const [search, setSearch] = useState('')
  const [selectedClassId, setSelectedClassId] = useState(null)
  const [selectedSubjectId, setSelectedSubjectId] = useState('all')

  useEffect(() => {
    if (profileLoading) return          // wait for profile first
    let disposed = false
    ;(async () => {
      setDataLoading(true)
      setDataError('')
      try {
        const [subjectsData, studentsRaw, usersData, attendanceData, gradesData] =
          await Promise.all([
            apiFetchAll('/subjects/'),
            apiFetchAll('/students/'),
            apiFetchAll('/users/'),
            apiFetchAll('/attendance/'),
            apiFetchAll('/grades/'),
          ])

        const userById = new Map(usersData.map((u) => [u.id, u]))

        const attendanceByStudent = new Map()
        for (const rec of attendanceData) {
          if (!rec.student) continue
          const prev = attendanceByStudent.get(rec.student) || { total: 0, present: 0 }
          prev.total += 1
          if (rec.status === 'present') prev.present += 1
          attendanceByStudent.set(rec.student, prev)
        }

        const gradesByStudent = new Map()
        for (const g of gradesData) {
          if (!g.student) continue
          const prev = gradesByStudent.get(g.student) || { totalPct: 0, count: 0 }
          const pct = typeof g.percentage === 'number' ? g.percentage : 0
          prev.totalPct += pct
          prev.count += 1
          gradesByStudent.set(g.student, prev)
        }

        const rows = studentsRaw.map((s) => {
          const att = attendanceByStudent.get(s.id)
          const attendancePct = att && att.total > 0 ? (att.present / att.total) * 100 : null
          const gs = gradesByStudent.get(s.id)
          const avgGrade = gs && gs.count > 0 ? gs.totalPct / gs.count : null
          return {
            id: s.id,
            userId: s.user,
            name: fullName(userById.get(s.user)),
            studentId: s.student_id || '—',
            classId: s.school_class,
            attendancePct,
            avgGrade,
            subjectIds: (s.subjects || []).map(Number),
          }
        })

        if (!disposed) {
          setAllSubjects(subjectsData)
          setStudentsData(rows)
        }
      } catch (e) {
        if (!disposed) setDataError(e.message || 'Failed to load data.')
      } finally {
        if (!disposed) setDataLoading(false)
      }
    })()
    return () => { disposed = true }
  }, [profileLoading])  // re-run once profile is done

  // Only my assigned subjects
  const mySubjects = useMemo(
    () => allSubjects.filter((s) => mySubjectIds.includes(Number(s.id))),
    [allSubjects, mySubjectIds]
  )

  // Class stats — only for my assigned classes
  const classStats = useMemo(() => {
    const stats = {}
    myClassObjects.forEach((c) => {
      const classStudents = studentsData.filter(
        (s) => s.classId === c.id && (mySubjectIds.length === 0 || s.subjectIds.some((sid) => mySubjectIds.includes(sid)))
      )
      let totalAtt = 0, countAtt = 0, totalGrade = 0, countGrade = 0
      classStudents.forEach((s) => {
        if (s.attendancePct != null) { totalAtt += s.attendancePct; countAtt++ }
        if (s.avgGrade != null) { totalGrade += s.avgGrade; countGrade++ }
      })
      stats[c.id] = {
        count: classStudents.length,
        avgAtt: countAtt > 0 ? totalAtt / countAtt : null,
        avgGrade: countGrade > 0 ? totalGrade / countGrade : null,
      }
    })
    return stats
  }, [myClassObjects, studentsData, mySubjectIds])

  // Students visible in the selected class — filtered by subject
  const filteredStudents = useMemo(() => {
    if (!selectedClassId) return []
    const q = search.trim().toLowerCase()
    return studentsData.filter((s) => {
      if (s.classId !== selectedClassId) return false
      // Must share at least one of my subjects
      if (mySubjectIds.length > 0 && !s.subjectIds.some((sid) => mySubjectIds.includes(sid))) return false
      // Additional per-subject filter
      if (selectedSubjectId !== 'all' && !s.subjectIds.includes(Number(selectedSubjectId))) return false
      if (q && !s.name.toLowerCase().includes(q)) return false
      return true
    })
  }, [studentsData, selectedClassId, selectedSubjectId, search, mySubjectIds])

  const loading = profileLoading || dataLoading
  const error = profileError || dataError
  const selectedClassName = myClassObjects.find((c) => c.id === selectedClassId)?.name || 'Class'

  function onAddGrade(student) {
    navigate('/teacher/exams')
    setTimeout(() => setMessage(`Opened Exams & grades for ${student.name}.`), 0)
  }

  return (
    <>
      <PageHeader
        title="My Students"
        subtitle="Students in your assigned classes. Select a class to view performance."
      />

      {loading ? <p className="muted">Loading students...</p> : null}
      {!loading && error ? <p className="teaching-error">{error}</p> : null}

      {!loading && !error && myClassObjects.length === 0 && (
        <div style={{ padding: '3rem', textAlign: 'center', background: 'var(--ss-bg-main)', borderRadius: '12px', border: '1px dashed var(--ss-border)' }}>
          <p className="muted" style={{ fontSize: '1.1rem' }}>
            No classes have been assigned to you yet. Please contact an administrator.
          </p>
        </div>
      )}

      {!loading && !error && myClassObjects.length > 0 && (
        <div className="class-cards-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          {myClassObjects.map((c) => {
            const st = classStats[c.id] || { count: 0, avgAtt: null, avgGrade: null }
            const isActive = selectedClassId === c.id
            return (
              <div
                key={c.id}
                onClick={() => setSelectedClassId(c.id)}
                style={{
                  padding: '1.5rem',
                  borderRadius: '12px',
                  border: isActive ? '1px solid var(--ss-text)' : '1px solid var(--ss-border)',
                  background: isActive ? 'var(--ss-bg-main)' : 'var(--ss-bg-card)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: isActive ? '0 4px 12px rgba(0,0,0,0.05)' : '0 2px 4px rgba(0,0,0,0.02)',
                }}
              >
                <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1.1rem', color: isActive ? 'var(--ss-text)' : 'var(--ss-text)' }}>{c.name}</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.85rem', color: 'var(--ss-text-muted)' }}>
                  <span style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Students:</span> <strong style={{ color: 'var(--ss-text)' }}>{st.count}</strong>
                  </span>
                  <span style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Avg Attendance:</span> <strong style={{ color: 'var(--ss-text)' }}>{formatPct(st.avgAtt)}</strong>
                  </span>
                  <span style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Avg Grade:</span> <strong style={{ color: 'var(--ss-text)' }}>{formatPct(st.avgGrade)}</strong>
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {!loading && !error && selectedClassId && (
        <Card title={`Students in ${selectedClassName}`}>
          <div className="students-toolbar" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
            <input
              type="search"
              className="login-input login-input--plain students-search"
              placeholder="Search by name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ flex: '1 1 200px' }}
            />
            {mySubjects.length > 0 && (
              <select
                className="login-input login-input--plain students-class-filter"
                value={selectedSubjectId}
                onChange={(e) => setSelectedSubjectId(e.target.value)}
                style={{ flex: '0 0 250px' }}
              >
                <option value="all">All My Subjects</option>
                {mySubjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            )}
          </div>

          {message ? <p className="teaching-msg">{message}</p> : null}

          {filteredStudents.length ? (
            <div className="feature-table-wrap">
              <table className="feature-table students-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Student ID</th>
                    <th>Attendance %</th>
                    <th>Avg Grade</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.map((s) => (
                    <tr key={s.id}>
                      <td>{s.name}</td>
                      <td>{s.studentId}</td>
                      <td>
                        <span style={{ fontWeight: 500, color: s.attendancePct != null && s.attendancePct < 75 ? 'var(--color-danger)' : 'inherit' }}>
                          {formatPct(s.attendancePct)}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 500, color: s.avgGrade != null && s.avgGrade < 60 ? 'var(--color-danger)' : 'inherit' }}>
                          {formatPct(s.avgGrade)}
                        </span>
                      </td>
                      <td>
                        <div className="table-actions">
                          <button type="button" className="btn btn-primary btn-xs" onClick={() => onAddGrade(s)}>
                            Add Grade
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="students-empty" style={{ padding: '2rem 0', textAlign: 'center' }}>
              <p className="muted">No students match your current search/filter in this class.</p>
            </div>
          )}
        </Card>
      )}

      {!loading && !error && myClassObjects.length > 0 && !selectedClassId && (
        <div style={{ padding: '3rem', textAlign: 'center', background: 'var(--ss-bg-main)', borderRadius: '12px', border: '1px dashed var(--ss-border)' }}>
          <p className="muted" style={{ fontSize: '1.1rem' }}>Please select a class card above to view your students.</p>
        </div>
      )}
    </>
  )
}
