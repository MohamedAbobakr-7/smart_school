# User Manual

> End-user guide mapped to React routes in `frontend/app/src/App.jsx` and `config/navigation.js`.

---

## 1. Getting Started

### 1.1 Accessing the application

1. Open the web application URL (development: Vite dev server, typically port 5173).
2. API requests are proxied to Django at `http://127.0.0.1:8000`.
3. Ensure Django, SQL Server, and (for attendance) the Face Recognition service on port **8001** are running.

### 1.2 Signing in

**Screen:** `/login` (`LoginPage.jsx`)

| Field | Instructions |
|-------|----------------|
| Username or student ID | Staff: Django username. Students: school `student_id` (e.g. auto-generated ID). |
| Password | Account password set by administrator |

Use the language selector (English / العربية) before login; preference is stored and sent as `Accept-Language` on API calls.

After login you are redirected:

| Role | Home URL |
|------|----------|
| Admin | `/admin` |
| Teacher | `/teacher` |
| Student | `/student` |
| Parent | `/parent` |

### 1.3 Signing out

Use the logout control in the dashboard layout (clears JWT from browser storage).

### 1.4 Unauthorized access

Navigating to another role's URL shows `/unauthorized`.

---

## 2. Administrator Guide

**Base path:** `/admin`

| Menu item | Route | What you can do |
|-----------|-------|-----------------|
| Overview | `/admin` | School KPIs: students, teachers, classes, attendance rate, grades, charts |
| Users | `/admin/users` | Create/edit users and assign roles |
| Students | `/admin/students` | Manage students, photos, face registration, class/parent links |
| Teachers | `/admin/teachers` | Manage teachers, subjects, classes |
| Parents | `/admin/parents` | Manage parent accounts and link children |
| Subjects | `/admin/subjects` | CRUD subjects (bilingual names) |
| Classes | `/admin/classes` | CRUD class groups (name + section) |
| Attendance History | `/admin/attendance` | Browse sessions; drill into `/admin/attendance/:sessionId` |
| Assessments & Grades | `/admin/exams` | Manage exams, questions, grades |
| Weekly reports | `/admin/weekly-reports` | View/generate school weekly analytics and PDFs |
| Notifications | `/admin/notifications` | View alerts; mark read; preferences |
| My Profile | `/admin/profile` | Update name, email, phone, address |

### 2.1 Typical admin workflows

**Add a new student**

1. Users → create STUDENT user (or create from Students page if integrated).
2. Students → assign `school_class`, `parent`, subjects.
3. Upload photo → register face when `student_id` is set.

**Review school attendance**

1. Attendance History → pick class/session.
2. Review present/absent/not marked per student.

**Generate weekly report**

1. Weekly reports → trigger generate (calls `POST /api/weekly-reports/generate/` with `scope=SCHOOL`).
2. Download PDF when available.

---

## 3. Teacher Guide

**Base path:** `/teacher`

| Menu item | Route | Purpose |
|-----------|-------|---------|
| Overview | `/teacher` | Classes, students taught, sessions, scores, charts |
| Students | `/teacher/students` | View students in assigned classes |
| Subjects | `/teacher/subjects` | Assigned subjects |
| Attendance | `/teacher/attendance` | Start session, camera capture, complete session |
| Assessments & Grades | `/teacher/exams` | Create MCQ exams, enter grades |
| Videos | `/teacher/videos` | Upload educational videos |
| Materials | `/teacher/materials` | Upload PDF/DOC materials |
| Weekly reports | `/teacher/weekly-reports` | Teacher-scoped analytics |
| Notifications | `/teacher/notifications` | Alerts (e.g. low grades) |
| My Profile | `/teacher/profile` | Profile settings |

### 3.1 Face recognition attendance (step-by-step)

1. Open **Attendance**.
2. Start a session: select class (creates `AttendanceSession` and marks all students absent).
3. Use **camera capture** to photograph the classroom.
4. System sends image to backend → face service matches students in that class only.
5. Matched students move to **present**; roster updates.
6. Repeat captures as needed during class.
7. **Complete session** when finished — parents of students still absent receive notifications.
8. View history: `/teacher/attendance/session-history` or session detail routes.

### 3.2 Creating an exam

1. Assessments & Grades → create exam (subject, type, duration, optional class/date).
2. Add questions with multiple options and correct answer index.
3. Enter grades per student after the exam.

### 3.3 Chatbot

Floating chatbot on dashboard: ask about class attendance, grades, or exams. Suggestions are role-specific.

---

## 4. Student Guide

**Base path:** `/student`

| Menu item | Route | Purpose |
|-----------|-------|---------|
| Overview | `/student` | Personal dashboard |
| Subjects | `/student/subjects` | Enrolled subjects |
| Grades | `/student/grades` | Exam results and percentages |
| Attendance | `/student/attendance` | Personal attendance history |
| Videos | `/student/videos` | Watch assigned videos; progress saved |
| Materials | `/student/materials` | Download subject materials |
| Weekly reports | `/student/weekly-reports` | Personal weekly summary (API-driven) |
| Notifications | `/student/notifications` | Low grade and other alerts |
| My Profile | `/student/profile` | Profile; view photo/face status |

**Login tip:** Use your **student ID** as username if you do not know your Django username.

---

## 5. Parent Guide

**Base path:** `/parent`

| Menu item | Route | Purpose |
|-----------|-------|---------|
| Overview | `/parent` | Children summary, attendance/grade trends, chatbot |
| Children | `/parent/children` | Linked students |
| Attendance | `/parent/attendance` | Children's attendance |
| Grades | `/parent/grades` | Children's exam results |
| Weekly reports | `/parent/weekly-reports` | Aggregated weekly view (client-side from API data) |
| Notifications | `/parent/notifications` | Absence alerts, low grades, reports |
| My Profile | `/parent/profile` | Profile settings |

### 5.1 Understanding notifications

You may receive:

- **Absence alert** when a teacher completes an attendance session and your child remained absent.
- **Low grade alert** when a grade falls below the configured threshold (default 60%).
- **New report** when teachers publish student reports.
- **Weekly report** when school/teacher analytics are generated.

Adjust categories under Notifications → preferences (`/api/notification-preferences/`).

---

## 6. Common UI Components

| Component | Used for |
|-----------|----------|
| `FeatureModulePage` | Generic API explorer + optional camera (teacher attendance) |
| `DashboardCharts` | Recharts visualizations on dashboards |
| `SmartChatbot` | AI assistant widget |
| `SessionHistoryPage` | Session list and per-session student breakdown |
| `AttendanceCameraCapture` | Webcam integration for attendance |

---

## 7. Language (English / Arabic)

- **Login page:** Full EN/AR via i18next.
- **API-backed content:** Subject names, exam names, notification text may return `_en` / `_ar` fields or localized choice labels when `Accept-Language: ar` is set.
- **Face service messages:** Localized via `Accept-Language` header.

**TODO:** Document which dashboard labels are still English-only in the React UI (most sidebar labels in `navigation.js` are English strings).

---

## 8. Troubleshooting

| Issue | Check |
|-------|-------|
| Login fails | Credentials; student must use valid `student_id` or username |
| Face attendance does nothing | Face service running on port 8001; students have `face_registered` |
| No matches in photo | Lighting; students registered; correct class on session |
| Chatbot generic answers | `GEMINI_API_KEY` in `.env`; or fallback mode without API |
| Notifications not live | WebSocket proxy `/ws`; Daphne/ASGI running |

---

## 9. Support Contacts

**TODO:** Insert school IT support email/phone for production deployment. *(Not in codebase.)*
