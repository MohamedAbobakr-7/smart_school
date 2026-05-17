import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { RequireRole } from './components/auth/RequireRole'
import { RootRedirect } from './components/auth/RootRedirect'
import { DashboardLayout } from './components/layout/DashboardLayout'
import { AdminDashboard } from './pages/admin/AdminDashboard'
import { AdminStudentsPage } from './pages/admin/AdminStudentsPage'
import { AdminTeachersPage } from './pages/admin/AdminTeachersPage'
import { AdminParentsPage } from './pages/admin/AdminParentsPage'
import { AdminSubjectsPage } from './pages/admin/AdminSubjectsPage'
import { AdminExamsPage } from './pages/admin/AdminExamsPage'
import { AdminClassesPage } from './pages/admin/AdminClassesPage'
import { AdminUsersPage } from './pages/admin/AdminUsersPage'
import { AdminWeeklyReportsPage } from './pages/admin/AdminWeeklyReportsPage'
import { FeatureModulePage } from './pages/FeatureModulePage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { ProfilePage } from './pages/ProfilePage'
import { ParentDashboard } from './pages/parent/ParentDashboard'
import { ParentAttendancePage } from './pages/parent/ParentAttendancePage'
import { ParentChildrenPage } from './pages/parent/ParentChildrenPage'
import { ParentGradesPage } from './pages/parent/ParentGradesPage'
import { ParentWeeklyReportsPage } from './pages/parent/ParentWeeklyReportsPage'
import { StudentAttendancePage } from './pages/student/StudentAttendancePage'
import { StudentDashboard } from './pages/student/StudentDashboard'
import { StudentGradesPage } from './pages/student/StudentGradesPage'
import { StudentWeeklyReportsPage } from './pages/student/StudentWeeklyReportsPage'
import { StudentVideosPage } from './pages/student/StudentVideosPage'
import { StudentMaterialsPage } from './pages/student/StudentMaterialsPage'
import { StudentSubjectsPage } from './pages/student/StudentSubjectsPage'
import { TeacherDashboard } from './pages/teacher/TeacherDashboard'
import { TeacherExamsPage } from './pages/teacher/TeacherExamsPage'
import { TeacherStudentsPage } from './pages/teacher/TeacherStudentsPage'
import { TeacherSubjectsPage } from './pages/teacher/TeacherSubjectsPage'
import { TeacherVideosPage } from './pages/teacher/TeacherVideosPage'
import { TeacherMaterialsPage } from './pages/teacher/TeacherMaterialsPage'
import { TeacherWeeklyReportsPage } from './pages/teacher/TeacherWeeklyReportsPage'
import { SessionHistoryPage } from './pages/attendance/SessionHistoryPage'
import { UnauthorizedPage } from './pages/UnauthorizedPage'
import { getFeatureModule } from './config/featureModules'

const ADMIN_SECTIONS = [
  'users',
  'students',
  'teachers',
  'parents',
  'subjects',
  'classes',
  'attendance',
  'exams',
  'weekly-reports',
  'notifications',
  'profile',
]

const TEACHER_SECTIONS = ['students', 'subjects', 'attendance', 'exams', 'videos', 'materials', 'weekly-reports', 'notifications', 'profile']

const STUDENT_SECTIONS = ['subjects', 'grades', 'attendance', 'videos', 'materials', 'weekly-reports', 'notifications', 'profile']

const PARENT_SECTIONS = ['children', 'attendance', 'grades', 'weekly-reports', 'notifications', 'profile']

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route path="/" element={<RootRedirect />} />

        <Route
          path="/admin"
          element={
            <RequireRole roles={['ADMIN']}>
              <DashboardLayout />
            </RequireRole>
          }
        >
          <Route index element={<AdminDashboard />} />
          {ADMIN_SECTIONS.map((path) => {
            if (path === 'users') {
              return <Route key={path} path={path} element={<AdminUsersPage />} />
            }
            if (path === 'students') {
              return <Route key={path} path={path} element={<AdminStudentsPage />} />
            }
            if (path === 'teachers') {
              return <Route key={path} path={path} element={<AdminTeachersPage />} />
            }
            if (path === 'parents') {
              return <Route key={path} path={path} element={<AdminParentsPage />} />
            }
            if (path === 'subjects') {
              return <Route key={path} path={path} element={<AdminSubjectsPage />} />
            }
            if (path === 'attendance') {
              return <Route key={path} path={path} element={<SessionHistoryPage title="Attendance History" />} />
            }
            if (path === 'exams') {
              return <Route key={path} path={path} element={<AdminExamsPage />} />
            }
            if (path === 'classes') {
              return <Route key={path} path={path} element={<AdminClassesPage />} />
            }
            if (path === 'weekly-reports') {
              return <Route key={path} path={path} element={<AdminWeeklyReportsPage />} />
            }
            if (path === 'notifications') {
              return <Route key={path} path={path} element={<NotificationsPage />} />
            }
            if (path === 'profile') {
              return <Route key={path} path={path} element={<ProfilePage />} />
            }
            const module = getFeatureModule('ADMIN', path)
            return (
              <Route
                key={path}
                path={path}
                element={
                  <FeatureModulePage
                    title={module?.title || path}
                    endpoint={module?.endpoint || '/'}
                    description={module?.description}
                    hints={module?.hints}
                    actions={module?.actions}
                    enableCameraScan={module?.enableCameraScan}
                  />
                }
              />
            )
          })}
          <Route path="attendance/:sessionId" element={<SessionHistoryPage title="Attendance History" />} />
        </Route>

        <Route
          path="/teacher"
          element={
            <RequireRole roles={['TEACHER']}>
              <DashboardLayout />
            </RequireRole>
          }
        >
          <Route index element={<TeacherDashboard />} />
          {TEACHER_SECTIONS.map((path) => {
            if (path === 'students') {
              return <Route key={path} path={path} element={<TeacherStudentsPage />} />
            }
            if (path === 'subjects') {
              return <Route key={path} path={path} element={<TeacherSubjectsPage />} />
            }
            if (path === 'exams') {
              return <Route key={path} path={path} element={<TeacherExamsPage />} />
            }
            if (path === 'videos') {
              return <Route key={path} path={path} element={<TeacherVideosPage />} />
            }
            if (path === 'materials') {
              return <Route key={path} path={path} element={<TeacherMaterialsPage />} />
            }
            if (path === 'weekly-reports') {
              return <Route key={path} path={path} element={<TeacherWeeklyReportsPage />} />
            }
            if (path === 'notifications') {
              return <Route key={path} path={path} element={<NotificationsPage />} />
            }
            if (path === 'profile') {
              return <Route key={path} path={path} element={<ProfilePage />} />
            }
            const module = getFeatureModule('TEACHER', path)
            return (
              <Route
                key={path}
                path={path}
                element={
                  <FeatureModulePage
                    title={module?.title || path}
                    endpoint={module?.endpoint || '/'}
                    description={module?.description}
                    hints={module?.hints}
                    actions={module?.actions}
                    enableCameraScan={module?.enableCameraScan}
                  />
                }
              />
            )
          })}
          <Route path="attendance/session-history" element={<SessionHistoryPage />} />
          <Route path="attendance/session-history/:sessionId" element={<SessionHistoryPage />} />
        </Route>

        <Route
          path="/student"
          element={
            <RequireRole roles={['STUDENT']}>
              <DashboardLayout />
            </RequireRole>
          }
        >
          <Route index element={<StudentDashboard />} />
          {STUDENT_SECTIONS.map((path) => {
            if (path === 'subjects') {
              return <Route key={path} path={path} element={<StudentSubjectsPage />} />
            }
            if (path === 'grades') {
              return <Route key={path} path={path} element={<StudentGradesPage />} />
            }
            if (path === 'attendance') {
              return <Route key={path} path={path} element={<StudentAttendancePage />} />
            }
            if (path === 'videos') {
              return <Route key={path} path={path} element={<StudentVideosPage />} />
            }
            if (path === 'materials') {
              return <Route key={path} path={path} element={<StudentMaterialsPage />} />
            }
            if (path === 'weekly-reports') {
              return <Route key={path} path={path} element={<StudentWeeklyReportsPage />} />
            }
            if (path === 'notifications') {
              return <Route key={path} path={path} element={<NotificationsPage />} />
            }
            if (path === 'profile') {
              return <Route key={path} path={path} element={<ProfilePage />} />
            }
            const module = getFeatureModule('STUDENT', path)
            return (
              <Route
                key={path}
                path={path}
                element={
                  <FeatureModulePage
                    title={module?.title || path}
                    endpoint={module?.endpoint || '/'}
                    description={module?.description}
                    hints={module?.hints}
                    actions={module?.actions}
                    enableCameraScan={module?.enableCameraScan}
                  />
                }
              />
            )
          })}
        </Route>

        <Route
          path="/parent"
          element={
            <RequireRole roles={['PARENT']}>
              <DashboardLayout />
            </RequireRole>
          }
        >
          <Route index element={<ParentDashboard />} />
          {PARENT_SECTIONS.map((path) => {
            if (path === 'children') {
              return <Route key={path} path={path} element={<ParentChildrenPage />} />
            }
            if (path === 'attendance') {
              return <Route key={path} path={path} element={<ParentAttendancePage />} />
            }
            if (path === 'grades') {
              return <Route key={path} path={path} element={<ParentGradesPage />} />
            }
            if (path === 'weekly-reports') {
              return <Route key={path} path={path} element={<ParentWeeklyReportsPage />} />
            }
            if (path === 'notifications') {
              return <Route key={path} path={path} element={<NotificationsPage />} />
            }
            if (path === 'profile') {
              return <Route key={path} path={path} element={<ProfilePage />} />
            }
            const module = getFeatureModule('PARENT', path)
            return (
              <Route
                key={path}
                path={path}
                element={
                  <FeatureModulePage
                    title={module?.title || path}
                    endpoint={module?.endpoint || '/'}
                    description={module?.description}
                    hints={module?.hints}
                    actions={module?.actions}
                    enableCameraScan={module?.enableCameraScan}
                  />
                }
              />
            )
          })}
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
