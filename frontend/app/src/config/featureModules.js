export const FEATURE_MODULES = {
  ADMIN: {
    users: {
      title: 'Users',
      endpoint: '/users/',
      description: 'User management + role-based filtering.',
      hints: ['GET /api/users/', 'GET /api/users/me/', 'GET /api/users/by_role/?role=TEACHER'],
    },
    students: { title: 'Students', endpoint: '/students/', hints: ['GET/POST /api/students/'] },
    teachers: { title: 'Teachers', endpoint: '/teachers/', hints: ['GET/POST /api/teachers/'] },
    parents: { title: 'Parents', endpoint: '/parents/', hints: ['GET/POST /api/parents/'] },
    subjects: { title: 'Subjects', endpoint: '/subjects/', hints: ['GET/POST /api/subjects/'] },
    attendance: {
      title: 'Attendance History',
      endpoint: '/attendance-sessions/',
      hints: ['GET /api/attendance-sessions/', 'GET /api/attendance-sessions/class-history/'],
      actions: [{ label: 'Load Attendance Records', endpoint: '/attendance/' }],
    },
    exams: { title: 'Assessments & Grades', endpoint: '/exams/', hints: ['GET /api/exams/', 'GET /api/grades/'] },
    'weekly-reports': {
      title: 'Weekly Reports',
      endpoint: '/weekly-reports/dashboard/?weeks=8',
      hints: ['GET /api/weekly-reports/dashboard/?weeks=8', 'GET /api/weekly-reports/'],
      actions: [{ label: 'Load Weekly Reports List', endpoint: '/weekly-reports/' }],
    },
    videos: { title: 'Videos', endpoint: '/videos/', hints: ['GET /api/videos/'] },
    notifications: {
      title: 'Notifications',
      endpoint: '/notifications/?unread=true',
      hints: ['GET /api/notifications/?unread=true', 'GET /api/notification-preferences/'],
      actions: [
        { label: 'Load Preferences', endpoint: '/notification-preferences/' },
        { label: 'Mark All Read', endpoint: '/notifications/mark-all-read/', method: 'POST', body: {} },
      ],
    },
  },
  TEACHER: {
    students: { title: 'Students', endpoint: '/students/', hints: ['GET /api/students/'] },
    subjects: { title: 'Subjects', endpoint: '/subjects/', hints: ['GET /api/subjects/'] },
    attendance: {
      title: 'Attendance',
      endpoint: '/attendance-sessions/',
      hints: ['GET /api/attendance-sessions/', 'POST /api/attendance/process-classroom-image/'],
      enableCameraScan: true,
      actions: [{ label: 'Load Attendance Records', endpoint: '/attendance/' }],
    },
    exams: { title: 'Assessments & Grades', endpoint: '/exams/', hints: ['GET /api/exams/', 'GET /api/grades/'] },
    videos: {
      title: 'Videos',
      endpoint: '/videos/',
      hints: ['GET /api/videos/', 'GET /api/video-progress/?video=<id>'],
      actions: [{ label: 'Load Video Progress', endpoint: '/video-progress/' }],
    },
    'weekly-reports': {
      title: 'Weekly Reports',
      endpoint: '/weekly-reports/dashboard/?weeks=8',
      hints: ['GET /api/weekly-reports/dashboard/?weeks=8'],
      actions: [{ label: 'Load Weekly Reports List', endpoint: '/weekly-reports/' }],
    },
    notifications: {
      title: 'Notifications',
      endpoint: '/notifications/?unread=true',
      hints: ['GET /api/notifications/', 'GET /api/notification-preferences/'],
      actions: [
        { label: 'Load Preferences', endpoint: '/notification-preferences/' },
        { label: 'Mark All Read', endpoint: '/notifications/mark-all-read/', method: 'POST', body: {} },
      ],
    },
  },
  STUDENT: {
    grades: { title: 'Grades', endpoint: '/grades/', hints: ['GET /api/grades/'] },
    attendance: { title: 'Attendance', endpoint: '/attendance/', hints: ['GET /api/attendance/'] },
    videos: {
      title: 'Videos',
      endpoint: '/videos/',
      hints: ['GET /api/videos/', 'GET /api/video-progress/', 'POST /api/video-progress/sync/'],
      actions: [{ label: 'Load My Progress', endpoint: '/video-progress/' }],
    },
    reports: { title: 'Reports', endpoint: '/reports/', hints: ['GET /api/reports/'] },
    notifications: {
      title: 'Notifications',
      endpoint: '/notifications/?unread=true',
      hints: ['GET /api/notifications/', 'GET/PATCH /api/notification-preferences/'],
      actions: [
        { label: 'Load Preferences', endpoint: '/notification-preferences/' },
        { label: 'Mark All Read', endpoint: '/notifications/mark-all-read/', method: 'POST', body: {} },
      ],
    },
  },
  PARENT: {
    children: { title: 'Children', endpoint: '/students/', hints: ['GET /api/students/'] },
    attendance: { title: 'Attendance', endpoint: '/attendance/', hints: ['GET /api/attendance/'] },
    grades: { title: 'Grades', endpoint: '/grades/', hints: ['GET /api/grades/'] },
    notifications: {
      title: 'Notifications',
      endpoint: '/notifications/?unread=true',
      hints: ['GET /api/notifications/', 'GET/PATCH /api/notification-preferences/'],
      actions: [
        { label: 'Load Preferences', endpoint: '/notification-preferences/' },
        { label: 'Mark All Read', endpoint: '/notifications/mark-all-read/', method: 'POST', body: {} },
      ],
    },
  },
}

export function getFeatureModule(role, slug) {
  return FEATURE_MODULES[role]?.[slug] || null
}
