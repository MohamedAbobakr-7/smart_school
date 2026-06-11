import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'
import { useTeacherProfile } from '../../hooks/useTeacherProfile'

function formatPct(value) {
  if (value == null || isNaN(value)) return '0%'
  return `${Math.round(value)}%`
}

export function TeacherWeeklyReportsPage() {
  const {
    myClassIds,
    myClassObjects,
    loading: profileLoading,
    error: profileError,
  } = useTeacherProfile()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [generating, setGenerating] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)
  const [selectedClassId, setSelectedClassId] = useState('')
  const [generatedReport, setGeneratedReport] = useState(null)

  const [dashboardData, setDashboardData] = useState(null)
  const [studentsData, setStudentsData] = useState([])

  useEffect(() => {
    if (profileLoading) return
    let disposed = false
    async function load() {
      try {
        const [dashRes, studentsRes] = await Promise.all([
          apiFetch('/teachers/dashboard/'),
          apiFetch('/teachers/my-students/'),
        ])
        if (!dashRes.ok) {
          const body = await dashRes.json().catch(() => ({}))
          throw new Error(
            typeof body.detail === 'string' ? body.detail : `Dashboard failed (${dashRes.status})`
          )
        }
        if (!studentsRes.ok) {
          const body = await studentsRes.json().catch(() => ({}))
          throw new Error(
            typeof body.detail === 'string' ? body.detail : `Student stats failed (${studentsRes.status})`
          )
        }
        const dash = await dashRes.json()
        const studentsJson = await studentsRes.json()
        if (!Array.isArray(studentsJson)) {
          throw new Error('Invalid student stats response.')
        }

        if (!disposed) {
          setDashboardData(dash)
          setStudentsData(studentsJson)
        }
      } catch (err) {
        if (!disposed) setError(err.message || 'Failed to load reporting data.')
      } finally {
        if (!disposed) setLoading(false)
      }
    }
    load()
    return () => { disposed = true }
  }, [profileLoading])

  const scopedStudents = useMemo(() => {
    const allowed = new Set(myClassIds.map(Number))
    return studentsData.filter((s) => s.class_id != null && allowed.has(Number(s.class_id)))
  }, [studentsData, myClassIds])

  const filteredStudents = useMemo(() => {
    if (!selectedClassId) return scopedStudents
    const cid = Number(selectedClassId)
    return scopedStudents.filter((s) => Number(s.class_id) === cid)
  }, [scopedStudents, selectedClassId])

  const analytics = useMemo(() => {
    if (!filteredStudents || filteredStudents.length === 0) {
      return {
        overallAtt: 0, overallGrd: 0, bestClass: '—', worstClass: '—',
        attTrend: [], gradeTrend: [], atRiskStudents: [], processedStudents: [],
      }
    }

    let totalPresent = 0
    let totalAttRecords = 0
    let totalPctSum = 0
    let totalGradeCount = 0
    const statsByClass = {}

    const processedStudents = filteredStudents.map((s) => {
      totalPresent += s.present_att || 0
      totalAttRecords += s.total_att || 0
      totalPctSum += s.total_grade_pct || 0
      totalGradeCount += s.grade_count || 0

      const cId = s.class_id
      if (cId) {
        if (!statsByClass[cId]) {
          statsByClass[cId] = {
            id: cId,
            name: s.class_name || `Class ${cId}`,
            attSum: 0,
            attCount: 0,
            grdSum: 0,
            grdCount: 0,
          }
        }
        if (s.attendance_pct != null) {
          statsByClass[cId].attSum += s.attendance_pct
          statsByClass[cId].attCount++
        }
        if (s.avg_grade != null) {
          statsByClass[cId].grdSum += s.avg_grade
          statsByClass[cId].grdCount++
        }
      }

      return {
        ...s,
        school_class_display: s.class_name,
        attendancePct: s.attendance_pct,
        avgGrade: s.avg_grade,
        isRiskAtt: s.attendance_pct != null && s.attendance_pct < 60,
        isRiskGrd: s.avg_grade != null && s.avg_grade < 50,
      }
    })

    const classStatsArray = Object.values(statsByClass).map((cs) => ({
      ...cs,
      avgAtt: cs.attCount > 0 ? cs.attSum / cs.attCount : 0,
      avgGrd: cs.grdCount > 0 ? cs.grdSum / cs.grdCount : 0,
    }))

    const sortedClassesByGrd = [...classStatsArray].sort((a, b) => b.avgGrd - a.avgGrd)
    const bestClass = sortedClassesByGrd[0]
    const worstClass = sortedClassesByGrd[sortedClassesByGrd.length - 1]

    let attTrend = []
    if (dashboardData?.weekly_attendance) {
      attTrend = dashboardData.weekly_attendance.map((item) => {
        const present = item.present ?? 0
        const absent = item.absent ?? 0
        const total = present + absent
        return {
          date: item.name,
          rate: total > 0 ? Math.round((present / total) * 100) : 0,
        }
      })
    }

    const gradeTrend = classStatsArray.map((c) => ({
      name: c.name,
      avg: Math.round(c.avgGrd),
    }))

    const atRiskStudents = processedStudents.filter((s) => s.isRiskAtt || s.isRiskGrd)

    return {
      overallAtt: dashboardData?.attendance_rate ?? (totalAttRecords > 0 ? (totalPresent / totalAttRecords) * 100 : 0),
      overallGrd: dashboardData?.avg_score ?? (totalGradeCount > 0 ? (totalPctSum / totalGradeCount) : 0),
      bestClass: bestClass?.name || '—',
      worstClass: worstClass?.name || '—',
      attTrend,
      gradeTrend,
      atRiskStudents,
      processedStudents,
      classStatsArray,
    }
  }, [filteredStudents, dashboardData])

  const classStatsFromDashboard = useMemo(() => {
    const stats = dashboardData?.class_stats ?? []
    if (!selectedClassId) return stats
    return stats.filter((c) => String(c.id) === String(selectedClassId))
  }, [dashboardData, selectedClassId])

  async function generateReport() {
    setGenerating(true)
    setError('')
    try {
      const res = await apiFetch('/weekly-reports/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scope: 'TEACHER', write_pdf: true }),
      })
      const json = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(json.detail || json.message || `Generate failed (${res.status})`)
      }
      setGeneratedReport(json)
      setShowReportModal(true)
    } catch (err) {
      setError(err.message || 'Could not generate weekly report.')
    } finally {
      setGenerating(false)
    }
  }

  const insights = useMemo(() => {
    const list = []
    const scopeLabel = selectedClassId
      ? myClassObjects.find((c) => String(c.id) === String(selectedClassId))?.name || 'this class'
      : 'your assigned classes'
    if (analytics.overallAtt < 80) {
      list.push(`Attendance in ${scopeLabel} has dropped below 80% this week. Monitor closely.`)
    }
    if (analytics.atRiskStudents.length > 0) {
      list.push(`${analytics.atRiskStudents.length} of your students in ${scopeLabel} are currently marked "At Risk".`)
    }
    if (analytics.bestClass !== '—') {
      list.push(`Excellent performance from ${analytics.bestClass} this week!`)
    }
    if (analytics.worstClass !== '—' && analytics.worstClass !== analytics.bestClass) {
      list.push(`Consider revising recent materials for ${analytics.worstClass} as their average scores are the lowest.`)
    }
    if (list.length === 0) list.push('All metrics for your assigned classes are looking steady this week.')
    return list
  }, [analytics, selectedClassId, myClassObjects])

  const recommendations = useMemo(() => {
    const list = []
    if (analytics.atRiskStudents.length > 0) {
      list.push('Schedule parent-teacher meetings for At-Risk students.')
      list.push('Assign extra remedial homework for struggling individuals.')
    } else {
      list.push('Acknowledge outstanding performance in the upcoming classes.')
      list.push('Prepare advanced materials for top-performing classes.')
    }
    return list
  }, [analytics])

  if (profileLoading || loading) return <div style={{ padding: '2rem' }}><p className="muted">Loading your class analytics...</p></div>
  if (profileError) return <div style={{ padding: '2rem' }}><p style={{ color: 'red' }}>{profileError}</p></div>

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <PageHeader
          title="My Classes — Weekly Reports"
          subtitle="Analytics for your assigned classes only. School-wide reports are available to administrators."
        />
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {myClassObjects.length > 0 && (
            <select
              className="input"
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              style={{ minWidth: '200px' }}
            >
              <option value="">All my classes ({myClassObjects.length})</option>
              {myClassObjects.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          )}
          <button
            className="btn btn-primary"
            onClick={generateReport}
            disabled={generating || myClassObjects.length === 0}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            {generating ? 'Generating...' : '📄 Generate My Weekly Report'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', background: '#fef2f2', color: '#991b1b', borderRadius: '8px' }}>
          {error}
        </div>
      )}

      {myClassObjects.length === 0 ? (
        <Card>
          <p className="muted" style={{ padding: '2rem', textAlign: 'center', margin: 0 }}>
            No classes are assigned to you yet. Contact an administrator to assign classes before viewing weekly reports.
          </p>
        </Card>
      ) : (
        <>
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
            <Card style={{ padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', whiteSpace: 'nowrap' }}>
              <span style={{ fontSize: 'clamp(0.75rem, 1.5vw, 0.85rem)', color: '#6b7280', fontWeight: 500 }}>My Classes Attendance</span>
              <span style={{ fontSize: 'clamp(1.5rem, 3vw, 2rem)', fontWeight: 700, color: '#111827' }}>{formatPct(analytics.overallAtt)}</span>
            </Card>

            <Card style={{ padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', whiteSpace: 'nowrap' }}>
              <span style={{ fontSize: 'clamp(0.75rem, 1.5vw, 0.85rem)', color: '#6b7280', fontWeight: 500 }}>My Subjects Avg Grade</span>
              <span style={{ fontSize: 'clamp(1.5rem, 3vw, 2rem)', fontWeight: 700, color: '#111827' }}>{formatPct(analytics.overallGrd)}</span>
            </Card>

            <Card style={{ padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', whiteSpace: 'nowrap' }}>
              <span style={{ fontSize: 'clamp(0.75rem, 1.5vw, 0.85rem)', color: '#6b7280', fontWeight: 500 }}>Top Class</span>
              <span style={{ fontSize: 'clamp(0.85rem, 1.5vw, 0.95rem)', fontWeight: 700, color: '#16a34a', overflow: 'hidden', textOverflow: 'ellipsis' }}>&nbsp;{analytics.bestClass}</span>
            </Card>

            <Card style={{ padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', whiteSpace: 'nowrap' }}>
              <span style={{ fontSize: 'clamp(0.75rem, 1.5vw, 0.85rem)', color: '#6b7280', fontWeight: 500 }}>Needs Attention</span>
              <span style={{ fontSize: 'clamp(0.85rem, 1.5vw, 0.95rem)', fontWeight: 700, color: '#d97706', overflow: 'hidden', textOverflow: 'ellipsis' }}>&nbsp;{analytics.worstClass}</span>
            </Card>
          </div>

          {/* Per-class breakdown */}
          {classStatsFromDashboard.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
              {classStatsFromDashboard.map((cls) => (
                <Card key={cls.id} style={{ padding: '1rem 1.25rem' }}>
                  <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#111827' }}>{cls.name}</div>
                  <div style={{ fontSize: '0.85rem', color: '#6b7280', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <span>{cls.student_count} students</span>
                    <span>Attendance: {cls.attendance_rate != null ? formatPct(cls.attendance_rate) : '—'}</span>
                    <span>Avg grade: {cls.avg_grade != null ? formatPct(cls.avg_grade) : '—'}</span>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Trends */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <Card title="Attendance Trend — My Classes (This Week)">
              <div style={{ height: '400px', width: '100%', marginTop: '1rem' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analytics.attTrend} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eaeaea" />
                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} angle={-35} textAnchor="end" height={60} tickMargin={15} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} domain={[0, 100]} width={40} />
                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                    <Line type="monotone" dataKey="rate" stroke="#000" strokeWidth={3} dot={{ r: 4, fill: '#000', strokeWidth: 0 }} activeDot={{ r: 6 }} name="Attendance %" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card title="Average Grades by My Class">
              <div className="weekly-chart-scroll" style={{ marginTop: '1rem' }}>
                <div style={{ height: '400px', minWidth: analytics.gradeTrend.length > 8 ? analytics.gradeTrend.length * 70 : '100%', width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics.gradeTrend} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eaeaea" />
                      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#6b7280' }} angle={-40} textAnchor="end" height={80} tickMargin={20} interval={0} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} domain={[0, 100]} width={40} />
                      <Tooltip cursor={{ fill: '#f4f4f5' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                      <Bar dataKey="avg" fill="#111827" radius={[4, 4, 0, 0]} name="Avg Grade %" maxBarSize={48} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </Card>
          </div>

          {/* Insights */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <Card title="✨ Insights — My Classes">
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                {insights.map((ins, i) => (
                  <li key={i} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                    <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '24px', height: '24px', background: '#f3e8ff', color: '#9333ea', borderRadius: '50%', fontSize: '0.85rem', flexShrink: 0 }}>✦</span>
                    <span style={{ fontSize: '0.95rem', color: '#374151', lineHeight: 1.5 }}>{ins}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card title="📋 Recommendations">
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                {recommendations.map((rec, i) => (
                  <li key={i} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                    <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '24px', height: '24px', background: '#e0f2fe', color: '#0284c7', borderRadius: '50%', fontSize: '0.85rem', flexShrink: 0 }}>→</span>
                    <span style={{ fontSize: '0.95rem', color: '#374151', lineHeight: 1.5 }}>{rec}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>

          {/* At Risk */}
          <Card title={`Students At Risk — My Classes (${analytics.atRiskStudents.length})`}>
            {analytics.atRiskStudents.length === 0 ? (
              <div style={{ padding: '3rem 1rem', textAlign: 'center', color: '#6b7280' }}>
                🎉 Great job! No students in your assigned classes are currently marked at risk.
              </div>
            ) : (
              <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
                <table className="feature-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #eaeaea' }}>
                      <th style={{ padding: '1rem', textAlign: 'left', color: '#6b7280', fontWeight: 500, fontSize: '0.85rem' }}>Student</th>
                      <th style={{ padding: '1rem', textAlign: 'left', color: '#6b7280', fontWeight: 500, fontSize: '0.85rem' }}>Class</th>
                      <th style={{ padding: '1rem', textAlign: 'left', color: '#6b7280', fontWeight: 500, fontSize: '0.85rem' }}>Attendance</th>
                      <th style={{ padding: '1rem', textAlign: 'left', color: '#6b7280', fontWeight: 500, fontSize: '0.85rem' }}>Avg Grade</th>
                      <th style={{ padding: '1rem', textAlign: 'left', color: '#6b7280', fontWeight: 500, fontSize: '0.85rem' }}>Alert</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.atRiskStudents.map((s) => (
                      <tr key={s.id} style={{ borderBottom: '1px solid #f4f4f5' }}>
                        <td style={{ padding: '1rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            {s.photo_url ? (
                              <img src={s.photo_url} alt="" style={{ width: '36px', height: '36px', borderRadius: '50%', objectFit: 'cover' }} />
                            ) : (
                              <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: '#eaeaea', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>👤</div>
                            )}
                            <div>
                              <div style={{ fontWeight: 600, color: '#111827', fontSize: '0.9rem' }}>{s.name}</div>
                              <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{s.student_id}</div>
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: '1rem', fontSize: '0.9rem', color: '#374151' }}>{s.school_class_display || '—'}</td>
                        <td style={{ padding: '1rem', fontSize: '0.9rem', fontWeight: 600, color: s.isRiskAtt ? '#dc2626' : '#111827' }}>{formatPct(s.attendancePct)}</td>
                        <td style={{ padding: '1rem', fontSize: '0.9rem', fontWeight: 600, color: s.isRiskGrd ? '#d97706' : '#111827' }}>{formatPct(s.avgGrade)}</td>
                        <td style={{ padding: '1rem' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', alignItems: 'flex-start' }}>
                            {s.isRiskAtt && <span style={{ background: '#fee2e2', color: '#991b1b', padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600, border: '1px solid #fecaca' }}>At Risk: Attendance</span>}
                            {s.isRiskGrd && <span style={{ background: '#fef3c7', color: '#b45309', padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600, border: '1px solid #fde68a' }}>Warning: Grades</span>}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}

      {showReportModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ background: '#fff', borderRadius: '16px', width: 'min(700px, 100%)', maxHeight: '90vh', overflowY: 'auto', padding: '2.5rem', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', borderBottom: '1px solid #eaeaea', paddingBottom: '1rem' }}>
              <div>
                <h2 style={{ margin: '0 0 0.25rem 0', fontSize: '1.5rem', color: '#111827' }}>My Classes — Weekly Report</h2>
                <p style={{ margin: 0, color: '#6b7280', fontSize: '0.9rem' }}>
                  {generatedReport?.week_start ? `${generatedReport.week_start} → ${generatedReport.week_end}` : `Generated on ${new Date().toLocaleDateString()}`}
                </p>
              </div>
              <button className="btn btn-ghost" onClick={() => setShowReportModal(false)}>✕ Close</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <p style={{ fontSize: '1rem', color: '#374151', lineHeight: 1.6, margin: 0 }}>
                This report covers <strong>your assigned classes only</strong>. Overall attendance was <strong>{formatPct(analytics.overallAtt)}</strong> and average grade in your subjects was <strong>{formatPct(analytics.overallGrd)}</strong>.
              </p>

              <div>
                <h3 style={{ fontSize: '1.1rem', margin: '0 0 0.75rem 0', color: '#111827' }}>Class Highlights</h3>
                <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#374151', lineHeight: 1.6 }}>
                  <li><strong>Highest Performance:</strong> {analytics.bestClass}</li>
                  <li><strong>Requires Attention:</strong> {analytics.worstClass}</li>
                </ul>
              </div>

              <div>
                <h3 style={{ fontSize: '1.1rem', margin: '0 0 0.75rem 0', color: '#111827' }}>Action Required</h3>
                <p style={{ margin: '0 0 0.5rem 0', color: '#374151', lineHeight: 1.6 }}>
                  There are <strong>{analytics.atRiskStudents.length}</strong> students in your classes marked as "At Risk".
                </p>
              </div>
            </div>

            <div style={{ marginTop: '2.5rem', display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setShowReportModal(false)}>Close</button>
              {generatedReport?.pdf_url && (
                <a className="btn btn-primary" href={generatedReport.pdf_url} target="_blank" rel="noreferrer">Download PDF</a>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
