import { useEffect, useRef, useState } from 'react'

import { apiFetch } from '../../lib/api'

function stopTracks(stream) {
  if (!stream) return
  for (const track of stream.getTracks()) track.stop()
}

function canvasToBlob(canvas) {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.9)
  })
}

function supportsFaceDetector() {
  return typeof window !== 'undefined' && 'FaceDetector' in window
}

/**
 * OpenCV in the browser loads a heavy WASM build and can freeze the tab for a long time.
 * We use the native FaceDetector API in Chromium (Chrome/Edge) instead — async and UI-safe.
 * Other browsers: camera + manual "Send frame" only.
 */
export function AttendanceCameraCapture({ sessionId, onResult }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const scanTimeoutRef = useRef(null)
  const scanTimerRef = useRef(null)
  const faceDetectorRef = useRef(null)
  const scanningRef = useRef(false)
  const frameBusyRef = useRef(false)
  const stableRef = useRef(0)

  const [running, setRunning] = useState(false)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('Choose a session from the table, then scan.')
  const [lastResult, setLastResult] = useState(null)
  const [faceApi, setFaceApi] = useState(supportsFaceDetector)

  useEffect(() => {
    setFaceApi(supportsFaceDetector())
  }, [])

  async function stopScan() {
    scanningRef.current = false
    frameBusyRef.current = false
    stableRef.current = 0
    setRunning(false)
    if (scanTimerRef.current) {
      clearTimeout(scanTimerRef.current)
      scanTimerRef.current = null
    }
    if (scanTimeoutRef.current) {
      clearTimeout(scanTimeoutRef.current)
      scanTimeoutRef.current = null
    }
    faceDetectorRef.current = null
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    stopTracks(streamRef.current)
    streamRef.current = null
  }

  async function captureAndSend() {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    const w = video.videoWidth || 640
    const h = video.videoHeight || 480
    if (w < 2 || h < 2) throw new Error('Camera not ready — wait a moment and try again.')

    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, w, h)
    const blob = await canvasToBlob(canvas)
    if (!blob) throw new Error('Could not capture image')

    const body = new FormData()
    body.append('session_id', sessionId.trim())
    body.append('image', blob, `attendance-${Date.now()}.jpg`)

    const res = await apiFetch('/attendance/process-classroom-image/', {
      method: 'POST',
      body,
    })
    const json = await res.json().catch(() => ({}))
    if (!res.ok) {
      const msg = json.message || json.detail || `Verification failed (${res.status})`
      const extra = json.error && json.error !== msg ? ` (${json.error})` : ''
      throw new Error(`${msg}${extra}`)
    }
    setLastResult(json)
    onResult?.(json)
    setStatus(
      `Done. Faces: ${json.num_faces_detected ?? 0}, Marked: ${json.num_attendance_marked ?? 0}`
    )
  }

  async function sendManual() {
    if (!String(sessionId || '').trim()) {
      setStatus('Select a session first.')
      return
    }
    setBusy(true)
    setStatus('Sending frame to server…')
    try {
      await captureAndSend()
    } catch (e) {
      setStatus(e.message || 'Send failed')
    } finally {
      setBusy(false)
    }
  }

  function scheduleNextFacePass(detector) {
    if (!scanningRef.current) return
    scanTimerRef.current = setTimeout(async () => {
      if (!scanningRef.current || frameBusyRef.current) {
        scheduleNextFacePass(detector)
        return
      }
      const video = videoRef.current
      if (!video || video.readyState < 2) {
        scheduleNextFacePass(detector)
        return
      }
      frameBusyRef.current = true
      try {
        const faces = await detector.detect(video)
        if (faces && faces.length > 0) {
          stableRef.current += 1
        } else {
          stableRef.current = 0
        }
        if (stableRef.current >= 3) {
          scanningRef.current = false
          setStatus('Face detected. Sending…')
          setBusy(true)
          try {
            await captureAndSend()
          } catch (e) {
            setStatus(e.message || 'Send failed')
          } finally {
            await stopScan()
            setBusy(false)
          }
          return
        }
      } catch {
        stableRef.current = 0
      } finally {
        frameBusyRef.current = false
        scheduleNextFacePass(detector)
      }
    }, 400)
  }

  async function startScan() {
    if (running || busy) return
    if (!String(sessionId || '').trim()) {
      setStatus('Select a session first.')
      return
    }
    setLastResult(null)
    setBusy(true)
    setStatus('Requesting camera access…')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      })
      streamRef.current = stream
      const video = videoRef.current
      video.srcObject = stream
      await video.play()
      setStatus('Camera on.')
      setRunning(true)
      setBusy(false)

      if (supportsFaceDetector()) {
        const detector = new window.FaceDetector({ fastMode: true, maxDetections: 4 })
        faceDetectorRef.current = detector
        scanningRef.current = true
        stableRef.current = 0
        setStatus('Scanning (browser face API) — hold still…')
        scanTimeoutRef.current = setTimeout(async () => {
          if (!scanningRef.current) return
          setStatus('No stable face in time. Use “Send frame” or try again with better light.')
          await stopScan()
        }, 25000)
        scheduleNextFacePass(detector)
      } else {
        setStatus(
          'This browser has no built-in face detector. Use “Send frame” to upload a snapshot, or use Chrome/Edge for auto-detect.'
        )
      }
    } catch (err) {
      await stopScan()
      setStatus(err?.message || 'Camera permission denied or unavailable.')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    return () => {
      stopScan()
    }
  }, [])

  return (
    <div className="attendance-scan">
      <p className="muted">Camera capture and upload to the attendance endpoint.</p>
      <p className="attendance-hint">
        Active session: <code>{sessionId || 'None'}</code>
      </p>
      {!faceApi ? (
        <p className="attendance-hint">Tip: use Chrome or Edge for automatic face-detected upload.</p>
      ) : null}

      <div className="feature-actions">
        <button
          type="button"
          className="btn btn-primary"
          disabled={busy || running || !String(sessionId || '').trim()}
          onClick={startScan}
        >
          Start scan
        </button>
        <button type="button" className="btn btn-ghost" disabled={busy || !running} onClick={stopScan}>
          Stop
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          disabled={busy || !String(sessionId || '').trim()}
          onClick={sendManual}
        >
          Send frame
        </button>
      </div>

      <p className="muted attendance-scan-status">{status}</p>

      <div className="attendance-video-wrap">
        <video ref={videoRef} className="attendance-video" autoPlay muted playsInline />
        <canvas ref={canvasRef} className="attendance-canvas" />
      </div>

      {lastResult ? (
        <p className="muted">
          Matches: <code>{String(lastResult.num_matches ?? 0)}</code> | Marked attendance:{' '}
          <code>{String(lastResult.num_attendance_marked ?? 0)}</code>
        </p>
      ) : null}
    </div>
  )
}
