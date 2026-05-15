import { useCallback, useEffect, useState, useMemo } from 'react'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch, apiFetchAll } from '../../lib/api'
import { useTeacherProfile } from '../../hooks/useTeacherProfile'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

const CATEGORIES = [
  { value: 'lecture', label: 'Lecture' },
  { value: 'tutorial', label: 'Tutorial' },
  { value: 'review', label: 'Review' },
  { value: 'lab', label: 'Lab / Demo' },
  { value: 'other', label: 'Other' },
]

export function TeacherVideosPage() {
  const { teacher: teacherProfile, mySubjectIds } = useTeacherProfile()
  const [allSubjects, setAllSubjects] = useState([])
  const [videos, setVideos] = useState([])
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [subject, setSubject] = useState('')
  const [category, setCategory] = useState('lecture')
  const [isPublished, setIsPublished] = useState(true)
  const [file, setFile] = useState(null)

  const subjects = useMemo(() => {
    if (mySubjectIds.length === 0) return []
    return allSubjects.filter((s) => mySubjectIds.includes(Number(s.id)))
  }, [allSubjects, mySubjectIds])

  const loadLists = useCallback(async () => {
    const [sRes, vRes] = await Promise.all([apiFetchAll('/subjects/'), apiFetch('/videos/')])
    setAllSubjects(sRes) // apiFetchAll returns the array directly
    if (vRes.ok) setVideos(parseList(await vRes.json()))
  }, [])

  useEffect(() => {
    loadLists()
  }, [loadLists])

  async function onSubmit(e) {
    e.preventDefault()
    setMsg('')
    if (!title.trim() || !subject) {
      setMsg('Title and subject are required.')
      return
    }
    if (!file) {
      setMsg('Choose a video file (mp4, webm, mov, …).')
      return
    }
    setBusy(true)
    try {
      const body = new FormData()
      body.append('title', title.trim())
      body.append('description', description.trim())
      body.append('subject', String(subject))
      body.append('category', category)
      body.append('is_published', isPublished ? 'True' : 'False')
      body.append('display_order', '0')
      body.append('video_file', file)

      const res = await apiFetch('/videos/', { method: 'POST', body })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const detail = data.detail || data.video_file || JSON.stringify(data)
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
      }
      setMsg(`Uploaded: “${data.title}” (id ${data.id}).`)
      setTitle('')
      setDescription('')
      setFile(null)
      await loadLists()
    } catch (err) {
      setMsg(err.message || 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Videos"
        subtitle="Upload lesson recordings. Allowed types: mp4, webm, mov, m4v, ogg."
      />

      {msg ? <p className="teaching-msg">{msg}</p> : null}

      <Card title="Upload video">
        <form className="teaching-form" onSubmit={onSubmit}>
          <label className="login-label" htmlFor="tv-title">
            Title
          </label>
          <input
            id="tv-title"
            className="login-input login-input--plain teaching-input-wide"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <label className="login-label" htmlFor="tv-desc">
            Description (optional)
          </label>
          <textarea
            id="tv-desc"
            className="teaching-textarea"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <label className="login-label" htmlFor="tv-subject">
            Subject
          </label>
          <select
            id="tv-subject"
            className="login-input login-input--plain teaching-input-wide"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
          >
            <option value="">Select subject…</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code ? `${s.code} — ` : ''}
                {s.name}
              </option>
            ))}
          </select>
          <label className="login-label" htmlFor="tv-cat">
            Category
          </label>
          <select
            id="tv-cat"
            className="login-input login-input--plain teaching-input-wide"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
          <label className="login-label flex-row teaching-check">
            <input type="checkbox" checked={isPublished} onChange={(e) => setIsPublished(e.target.checked)} />
            Published (visible to students)
          </label>
          <label className="login-label" htmlFor="tv-file">
            Video file
          </label>
          <input id="tv-file" type="file" accept=".mp4,.webm,.mov,.m4v,.ogg,video/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <div className="feature-actions">
            <button type="submit" className="btn btn-primary" disabled={busy}>
              Upload
            </button>
            <button type="button" className="btn btn-ghost" disabled={busy} onClick={loadLists}>
              Refresh list
            </button>
          </div>
        </form>
      </Card>

      <Card title="Your videos">
        {videos.length === 0 ? (
          <p className="muted">No videos yet.</p>
        ) : (
          <div className="teaching-table-wrap">
            <table className="feature-table teaching-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Subject</th>
                  <th>Category</th>
                  <th>Published</th>
                </tr>
              </thead>
              <tbody>
                {videos.slice(0, 30).map((v) => (
                  <tr key={v.id}>
                    <td>{v.title}</td>
                    <td>{v.subject_name || v.subject_code || v.subject}</td>
                    <td>{v.category}</td>
                    <td>{v.is_published ? 'Yes' : 'No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  )
}
