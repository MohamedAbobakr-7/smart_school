import { create } from 'zustand'
import i18n, { STORAGE_KEY } from '../i18n'

/**
 * Language store — persists the selected language in localStorage,
 * syncs with i18next, and toggles the document direction (LTR / RTL).
 */
export const useLangStore = create((set, get) => ({
  lang: localStorage.getItem(STORAGE_KEY) || 'en',

  setLang: (lang) => {
    if (lang === get().lang) return
    localStorage.setItem(STORAGE_KEY, lang)
    i18n.changeLanguage(lang)
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr')
    document.documentElement.setAttribute('lang', lang)
    set({ lang })
  },

  /** Call once on app boot to sync DOM with persisted preference */
  initLang: () => {
    const lang = localStorage.getItem(STORAGE_KEY) || 'en'
    i18n.changeLanguage(lang)
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr')
    document.documentElement.setAttribute('lang', lang)
    set({ lang })
  },
}))