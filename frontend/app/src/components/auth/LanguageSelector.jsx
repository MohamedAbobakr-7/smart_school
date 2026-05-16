import { useLangStore } from '../../stores/langStore'
import { useTranslation } from 'react-i18next'

/**
 * Minimal language toggle for the login page footer.
 * Renders as:  English  |  العربية
 * Clicking either word switches the language instantly.
 */
export function LanguageSelector() {
  const { t } = useTranslation()
  const lang = useLangStore((s) => s.lang)
  const setLang = useLangStore((s) => s.setLang)

  return (
    <span className="lang-selector">
      <button
        type="button"
        className={`lang-selector-btn${lang === 'en' ? ' is-active' : ''}`}
        onClick={() => setLang('en')}
        aria-label={t('login.languageEn')}
      >
        {t('login.languageEn')}
      </button>
      <span className="lang-selector-divider" aria-hidden="true">|</span>
      <button
        type="button"
        className={`lang-selector-btn${lang === 'ar' ? ' is-active' : ''}`}
        onClick={() => setLang('ar')}
        aria-label={t('login.languageAr')}
      >
        {t('login.languageAr')}
      </button>
    </span>
  )
}