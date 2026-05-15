import { create } from 'zustand'

export const useThemeStore = create((set) => ({
  theme: localStorage.getItem('ss_theme') || 'light',
  toggleTheme: () => set((state) => {
    const next = state.theme === 'light' ? 'dark' : 'light'
    localStorage.setItem('ss_theme', next)
    if (next === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark')
    } else {
      document.documentElement.setAttribute('data-theme', 'light')
    }
    return { theme: next }
  }),
  initTheme: () => {
    const theme = localStorage.getItem('ss_theme') || 'light'
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark')
    } else {
      document.documentElement.setAttribute('data-theme', 'light')
    }
    set({ theme })
  }
}))
