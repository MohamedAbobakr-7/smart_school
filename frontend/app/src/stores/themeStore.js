import { create } from 'zustand'

const THEME_KEY = 'ss_theme'
const VALID_THEMES = ['default', 'dark']

export const useThemeStore = create((set) => ({
  theme: localStorage.getItem(THEME_KEY) || 'default',

  setTheme: (next) => {
    if (!VALID_THEMES.includes(next)) next = 'default'
    localStorage.setItem(THEME_KEY, next)
    document.documentElement.setAttribute('data-theme', next)
    set({ theme: next })
  },

  initTheme: () => {
    const theme = localStorage.getItem(THEME_KEY) || 'default'
    if (!VALID_THEMES.includes(theme)) {
      theme = 'default'
      localStorage.setItem(THEME_KEY, theme)
    }
    document.documentElement.setAttribute('data-theme', theme)
    set({ theme })
  },
}))
