import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const STORAGE_KEY = 'ss_lang'

/** Read persisted language or default to 'en' */
function getSavedLanguage() {
  return localStorage.getItem(STORAGE_KEY) || 'en'
}

i18n.use(initReactI18next).init({
  resources: {
    en: {
      translation: {
        // ──── Login page ────
        login: {
          asideTagline: 'Learning, attendance, and grades — one connected platform for your school community.',
          asideHeadline: 'Manage your school',
          wordmark: 'Smart School',
          help: 'Help',
          title: 'Sign In',
          usernameLabel: 'Username or student ID',
          usernamePlaceholder: 'Staff: username · Students: school ID',
          passwordLabel: 'Password',
          passwordPlaceholder: 'Enter your password',
          showPassword: 'Show password',
          hidePassword: 'Hide password',
          submitting: 'Signing in…',
          submit: 'Sign In',
          footerCopy: '© {{year}} Smart School',
          contactUs: 'Contact us',
          languageEn: 'English',
          languageAr: 'العربية',
        },
        // ──── General ────
        general: {
          loginFailed: 'Login failed',
        },
      },
    },
    ar: {
      translation: {
        // ──── Login page ────
        login: {
          asideTagline: 'التعلم، الحضور، والدرجات — منصة متكاملة لمجتمع مدرستكم.',
          asideHeadline: 'إدارة مدرستك',
          wordmark: 'المدرسة الذكية',
          help: 'المساعدة',
          title: 'تسجيل الدخول',
          usernameLabel: 'اسم المستخدم أو رقم الطالب',
          usernamePlaceholder: 'الموظفون: اسم المستخدم · الطلاب: الرقم المدرسي',
          passwordLabel: 'كلمة المرور',
          passwordPlaceholder: 'أدخل كلمة المرور',
          showPassword: 'إظهار كلمة المرور',
          hidePassword: 'إخفاء كلمة المرور',
          submitting: 'جارٍ تسجيل الدخول…',
          submit: 'تسجيل الدخول',
          footerCopy: '© {{year}} المدرسة الذكية',
          contactUs: 'اتصل بنا',
          languageEn: 'English',
          languageAr: 'العربية',
        },
        // ──── General ────
        general: {
          loginFailed: 'فشل تسجيل الدخول',
        },
      },
    },
  },
  lng: getSavedLanguage(),
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false, // React already escapes
  },
})

export default i18n
export { STORAGE_KEY }