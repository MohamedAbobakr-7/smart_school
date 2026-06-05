# Software Requirements Specification (SRS)

> Derived from Django models, DRF viewsets, React routes, and microservice code.  
> **Version:** 1.0 (codebase audit, June 2026)

---

## 1. Introduction

### 1.1 Scope

The Smart School system provides a web application for managing school operations with four user roles, REST APIs, a React dashboard, a face-recognition attendance microservice, and an AI chatbot.

### 1.2 Definitions

| Term | Meaning in this system |
|------|------------------------|
| Session | `AttendanceSession` — teacher-led attendance period for one class on one date |
| Face registration | Storing a 128-d face encoding keyed by `student_id` in the face service |
| Weekly report | `WeeklyReport` analytics snapshot (`SCHOOL` or `TEACHER` scope) |
| Grade | `Grade` — score on an MCQ `Exam` (percentage = score / question count) |

---

## 2. Use Case Diagram Descriptions

### 2.1 Administrator

| Use case | Description |
|----------|-------------|
| Manage users | CRUD on `User`; filter by role; view admin dashboard KPIs |
| Manage students/teachers/parents | Full CRUD via respective viewsets |
| Manage classes & subjects | CRUD `SchoolClass`, `Subject`, assign relations |
| View attendance history | Read-only attendance sessions; class history API |
| Manage exams | Full exam/question/grade access |
| Generate weekly reports | `POST /api/weekly-reports/generate/` with `scope=SCHOOL` or `all_teachers=true` |
| Receive notifications | List, mark read, configure preferences |
| Ask chatbot | School-wide statistics via `/api/chatbot/ask/` |

**Actor:** Administrator (`User.role = ADMIN`)

### 2.2 Teacher

| Use case | Description |
|----------|-------------|
| View assigned students | Filtered by assigned classes, sessions, exams |
| Start attendance session | Create `AttendanceSession`; bulk absent records for class |
| Capture classroom photo | `POST /api/attendance/process-classroom-image/` |
| Complete/cancel session | Triggers parent absence notifications on complete |
| Create exams & grades | MCQ exams with JSON options; grade students |
| Upload videos & materials | `Video`, `Material` with subject linkage |
| View teacher dashboard | `GET /api/teachers/dashboard/` |
| Generate teacher weekly report | `scope=TEACHER` on generate endpoint |

**Actor:** Teacher (`User.role = TEACHER`)

### 2.3 Student

| Use case | Description |
|----------|-------------|
| View own attendance/grades | Queryset scoped to `student_profile` |
| View enrolled subjects & materials | Subject M2M on `Student` |
| Watch videos & sync progress | `VideoProgressViewSet` |
| View weekly self-report | `GET /api/students/weekly-report/` |
| Login with student ID | `CustomTokenObtainPairSerializer` resolves `student_id` |
| Ask chatbot | Personal attendance/grades context |

**Actor:** Student (`User.role = STUDENT`)

### 2.4 Parent

| Use case | Description |
|----------|-------------|
| View children | Students where `Student.parent` links to parent profile |
| Monitor attendance & grades | Filtered querysets on children |
| View computed weekly summary | Client aggregates `/students/`, `/attendance/`, `/grades/` |
| Receive absence/low-grade alerts | Notifications + WebSocket |
| Ask chatbot | Per-child context in `chatbot/views.py` |

**Actor:** Parent (`User.role = PARENT`)

### 2.5 System (Face Recognition Service)

| Use case | Description |
|----------|-------------|
| Register face | `POST /register-face` after photo upload |
| Batch detect & match | `POST /detect-faces-batch` with optional `student_ids` filter |
| Verify single face | `POST /verify-face` |

**Actor:** Face Recognition Service (automated, invoked by Django)

---

## 3. Functional Requirements by Feature

### 3.1 Users & Authentication

| ID | Requirement | Implementation |
|----|-------------|----------------|
| AUTH-01 | Users authenticate with JWT | `users/urls.py`: login, refresh |
| AUTH-02 | Roles: ADMIN, TEACHER, STUDENT, PARENT | `users.models.User.Role` |
| AUTH-03 | Superusers auto-assigned ADMIN | `User.save()` |
| AUTH-04 | Students may use `student_id` at login | `CustomTokenObtainPairSerializer.validate()` |
| AUTH-05 | Default API requires authentication | `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES` |

**Business rules:**

- Only ADMIN creates/updates/deletes users (`UserViewSet.get_permissions`).
- Students/parents see limited user lists (`get_queryset`).

**APIs:** `POST /api/auth/login/`, `POST /api/auth/refresh/`, `/api/users/`, `/api/users/me/`

**Tables:** `users`

**Screens:** `LoginPage.jsx`, `ProfilePage.jsx`, `AdminUsersPage.jsx`

---

### 3.2 Students

| ID | Requirement | Implementation |
|----|-------------|----------------|
| STU-01 | One user account per student | `Student.user` OneToOne |
| STU-02 | Unique `student_id` (auto-generated if blank) | `students/utils.py`, backfill action |
| STU-03 | Photo for face recognition | `Student.photo`, `face_registered` |
| STU-04 | Link to class and parent | `school_class`, `parent` FKs |
| STU-05 | Subject enrollment | M2M `subjects` |

**APIs:** CRUD `/api/students/`, `POST .../register-face/`, `GET .../face-status/`, `POST .../backfill-ids/` (admin), `GET .../weekly-report/`, `GET .../dashboard/` (student)

**Tables:** `students`, `students_subjects` (M2M)

**Screens:** `AdminStudentsPage.jsx`, `TeacherStudentsPage.jsx`, `StudentDashboard.jsx`

---

### 3.3 Teachers

| ID | Requirement | Implementation |
|----|-------------|----------------|
| TCH-01 | Assign subjects and classes | M2M `assigned_subjects`, `assigned_classes` |
| TCH-02 | Map teacher–subject–class | `TeacherSubjectClass` unique triple |
| TCH-03 | Teacher dashboard metrics | `GET /api/teachers/dashboard/` |

**APIs:** `/api/teachers/`, dashboard action

**Tables:** `teachers`, `teacher_subject_classes`, M2M tables

**Screens:** `AdminTeachersPage.jsx`, `TeacherDashboard.jsx`

---

### 3.4 Parents

| ID | Requirement | Implementation |
|----|-------------|----------------|
| PAR-01 | Parent linked to children via `Student.parent` | Reverse `children` |
| PAR-02 | Parent dashboard KPIs | `GET /api/parents/dashboard/` |

**APIs:** `/api/parents/`, dashboard

**Tables:** `parents`, `students.parent_id`

**Screens:** `AdminParentsPage.jsx`, `ParentDashboard.jsx`, `ParentChildrenPage.jsx`

---

### 3.5 Classes & Subjects

| ID | Requirement | Implementation |
|----|-------------|----------------|
| CLS-01 | Class name + optional section, unique together | `SchoolClass` |
| SUB-01 | Subject code unique | `Subject.code` |
| SUB-02 | Bilingual name/description | modeltranslation on Subject, Material |
| MAT-01 | Teachers upload files per subject | `Material` model |

**APIs:** `/api/classes/`, `/api/subjects/`, `/api/materials/`

**Tables:** `school_classes`, `subjects`, `materials`

**Screens:** `AdminClassesPage.jsx`, `AdminSubjectsPage.jsx`, `TeacherSubjectsPage.jsx`, `TeacherMaterialsPage.jsx`

---

### 3.6 Attendance (Manual + Face Recognition)

| ID | Requirement | Implementation |
|----|-------------|----------------|
| ATT-01 | One attendance record per student per day | `unique_together (student, date)` |
| ATT-02 | Status: present / absent | `Attendance.STATUS_CHOICES` |
| ATT-03 | Source: manual / face_recognition | `Attendance.source` |
| ATT-04 | Teacher creates session → all class students absent initially | `AttendanceSessionViewSet.perform_create` |
| ATT-05 | Batch image updates absent→present for matched faces | `process_classroom_image` |
| ATT-06 | Only students in session class are marked | `school_class` verification |
| ATT-07 | On session complete, notify parents of absent children | `complete_session` bulk `Notification` |
| ATT-08 | No duplicate active session same class+date | Validation in `perform_create` |

**APIs:**

- `/api/attendance/` (CRUD; teacher write; upsert on create)
- `/api/attendance/process-classroom-image/` (POST multipart)
- `/api/attendance-sessions/` (CRUD teacher; admin read)
- `GET .../active/`, `GET .../roster/`, `POST .../complete/`, `POST .../cancel/`
- `GET .../history/`, `GET .../class-history/?school_class=`

**Tables:** `attendance`, `attendance_sessions`

**Screens:** `FeatureModulePage` (teacher attendance + camera), `SessionHistoryPage.jsx`, `StudentAttendancePage.jsx`, `ParentAttendancePage.jsx`

**Sequence (face attendance):** See [system-architecture.md](./system-architecture.md#sequence-face-recognition-attendance)

---

### 3.7 Exams & Grades

| ID | Requirement | Implementation |
|----|-------------|----------------|
| EXM-01 | MCQ exams with JSON options and correct index | `Question.options`, `correct_answer` |
| EXM-02 | Exam types: quiz, midterm, final, assignment | `Exam.exam_type` |
| EXM-03 | One grade per student per exam | `Grade` unique_together |
| EXM-04 | Letter grade A–F from percentage | `Grade.get_grade_letter()` |
| EXM-05 | Low grade notifications below threshold | `notifications/signals.py` on `Grade` save |

**APIs:** `/api/exams/`, `/api/questions/`, `/api/grades/`, `GET /api/exams/upcoming/` (student)

**Tables:** `exams`, `questions`, `grades`

**Screens:** `AdminExamsPage.jsx`, `TeacherExamsPage.jsx`, `StudentGradesPage.jsx`, `ParentGradesPage.jsx`

---

### 3.8 Weekly Reports

| ID | Requirement | Implementation |
|----|-------------|----------------|
| WR-01 | School-wide and per-teacher weekly snapshots | `WeeklyReport.scope` |
| WR-02 | JSON stats: attendance, academic, exams, charts, insights | JSON fields on model |
| WR-03 | Optional PDF file | `pdf_file`, ReportLab in service layer |
| WR-04 | Dedupe key per week+scope | `dedupe_key` on save |
| WR-05 | Management command for batch generation | `generate_weekly_reports` command |

**APIs:** `/api/weekly-reports/`, `GET .../dashboard/`, `POST .../generate/`, `GET .../{id}/download-pdf/`

**Tables:** `weekly_reports`

**Screens:** `AdminWeeklyReportsPage.jsx`, `TeacherWeeklyReportsPage.jsx`, `StudentWeeklyReportsPage.jsx` (API), `ParentWeeklyReportsPage.jsx` (client-side aggregate)

---

### 3.9 Videos

| ID | Requirement | Implementation |
|----|-------------|----------------|
| VID-01 | Teachers upload mp4/webm/mov/etc. | `Video.video_file` validators |
| VID-02 | Students track watch position and completion | `VideoProgress` unique (student, video) |
| VID-03 | Stream endpoint | `videos/streaming.py` (if used by views) |

**APIs:** `/api/videos/`, `/api/video-progress/`, `POST .../sync/`

**Tables:** `educational_videos`, `video_progress`

**Screens:** `TeacherVideosPage.jsx`, `StudentVideosPage.jsx`

---

### 3.10 Notifications

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NTF-01 | Types: LOW_GRADE, ATTENDANCE, NEW_STUDENT_REPORT, NEW_WEEKLY_REPORT, SYSTEM | `Notification.Type` |
| NTF-02 | Per-user preferences | `NotificationPreference` |
| NTF-03 | Dedupe keys prevent duplicate alerts | `dedupe_key` |
| NTF-04 | Real-time push via WebSocket | `ws/notifications/`, Channels |

**APIs:** `/api/notifications/`, `POST .../mark-read/`, `POST .../mark-all-read/`, `/api/notification-preferences/`

**Tables:** `notifications`, `notification_preferences`

**Screens:** `NotificationsPage.jsx`

---

### 3.11 AI Chatbot

| ID | Requirement | Implementation |
|----|-------------|----------------|
| BOT-01 | Authenticated users ask natural-language questions | `POST /api/chatbot/ask/` |
| BOT-02 | Intent detection (attendance, grades, etc.) | `detect_intent()` |
| BOT-03 | Role-scoped DB context injected into prompt | `_build_*_context()` |
| BOT-04 | Gemini API when `GEMINI_API_KEY` set; else fallback | `call_gemini()`, `_smart_fallback()` |
| BOT-05 | Quick suggestions per role | `ROLE_SUGGESTIONS`, `GET /api/chatbot/ask/` |

**APIs:** `POST|GET /api/chatbot/ask/`

**Tables:** Read-only across attendance, grades, students, etc.

**Screens:** `SmartChatbot.jsx`, `ParentChatbot.jsx`

---

## 4. Non-Functional Requirements (Observed)

| ID | Category | Requirement | Notes |
|----|----------|-------------|-------|
| NFR-01 | Security | JWT bearer auth on API | SimpleJWT HS256 |
| NFR-02 | i18n | EN/AR API messages and model fields | See localization chapter |
| NFR-03 | Performance | Face batch timeout 120s default | `FACE_RECOGNITION_BATCH_TIMEOUT` |
| NFR-04 | Pagination | Page size 20 | DRF `PAGE_SIZE` |
| NFR-05 | Availability | Face service optional degradation | Photo saved even if service offline |

**TODO:** Define formal SLA, max concurrent users, and backup RPO/RTO for production thesis deployment. *(Not in repository.)*

---

## 5. Dedicated System Chapters (Thesis-Ready Summaries)

### 5.1 Face Recognition Attendance

**Purpose:** Automate marking present students from a classroom photo during an active session.

**Flow:**

1. Teacher creates `AttendanceSession` for a `SchoolClass` → absent records for all enrolled students.
2. Teacher uploads classroom image → Django calls FastAPI `detect-faces-batch` with class `student_ids`.
3. Matches update/create `Attendance` as `present`, `source=face_recognition`.
4. Teacher completes session → parents of still-absent students receive `ATTENDANCE` notifications.

**Actors:** Teacher, Face Recognition Service, Parent (notified)

**Tolerance:** 0.6 default; HOG model default in client.

### 5.2 AI Chatbot Assistant

**Purpose:** Natural-language access to role-appropriate school data.

**Mechanism:** Keyword intent → SQL-backed context strings → Gemini `generate_content` (max 300 tokens, temperature 0.3) or formatted fallback.

**Constraints:** 500 character message limit; answers must use provided context only (prompt rules).

### 5.3 Localization (English / Arabic)

**Backend:** `APILanguageMiddleware`, `smartSchool/messages.py`, `locale/ar/`, modeltranslation `_en`/`_ar` columns.

**Frontend:** i18next for login strings; `Accept-Language` from `localStorage` key `ss_lang`; RTL styling **TODO:** verify full-app RTL CSS coverage beyond login.

**Face service:** Dictionary translations in `face_recognition_service/translations.py`.

### 5.4 Role-Based Access Control

**Layers:**

1. DRF permission classes (`IsAdmin`, `IsTeacher`, `IsAdminOrTeacher`, etc.)
2. Per-viewset `get_permissions()` action overrides
3. `get_queryset()` row-level filtering by role
4. React `RequireRole` route wrapper

Utility helpers in `users/permissions.py`: `can_access_student_data`, `can_modify_student_data`.

---

## 6. Traceability Matrix (Sample)

| Requirement | Model | View/Endpoint | UI |
|-------------|-------|---------------|-----|
| ATT-05 | `Attendance` | `process_classroom_image` | `AttendanceCameraCapture` |
| EXM-05 | `Grade` | `notifications.signals` | `NotificationsPage` |
| BOT-01 | — | `ChatbotAskView` | `SmartChatbot` |
| WR-03 | `WeeklyReport.pdf_file` | `download_pdf` | Admin/Teacher weekly pages |
