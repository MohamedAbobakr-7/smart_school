# System Architecture

> Diagram descriptions for thesis/documentation tools (PlantUML, draw.io, etc.).  
> All relationships verified against `smartSchool/urls.py`, `settings.py`, and service code.

---

## 1. High-Level Architecture

```
┌─────────────────┐     HTTPS/HTTP      ┌──────────────────────────────┐
│  React SPA      │ ──────────────────► │  Django + DRF + Channels     │
│  (Vite :5173)   │   /api/*  /media/*  │  (Daphne/ASGI :8000)         │
│                 │   /ws/notifications │                              │
└─────────────────┘                     │  ┌────────┐  ┌─────────────┐ │
                                        │  │ SQL    │  │ Media files │ │
                                        │  │ Server │  │ (photos…)   │ │
                                        │  └────────┘  └─────────────┘ │
                                        └───────────┬──────────────────┘
                                                    │ HTTP multipart
                                                    ▼
                                        ┌──────────────────────────────┐
                                        │  Face Recognition Service    │
                                        │  FastAPI (:8001)             │
                                        │  face_encodings/*.pkl        │
                                        └──────────────────────────────┘
                                                    │
                                        ┌───────────▼──────────────────┐
                                        │  Google Gemini API (optional) │
                                        │  Chatbot LLM                  │
                                        └──────────────────────────────┘
```

---

## 2. Component Diagram Description

### 2.1 Presentation Layer

| Component | Path | Responsibility |
|-----------|------|----------------|
| **React Application** | `frontend/app/src/` | SPA routing, role dashboards, forms |
| **Auth Store** | `stores/authStore.js` | JWT persistence, login/logout |
| **API Client** | `lib/api.js` | `apiFetch`, pagination helper, `Accept-Language` |
| **i18n** | `i18n.js`, `stores/langStore.js` | Login UI translations; lang header for API |
| **Layout** | `components/layout/` | `DashboardLayout`, `Sidebar` from `navigation.js` |
| **Chatbot UI** | `components/chatbot/SmartChatbot.jsx` | Calls `/api/chatbot/ask/` |
| **Attendance Camera** | `components/attendance/AttendanceCameraCapture.jsx` | Webcam capture → process-classroom-image |

### 2.2 Application Layer (Django Apps)

| Component | Responsibility |
|-----------|----------------|
| `users` | Authentication, profiles, admin dashboard API |
| `students` | Student CRUD, face register, student weekly report |
| `teachers` | Teacher CRUD, teacher dashboard |
| `parents` | Parent CRUD, parent dashboard |
| `classes` | School class groups |
| `subjects` | Subjects, materials |
| `attendance` | Records, sessions, face client orchestration |
| `exams` | Exams, questions, grades |
| `reports` | Academic reports, weekly analytics + PDF |
| `videos` | Video upload, student progress |
| `notifications` | CRUD preferences, WebSocket consumer, signals |
| `chatbot` | Intent + context + Gemini |

### 2.3 Infrastructure Layer

| Component | Configuration |
|-----------|---------------|
| **SQL Server** | `DATABASES['default']` engine `mssql` |
| **Channel Layer** | `InMemoryChannelLayer` (development) |
| **Static/Media** | `MEDIA_ROOT` for uploads |
| **Face encodings** | `face_recognition_service/face_encodings/` |

### 2.4 External Services

| Service | Protocol | Used by |
|---------|----------|---------|
| Face Recognition | REST multipart | `attendance.face_recognition_client` |
| Gemini | google-generativeai SDK | `chatbot.views.call_gemini` |

---

## 3. Deployment Diagram Description

### 3.1 Development (as implemented)

| Node | Process | Port |
|------|---------|------|
| Dev workstation | `python manage.py runserver` or Daphne | 8000 |
| Dev workstation | `uvicorn face_recognition_service.main:app` | 8001 |
| Dev workstation | `npm run dev` (Vite) | 5173 (typical) |
| SQL Server Express | Database `smart-school` | instance-specific |

Vite proxies `/api`, `/media`, `/ws` → `127.0.0.1:8000` (`vite.config.js`).

### 3.2 Production (recommended topology — partial TODO)

```
[Browser] → [Reverse Proxy / TLS] → [Static CDN or Nginx for React build]
                                 → [Gunicorn/Daphne workers] → [SQL Server]
                                 → [Face service container/host :8001]
```

**TODO:** Document actual production hostnames, process manager (systemd/IIS), and whether React is served separately or via Django. *(Not in repository.)*

### 3.3 Environment variables (deployment)

See `smartSchool/settings.py` and `face_recognition_service/.env` pattern: `SECRET_KEY`, `DB_*`, `GEMINI_API_KEY`, `FACE_RECOGNITION_SERVICE_URL`.

---

## 4. Sequence Diagram Descriptions

### 4.1 User Login

1. **User** enters credentials on `LoginPage`.
2. **React** `POST /api/auth/login/` with `Accept-Language`.
3. **Django** `CustomTokenObtainPairSerializer` validates user (or resolves `student_id`).
4. **Django** returns `access`, `refresh`, `user` object with role.
5. **React** stores tokens in Zustand → `navigate(homePathForRole(role))`.
6. **RequireRole** checks `user.role` on subsequent routes.

### 4.2 Face Recognition Attendance

1. **Teacher** opens attendance module → checks `GET /api/attendance-sessions/active/`.
2. If none: **Teacher** `POST /api/attendance-sessions/` with `school_class`, `class_name`.
3. **Django** creates session + bulk `Attendance` rows (`absent`, `manual`).
4. **Teacher** captures image → `POST /api/attendance/process-classroom-image/` (`session_id`, `image`).
5. **Django** loads class `student_id` list → **FaceRecognitionClient.detect_faces_batch**.
6. **FastAPI** detects faces, matches encodings (filtered IDs) → returns `matches`.
7. **Django** upserts `Attendance` to `present`, `face_recognition`; updates session counters.
8. **Teacher** `POST /api/attendance-sessions/{id}/complete/`.
9. **Django** creates `Notification` for each absent child → parent users; optional WebSocket push.

### 4.3 Student Face Registration

1. **Admin/Teacher** `POST /api/students/{id}/register-face/` with `photo` multipart.
2. **Django** saves `Student.photo`, resets `face_registered=False`.
3. If `student_id` empty → return success with photo only (no service call).
4. **Django** `FaceRecognitionClient.register_face(student_id, file)`.
5. **FastAPI** `process_image` → `save_student_face_encoding` → pickle file.
6. **Django** sets `face_registered=True` on success.

### 4.4 Chatbot Question

1. **User** sends message in `SmartChatbot`.
2. **React** `POST /api/chatbot/ask/` `{ message }`.
3. **Django** `detect_intent(message, role)`.
4. **Django** `build_context_for_user(user, intent)` queries ORM.
5. **Django** `call_gemini` or `_smart_fallback`.
6. **React** displays `reply` and `suggestions`.

### 4.5 Real-Time Notification

1. **Signal** (e.g. low grade on `Grade.post_save`) calls `notifications.services.create_notification`.
2. **Service** checks `NotificationPreference`, inserts row, `push_to_websocket`.
3. **Channels** `group_send` to `notifications_user_{id}`.
4. **Browser** WebSocket `ws/notifications/` (JWT middleware) receives payload.
5. **Frontend** `notificationStore` updates UI (if connected).

---

## 5. Use Case ↔ Component Mapping

| Use case | Primary components |
|----------|-------------------|
| Manage students | `StudentViewSet`, `AdminStudentsPage` |
| Take attendance | `AttendanceSessionViewSet`, `AttendanceViewSet`, FastAPI |
| Grade exam | `GradeViewSet`, `TeacherExamsPage` |
| Weekly analytics | `WeeklyReportViewSet`, `weekly_report_service` |
| Chat | `ChatbotAskView`, `SmartChatbot` |

---

## 6. Security Architecture

| Concern | Mechanism |
|---------|-----------|
| API auth | JWT Bearer (`rest_framework_simplejwt`) |
| WebSocket auth | `notifications.middleware.JWTWebSocketMiddleware` |
| RBAC | Permission classes + queryset filters + React `RequireRole` |
| CSRF | Django middleware (API uses JWT, not session cookies for SPA) |
| Face data | Encodings on disk; not in SQL Server |

**TODO:** Document penetration test results and secrets management (Azure Key Vault, etc.) if required by institution.

---

## 7. Data Flow — Weekly Report Generation

1. Admin/Teacher `POST /api/weekly-reports/generate/`.
2. `weekly_report_service.upsert_weekly_report` aggregates attendance/grades/exams.
3. Writes JSON fields on `WeeklyReport`; optional ReportLab PDF to `pdf_file`.
4. Signal may notify users (`NEW_WEEKLY_REPORT`).
5. UI `GET /api/weekly-reports/dashboard/?weeks=8` for charts.

---

## 8. Related Files

| Topic | Location |
|-------|----------|
| URL routing | `smartSchool/urls.py` |
| ASGI | `smartSchool/asgi.py` |
| Face client | `attendance/face_recognition_client.py` |
| Face API | `face_recognition_service/main.py` |
| Frontend routes | `frontend/app/src/App.jsx` |
