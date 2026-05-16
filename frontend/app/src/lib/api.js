import { useAuthStore } from '../stores/authStore'
import { STORAGE_KEY as LANG_STORAGE_KEY } from '../i18n'

/** Read persisted language for API headers */
function getLang() {
  return localStorage.getItem(LANG_STORAGE_KEY) || 'en'
}

/**
 * Fetch JSON from the API with Bearer token when logged in.
 * Automatically includes Accept-Language header from persisted preference.
 */
export async function apiFetch(path, options = {}) {
  const { access } = useAuthStore.getState()
  const headers = {
    Accept: 'application/json',
    'Accept-Language': getLang(),
    ...(options.headers || {}),
  }
  if (access && !headers.Authorization) {
    headers.Authorization = `Bearer ${access}`
  }
  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(options.body)
  }
  const res = await fetch(path.startsWith('http') ? path : `/api${path.startsWith('/') ? '' : '/'}${path}`, {
    ...options,
    headers,
  })
  return res
}

/**
 * Convert an absolute DRF pagination URL back to a relative proxy path.
 * DRF `next` links are absolute (e.g. http://127.0.0.1:8000/api/users/?page=2).
 * In dev the Vite proxy only intercepts /api/* paths, so fetching an absolute
 * URL directly from the browser bypasses the proxy and fails with a CORS error.
 * This helper strips the origin and returns just the pathname + search so the
 * request always goes through the proxy.
 */
function toProxyPath(url) {
  if (!url) return null
  try {
    const u = new URL(url)
    // Preserve the full path + query string, e.g. /api/users/?page=2
    return u.pathname + u.search
  } catch {
    // Not a valid absolute URL — assume it's already a relative path
    return url.startsWith('/') ? url : `/api/${url}`
  }
}

export async function apiFetchAll(path) {
  const { access } = useAuthStore.getState()
  const authHeader = access ? { Authorization: `Bearer ${access}` } : {}

  // Build the first-page URL as a relative proxy path
  const firstPath = path.startsWith('http') ? toProxyPath(path) : `/api${path.startsWith('/') ? '' : '/'}${path}`

  let url = firstPath
  const all = []

  while (url) {
    const res = await fetch(url, {
      headers: { Accept: 'application/json', 'Accept-Language': getLang(), ...authHeader },
    })
    if (!res.ok) {
      // Re-expose the raw response so callers can throw a meaningful error
      const err = new Error(`API error ${res.status} on ${url}`)
      err.status = res.status
      err.response = res
      throw err
    }
    const json = await res.json()
    if (Array.isArray(json)) {
      all.push(...json)
      break
    }
    if (json.results && Array.isArray(json.results)) {
      all.push(...json.results)
      // Convert absolute `next` URL to a relative proxy path so subsequent
      // pages also go through the Vite proxy (avoids CORS failures).
      url = toProxyPath(json.next)
    } else {
      // Unexpected shape — return as-is
      all.push(json)
      break
    }
  }

  return all
}
