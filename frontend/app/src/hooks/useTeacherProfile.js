import { useEffect, useState } from 'react'
import { apiFetch } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

function parseList(payload) {
  if (Array.isArray(payload)) return payload
  if (payload?.results && Array.isArray(payload.results)) return payload.results
  return []
}

/**
 * Fetches the logged-in teacher's own profile from /api/teachers/.
 *
 * Returns:
 *   teacher          — the full teacher object (or null while loading)
 *   mySubjectIds     — number[] of assigned subject PKs
 *   myClassIds       — number[] of assigned class PKs
 *   myClassObjects   — { id, name }[] of assigned classes
 *   loading          — boolean
 *   error            — string | ''
 */
export function useTeacherProfile() {
  const user = useAuthStore((s) => s.user)
  const [teacher, setTeacher] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user?.id) return
    let cancelled = false

    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const res = await apiFetch('/teachers/')
        if (!res.ok) throw new Error(`Failed to load teacher profile (${res.status})`)
        const data = await res.json().catch(() => [])
        const list = parseList(data)
        const mine = list.find((t) => t.user === user.id) || null
        if (!cancelled) setTeacher(mine)
      } catch (e) {
        if (!cancelled) setError(e.message || 'Failed to load teacher profile.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [user?.id])

  const mySubjectIds = teacher?.subject_ids?.map(Number) ?? []

  // assigned_classes_display is [{ id, name, display_name, … }]
  const myClassObjects = (teacher?.assigned_classes_display ?? []).map((c) => ({
    id: Number(c.id),
    name: c.display_name || c.name || `Class #${c.id}`,
  }))

  const myClassIds = myClassObjects.map((c) => c.id)

  return { teacher, mySubjectIds, myClassIds, myClassObjects, loading, error }
}
