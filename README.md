# 🏫 Smart School

> A bilingual (English/Arabic) school management platform that connects administrators, teachers, students, and parents with face-recognition attendance, AI-powered chatbot, real-time notifications, and comprehensive academic analytics.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **User & Role Management** | JWT-based auth with four roles: Admin, Teacher, Student, Parent |
| **Face-Recognition Attendance** | Session-based batch detection via FastAPI microservice + OpenCV |
| **MCQ Exams & Grades** | Create exams, manage questions, auto-grade, and track performance |
| **Weekly Analytics Reports** | Automated report generation with optional PDF export (ReportLab) |
| **Real-Time Notifications** | WebSocket push via Django Channels — low-grade & at-risk alerts |
| **AI Chatbot Assistant** | Google Gemini-powered Q&A with rule-based fallback |
| **Educational Videos & Materials** | Upload, watch, and track video progress per subject |
| **Bilingual Support (EN/AR)** | Full i18n on backend (django-modeltranslation) and frontend (i18next) |
| **Parent Monitoring** | Linked children view — attendance, grades, and reports |
| **Role-Based Access Control** | Permission classes + queryset filtering per role |

---

## 🛠️ Technology Stack

### Backend

| Layer | Technology |
|-------|-----------|
| API Framework | Django 5.2 + Django REST Framework |
| Auth | SimpleJWT (access + refresh tokens) |
| Real-Time | Django Channels + Daphne (WebSocket) |
| Database | Microsoft SQL Server (`mssql-django` + `pyodbc`) |
| i18n | `django-modeltranslation` + gettext |
| PDF Reports | ReportLab |
| AI | `google-generativeai` (Gemini) |

### Face Recognition Service

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI + Uvicorn |
| Detection | `face_recognition` library + OpenCV |
| Storage | Pickle encodings on disk |

### Frontend

| Layer | Technology |
|-------|-----------|
| Framework | React 19 (Vite) |
| Routing | React Router 7 |
| State | Zustand |
| Charts | Recharts |
| i18n | i18next + react-i18next |
| HTTP | Custom `apiFetch` with JWT + language headers |

---

## 📁 Project Structure

```
smart-school/
├── smartSchool/               # Django project config (settings, URLs, ASGI, middleware)
├── users/                     # Custom User model + JWT auth endpoints
├── students/                  # Student model, serializers, views
├── teachers/                  # Teacher model + TeacherSubjectClass assignment
├── parents/                   # Parent model + child linking
├── subjects/                  # Subject & Material models
├── classes/                   # SchoolClass model
├── attendance/                # Attendance sessions + face-recognition client
├── exams/                     # Exam, Question, Grade models
├── reports/                   # Report + WeeklyReport + PDF generation
├── videos/                    # Video & VideoProgress models
├── notifications/             # Notification + WebSocket consumer + management commands
├── chatbot/                   # Gemini-backed Q&A API (stateless)
├── face_recognition_service/  # FastAPI microservice (port 8001)
├── frontend/app/              # React SPA (Vite)
│   ├── src/
│   │   ├── pages/             # Role-based page components (admin/, teacher/, student/, parent/)
│   │   ├── components/        # Shared UI components
│   │   ├── stores/            # Zustand stores (auth, notifications, etc.)
│   │   ├── hooks/             # Custom React hooks
│   │   ├── styles/            # CSS stylesheets
│   │   ├── config/            # App configuration
│   │   └── i18n.js            # i18next setup
│   └── vite.config.js
├── locale/                    # gettext translation files (en/, ar/)
├── docs/                      # Project documentation (SRS, architecture, API docs, DB design)
├── scripts/                   # Utility scripts
├── manage.py                  # Django management entry point
└── requirements.txt           # Python dependencies
```

---

## ⚡ Quick Start

### Prerequisites

- **Python** ≥ 3.10
- **Node.js** ≥ 18
- **Microsoft SQL Server** (running instance)
- **ODBC Driver 17 for SQL Server**
- **dlib** (for face_recognition — see [`face_recognition_service/INSTALL_DLIB.md`](face_recognition_service/INSTALL_DLIB.md))

### 1. Clone the Repository

```bash
git clone <repo-url>
cd smart-school
```

### 2. Backend Setup

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Environment Variables below)
copy .env.example .env     # Windows
# cp .env.example .env      # Linux/Mac

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Seed demo data (optional)
python manage.py seed_data

# Start the backend server
python manage.py runserver
```

The Django API server runs at **http://localhost:8000**.

### 3. Face Recognition Service

```bash
cd face_recognition_service

# Install face service dependencies (in a separate venv recommended)
pip install -r requirements.txt

# Start the FastAPI service
python main.py
```

The face recognition service runs at **http://localhost:8001** by default.

> 💡 On Windows, you can use the provided batch script: `start_face_recognition_service.bat`

### 4. Frontend Setup

```bash
cd frontend

# Install root dependencies
npm install

# Install app dependencies
npm run install:app

# Start the dev server
npm run dev
```

The React frontend runs at **http://localhost:5173** and proxies API requests to `:8000`.

---

## 🔑 Environment Variables

Create a `.env` file in the project root with the following variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django/JWT signing key | (insecure default for dev) |
| `DB_NAME` | SQL Server database name | `smart-school` |
| `DB_HOST` | SQL Server host | `DESKTOP-2ASDU43\SQLEXPRESS` |
| `DB_PORT` | SQL Server port (omit for named instances) | — |
| `DB_USER` | SQL Server auth user (empty = Windows auth) | — |
| `DB_PASSWORD` | SQL Server auth password | — |
| `DB_DRIVER` | ODBC driver name | `ODBC Driver 17 for SQL Server` |
| `GEMINI_API_KEY` | Google Gemini API key for chatbot | — |
| `FACE_RECOGNITION_SERVICE_URL` | Face service endpoint | `http://localhost:8001` |
| `NOTIFICATION_LOW_GRADE_PERCENT` | Threshold for low-grade alerts | `50` |
| `NOTIFICATION_AT_RISK_ABSENCE_THRESHOLD` | Absences to flag at-risk | `3` |
| `NOTIFICATION_AT_RISK_ABSENCE_WINDOW_DAYS` | Window for at-risk detection | `30` |
| `NOTIFICATION_AT_RISK_GRADE_PERCENT` | Grade % for at-risk flag | `50` |

---

## 🔐 Authentication & Roles

| Role | `User.role` | Access Scope |
|------|-------------|--------------|
| **Admin** | `ADMIN` | Full CRUD — users, classes, subjects, attendance, reports |
| **Teacher** | `TEACHER` | Assigned classes, attendance sessions, exams, materials, videos |
| **Student** | `STUDENT` | View own subjects, grades, attendance, videos, weekly self-report |
| **Parent** | `PARENT` | Monitor linked children — attendance, grades, reports |

- **Login:** `POST /api/auth/login/` — returns JWT access + refresh tokens
- **Refresh:** `POST /api/auth/refresh/`
- **Profile:** `GET|PATCH /api/users/me/`
- **Frontend guard:** `RequireRole` component wraps role-specific routes

---

## 📡 API Overview

All API endpoints are prefixed with `/api/`:

| Endpoint Prefix | Module |
|-----------------|--------|
| `/api/auth/` | Users — login, refresh, profile |
| `/api/students/` | Students CRUD |
| `/api/teachers/` | Teachers CRUD |
| `/api/parents/` | Parents CRUD |
| `/api/subjects/` | Subjects & Materials |
| `/api/classes/` | School Classes |
| `/api/attendance/` | Attendance sessions & records |
| `/api/exams/` | Exams, Questions, Grades |
| `/api/reports/` | Reports & Weekly Analytics |
| `/api/videos/` | Videos & Progress |
| `/api/notifications/` | Notifications & Preferences |
| `/api/chatbot/` | AI Chatbot Q&A |

> Full API documentation is available in [`docs/api-documentation.md`](docs/api-documentation.md)

---

## 📊 Management Commands

| Command | App | Description |
|---------|-----|-------------|
| `seed_data` | students | Populate demo students, classes, subjects |
| `create_test_data` | users | Create test users for each role |
| `backfill_student_ids` | students | Backfill student ID fields |
| `generate_weekly_reports` | reports | Generate weekly analytics reports |
| `send_exam_reminders` | notifications | Send exam reminder notifications |
| `detect_at_risk` | notifications | Detect and notify at-risk students |
| `test_notifications` | notifications | Test notification delivery |
| `register_student_faces` | root | Batch register student face encodings |

---

## 🧪 Testing

```bash
# Run Django tests
python manage.py test

# Test face recognition service
cd face_recognition_service
python test_face_service.py

# Test automated attendance workflow
python test_automated_attendance.py

# Test API endpoints
python test_api.py
```

See [`TESTING_GUIDE.md`](TESTING_GUIDE.md) for detailed testing instructions.

---

## 📚 Documentation

| Document | Contents |
|----------|----------|
| [`docs/PROJECT_PROPOSAL.md`](docs/PROJECT_PROPOSAL.md) | Project proposal and objectives |
| [`docs/srs.md`](docs/srs.md) | Functional requirements, use cases, business rules |
| [`docs/system-architecture.md`](docs/system-architecture.md) | UML-style diagrams, deployment architecture |
| [`docs/database-design.md`](docs/database-design.md) | ERD, tables, constraints |
| [`docs/api-documentation.md`](docs/api-documentation.md) | REST endpoint reference |
| [`docs/localization.md`](docs/localization.md) | Deep dive on i18n implementation |
| [`docs/project-overview.md`](docs/project-overview.md) | Implementation-verified feature inventory |
| [`FACE_RECOGNITION_INTEGRATION.md`](FACE_RECOGNITION_INTEGRATION.md) | Face recognition integration guide |
| [`AUTOMATED_ATTENDANCE_WORKFLOW.md`](AUTOMATED_ATTENDANCE_WORKFLOW.md) | Automated attendance workflow |
| [`TESTING_GUIDE.md`](TESTING_GUIDE.md) | Test strategy and scripts |

---

## 🖼️ Frontend Pages

The React SPA provides role-specific dashboards:

- **Admin:** `/admin/*` — users, students, teachers, parents, classes, subjects, attendance, reports
- **Teacher:** `/teacher/*` — attendance sessions, exams, materials, videos, students
- **Student:** `/student/*` — subjects, grades, attendance, videos, weekly self-report
- **Parent:** `/parent/*` — children overview, attendance, grades, reports
- **Shared:** `/login`, `/notifications`, chatbot widget

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is developed as a graduation thesis project. See the [`docs/`](docs/) directory for thesis-related documentation.

---

<p align="center">
  Built with ❤️ for smarter school management
</p>