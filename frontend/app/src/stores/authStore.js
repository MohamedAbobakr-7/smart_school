import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { STORAGE_KEY as LANG_STORAGE_KEY } from '../i18n'

const ROLE_HOME = {
  ADMIN: '/admin',
  TEACHER: '/teacher',
  STUDENT: '/student',
  PARENT: '/parent',
}

export function homePathForRole(role) {
  return ROLE_HOME[role] || '/login'
}

/** Helper: read persisted language for API headers */
function getLang() {
  return localStorage.getItem(LANG_STORAGE_KEY) || 'en'
}

export const useAuthStore = create(
  persist(
    (set) => ({
      access: null,
      refresh: null,
      user: null,

      login: async (username, password) => {
        const res = await fetch('/api/auth/login/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            'Accept-Language': getLang(),
          },
          body: JSON.stringify({ username, password }),
        })
        const data = await res.json().catch(() => ({}))
        if (!res.ok) {
          const msg =
            typeof data.detail === 'string'
              ? data.detail
              : Array.isArray(data.detail)
                ? data.detail.map((e) => e.msg || e).join(', ')
                : 'Login failed'
          throw new Error(msg)
        }
        set({
          access: data.access,
          refresh: data.refresh,
          user: data.user ?? null,
        })
        return data.user
      },

      logout: () => set({ access: null, refresh: null, user: null }),

      /** Optional: replace tokens without clearing user */
      setTokens: (access, refresh) => set({ access, refresh }),
    }),
    {
      name: 'smart-school-auth',
      partialize: (s) => ({
        access: s.access,
        refresh: s.refresh,
        user: s.user,
      }),
    }
  )
)

export { ROLE_HOME }
