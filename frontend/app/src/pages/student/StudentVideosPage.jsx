import { useEffect, useMemo, useState } from 'react'

import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { apiFetch } from '../../lib/api'
import { useAuthStore } from '../../stores/authStore'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

function streamUrlForVideo(videoId, accessToken) {
  if (!videoId || !accessToken) return ''
  return `/api/videos/${videoId}/stream/?access=${encodeURIComponent(accessToken)}`
}

export function StudentVideosPage() {
  const access = useAuthStore((s) => s.access)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [videos, setVideos] = useState([])
  const [activeVideo, setActiveVideo] = useState(null)

  useEffect(() => {
    let disposed = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const res = await apiFetch('/videos/')
        const json = await res.json().catch(() => [])
        if (!res.ok) throw new Error(json.detail || `Failed to load videos (${res.status})`)
        if (!disposed) setVideos(parseList(json))
      } catch (e) {
        if (!disposed) setError(e.message || 'Failed to load videos.')
      } finally {
        if (!disposed) setLoading(false)
      }
    })()
    return () => {
      disposed = true
    }
  }, [])

  const cards = useMemo(() => videos, [videos])

  function openVideo(video) {
    setActiveVideo(video)
  }

  function closeVideo() {
    setActiveVideo(null)
  }

  return (
    <>
      <PageHeader
        title="Videos"
        subtitle="Browse your educational videos by subject and play instantly."
      />

      {loading ? <p className="muted">Loading videos...</p> : null}
      {!loading && error ? <p className="teaching-error">{error}</p> : null}

      {!loading && !error ? (
        cards.length ? (
          <div className="grid-cards student-videos-grid">
            {cards.map((video) => (
              <Card key={video.id} className="student-video-card">
                <h3 className="student-video-title">{video.title || 'Untitled video'}</h3>
                <p className="student-video-subject">
                  Subject: <strong>{video.subject_name || video.subject_code || '—'}</strong>
                </p>
                <div className="feature-actions">
                  <button type="button" className="btn btn-primary btn-xs" onClick={() => openVideo(video)}>
                    Play
                  </button>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <div className="student-videos-empty">
            <p className="muted">No videos available yet.</p>
          </div>
        )
      ) : null}

      {activeVideo ? (
        <div className="video-modal-backdrop" role="dialog" aria-modal="true" aria-label="Video player">
          <div className="video-modal-card">
            <div className="video-modal-head">
              <div>
                <h3 className="video-modal-title">{activeVideo.title || 'Video'}</h3>
                <p className="video-modal-sub">
                  {activeVideo.subject_name || activeVideo.subject_code || 'Subject'}
                </p>
              </div>
              <button type="button" className="btn btn-ghost btn-xs" onClick={closeVideo}>
                Close
              </button>
            </div>
            <div className="video-modal-player-wrap">
              <video
                key={activeVideo.id}
                className="video-modal-player"
                controls
                autoPlay
                playsInline
                src={streamUrlForVideo(activeVideo.id, access)}
              />
            </div>
          </div>
        </div>
      ) : null}
    </>
  )
}
