# Smart School — Project Overview

> **Source of truth:** Generated from repository audit (`smart-school-backend`, June 2026).  
> **Stack:** Django 5.2 + DRF + JWT, React 19 (Vite), FastAPI face service, Microsoft SQL Server.

---

## 1. Purpose

Smart School is a bilingual (English/Arabic) school management platform that connects administrators, teachers, students, and parents around:

- User and role management
- Academic structure (classes, subjects, enrollments)
- Face-recognition attendance sessions
- MCQ exams and grades
- Educational videos and materials
- Weekly analytics reports (with optional PDF)
- In-app notifications (with WebSocket push)
- AI chatbot assistant (Google Gemini, with rule-based fallback)

---

## 2. Stakeholders and Actors

| Actor | `User.role` | Primary goals |
|-------|-------------|---------------|
| **Administrator** | `ADMIN` | School-wide CRUD, dashboards, weekly reports, user management |
| **Teacher** | `TEACHER` | Classes, attendance sessions, exams/grades, videos/materials |
| **Student** | `STUDENT` | View subjects, grades, attendance, videos, weekly self-report |
| **Parent** | `PARENT` | Monitor linked children: attendance, grades, reports |
| **System services** | — | Face Recognition microservice (port 8001), optional Gemini API |

---

## 3. Repository Layout

```
smart-school-backend/
├── smartSchool/          # Django project (settings, URLs, middleware, messages)
├── users/                # Custom User + JWT auth
├── students/ teachers/ parents/ classes/ subjects/
├── attendance/           # Attendance + sessions + face client
├── exams/                # Exams, questions, grades
├── reports/              # Report + WeeklyReport analytics
├── videos/               # Educational videos + progress
├── notifications/        # Notifications + WebSocket consumer
├── chatbot/              # Gemini-backed Q&A API
├── face_recognition_service/  # FastAPI + face_recognition library
├── frontend/app/         # React SPA (Vite)
├── locale/               # gettext AR/EN
├── docs/                 # Project documentation (this set)
└── test_automated_attendance.py
```

---

## 4. Technology Stack

| Layer | Technology | Version / notes (from `requirements.txt`, `package.json`) |
|-------|------------|--------------------------------------------------------------|
| API | Django, DRF, SimpleJWT | Django ≥5.2.10 |
| Real-time | Django Channels, Daphne | In-memory channel layer (dev) |
| DB | SQL Server via `mssql-django`, pyodbc | Env: `DB_NAME`, `DB_HOST`, etc. |
| i18n | gettext + django-modeltranslation | `en`, `ar` |
| Face service | FastAPI, face_recognition, OpenCV | Port 8001 default |
| AI | google-generativeai (optional) | `GEMINI_API_KEY` in `.env` |
| Frontend | React 19, React Router 7, Zustand, i18next, Recharts | Vite dev proxy → `:8000` |
| PDF reports | ReportLab | Weekly report export |

---

## 5. Feature Inventory (Implementation-Verified)

| Module | Backend app | Key models | Frontend routes (role prefix) |
|--------|-------------|------------|-------------------------------|
| Users & auth | `users` | `User` | `/login`, `/admin/users`, profile |
| Students | `students` | `Student` | `/admin/students`, `/teacher/students` |
| Teachers | `teachers` | `Teacher`, `TeacherSubjectClass` | `/admin/teachers` |
| Parents | `parents` | `Parent` | `/admin/parents`, `/parent/children` |
| Classes | `classes` | `SchoolClass` | `/admin/classes` |
| Subjects & materials | `subjects` | `Subject`, `Material` | `/admin/subjects`, `/teacher/materials` |
| Attendance | `attendance` | `Attendance`, `AttendanceSession` | `/teacher/attendance`, `/admin/attendance` |
| Exams & grades | `exams` | `Exam`, `Question`, `Grade` | `*/exams`, `*/grades` |
| Reports | `reports` | `Report`, `WeeklyReport` | `*/weekly-reports` |
| Videos | `videos` | `Video`, `VideoProgress` | `/teacher/videos`, `/student/videos` |
| Notifications | `notifications` | `Notification`, `NotificationPreference` | `*/notifications` |
| Chatbot | `chatbot` | — (stateless API) | `SmartChatbot` in dashboards |
| Face recognition | `face_recognition_service` | Pickle encodings on disk | `AttendanceCameraCapture`, admin student photo |

---

## 6. Authentication Summary

- **Login:** `POST /api/auth/login/` — JWT access + refresh; custom serializer adds `role`, `user` payload; students may log in with `student_id` instead of username.
- **Refresh:** `POST /api/auth/refresh/`
- **Profile:** `GET|PATCH /api/users/me/`
- **Frontend:** Zustand `authStore` persists tokens; `apiFetch` sends `Authorization: Bearer` and `Accept-Language`.
- **Route guard:** `RequireRole` wraps `/admin`, `/teacher`, `/student`, `/parent`.

---

## 7. Cross-Cutting Capabilities

Detailed chapters appear in `system-architecture.md` and `srs.md`:

1. **Face Recognition Attendance** — session-based batch detection
2. **AI Chatbot Assistant** — intent detection + DB context + Gemini
3. **Localization (EN/AR)** — middleware, modeltranslation, React i18n (login)
4. **Role-Based Access Control** — permission classes + queryset filtering

---

## 8. External Dependencies & Environment

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django/JWT signing |
| `DB_*` | SQL Server connection |
| `GEMINI_API_KEY` | Chatbot LLM |
| `FACE_RECOGNITION_SERVICE_URL` | Default `http://localhost:8001` |
| `NOTIFICATION_LOW_GRADE_PERCENT` | Default `60` — triggers low-grade alerts |

**TODO:** Document production hostnames, TLS certificates, and institutional SSO if deployed beyond the current JWT login. *(Not present in codebase.)*

---

## 9. Related Documentation

| Document | Contents |
|----------|----------|
| [srs.md](./srs.md) | Functional requirements, use cases, business rules |
| [system-architecture.md](./system-architecture.md) | UML-style diagram descriptions, deployment |
| [database-design.md](./database-design.md) | ERD, tables, constraints |
| [api-documentation.md](./api-documentation.md) | REST endpoints |
| [user-manual.md](./user-manual.md) | Role-based UI guide |
| [testing.md](./testing.md) | Test strategy and scripts |
| [thesis-outline.md](./thesis-outline.md) | Graduation thesis chapter plan |
| [localization.md](./localization.md) | Deep dive on i18n (existing) |

---

## 10. Diagram References (Textual)

Use case, sequence, component, and deployment diagram **descriptions** are centralized in [system-architecture.md](./system-architecture.md) and expanded per feature in [srs.md](./srs.md).
