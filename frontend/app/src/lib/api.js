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
 * Fetch ALL pages of a paginated DRF list endpoint.
 * Automatically follows `next` links until exhausted.
 * Returns a plain array of all results.
 *
 * @param {string} path  - API path, e.g. '/users/'
 * @returns {Promise<Array>}
 */
export async function apiFetchAll(path) {
  const { access } = useAuthStore.getState()
  const authHeader = access ? { Authorization: `Bearer ${access}` } : {}

  // Build the absolute first-page URL
  const firstUrl = path.startsWith('http')
    ? path
    : `/api${path.startsWith('/') ? '' : '/'}${path}`

  let url = firstUrl
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
      // `next` is an absolute URL like http://localhost:8000/api/users/?page=2
      url = json.next || null
    } else {
      // Unexpected shape — return as-is
      all.push(json)
      break
    }
  }

  return all
}
