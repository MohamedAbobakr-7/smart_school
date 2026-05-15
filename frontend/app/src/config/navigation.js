/**
 * Sidebar items per backend role (ADMIN, TEACHER, STUDENT, PARENT).
 * Paths are absolute for React Router.
 */
export const NAV_BY_ROLE = {
  ADMIN: [
    { to: '/admin', label: 'Overview', end: true },
    { to: '/admin/users', label: 'Users' },
    { to: '/admin/students', label: 'Students' },
    { to: '/admin/teachers', label: 'Teachers' },
    { to: '/admin/parents', label: 'Parents' },
    { to: '/admin/subjects', label: 'Subjects' },
    { to: '/admin/classes', label: 'Classes' },
    { to: '/admin/attendance', label: 'Attendance' },
    { to: '/admin/exams', label: 'Assessments & Grades' },
    { to: '/admin/weekly-reports', label: 'Weekly reports' },
    { to: '/admin/notifications', label: 'Notifications' },
    { to: '/admin/profile', label: 'My Profile' },
  ],
  TEACHER: [
    { to: '/teacher', label: 'Overview', end: true },
    { to: '/teacher/students', label: 'Students' },
    { to: '/teacher/subjects', label: 'Subjects' },
    { to: '/teacher/attendance', label: 'Attendance' },
    { to: '/teacher/exams', label: 'Assessments & Grades' },
    { to: '/teacher/videos', label: 'Videos' },
    { to: '/teacher/materials', label: 'Materials' },
    { to: '/teacher/weekly-reports', label: 'Weekly reports' },
    { to: '/teacher/notifications', label: 'Notifications' },
    { to: '/teacher/profile', label: 'My Profile' },
  ],
  STUDENT: [
    { to: '/student', label: 'Overview', end: true },
    { to: '/student/subjects', label: 'Subjects' },
    { to: '/student/grades', label: 'Grades' },
    { to: '/student/attendance', label: 'Attendance' },
    { to: '/student/videos', label: 'Videos' },
    { to: '/student/materials', label: 'Materials' },
    { to: '/student/weekly-reports', label: 'Weekly reports' },
    { to: '/student/notifications', label: 'Notifications' },
    { to: '/student/profile', label: 'My Profile' },
  ],
  PARENT: [
    { to: '/parent', label: 'Overview', end: true },
    { to: '/parent/children', label: 'Children' },
    { to: '/parent/attendance', label: 'Attendance' },
    { to: '/parent/grades', label: 'Grades' },
    { to: '/parent/weekly-reports', label: 'Weekly reports' },
    { to: '/parent/notifications', label: 'Notifications' },
    { to: '/parent/profile', label: 'My Profile' },
  ],
}

export function navItemsForRole(role) {
  return NAV_BY_ROLE[role] ?? []
}
