# Smart School — Documentation Index

Welcome to the technical documentation for **Smart School**, a bilingual school management platform developed as a graduation-project codebase. This folder is the **entry point for supervisors, evaluators, and developers** reviewing the system design, implementation, and thesis materials.

All documents were produced from a **full repository audit** (Django models, DRF viewsets, URLs, React routes, face-recognition microservice, chatbot, notifications, and localization). They describe what the software **actually does**, not a hypothetical specification.

---

## About the project

Smart School connects **administrators**, **teachers**, **students**, and **parents** through a single web application:

- **Role-based dashboards** with JWT authentication  
- **Face-recognition attendance** (teacher-led sessions + classroom photo capture)  
- **MCQ exams and grades** with automated low-grade alerts  
- **Subjects, classes, videos, and materials**  
- **Weekly analytics reports** (optional PDF export)  
- **In-app notifications** with WebSocket push  
- **AI chatbot** (Google Gemini with database-backed context and fallback)  
- **English / Arabic** support across API messages, database content, and the face service  

| Layer | Technology |
|-------|------------|
| Backend API | Django 5.2, Django REST Framework, SimpleJWT |
| Real-time | Django Channels + Daphne (WebSocket notifications) |
| Database | Microsoft SQL Server (`mssql-django`) |
| Frontend | React 19, Vite, Zustand, React Router 7 |
| Face service | FastAPI, `face_recognition`, OpenCV (default port **8001**) |
| AI | `google-generativeai` (optional `GEMINI_API_KEY`) |

Repository root: `smart-school-backend/` — application code lives alongside this `docs/` directory.

---

## Documentation map

| Document | Description |
|----------|-------------|
| [**project-overview.md**](./project-overview.md) | Executive summary: purpose, actors, repository layout, technology stack, feature inventory, authentication overview, and links to deeper docs. |
| [**srs.md**](./srs.md) | Software Requirements Specification: use case descriptions per role, functional requirements (ID-tagged), business rules, APIs/tables/screens per feature, and dedicated chapters on face attendance, chatbot, localization, and RBAC. |
| [**system-architecture.md**](./system-architecture.md) | Architecture views: high-level diagram, component and deployment descriptions, sequence flows (login, face attendance, face registration, chatbot, notifications), and security notes. |
| [**database-design.md**](./database-design.md) | Data model: ERD (Mermaid), entity relationships, full table catalog with columns and constraints, referential integrity, and translation-field notes. |
| [**api-documentation.md**](./api-documentation.md) | REST API reference: authentication, all Django endpoints and custom actions, request/response notes, face microservice API, WebSocket path, and error conventions. |
| [**user-manual.md**](./user-manual.md) | End-user guide by role: login, navigation, workflows (especially face attendance for teachers), troubleshooting, and screen-to-route mapping. |
| [**testing.md**](./testing.md) | Test strategy: automated localization suite, attendance integration script, manual checklists, frontend smoke tests, and gaps (CI, load tests). |
| [**thesis-outline.md**](./thesis-outline.md) | Suggested graduation thesis structure (9 chapters + appendices), diagram checklist, and cross-references to other docs. |
| [**localization.md**](./localization.md) | Deep dive on i18n: middleware, gettext messages, `django-modeltranslation`, face-service dictionary translations, and 51 localization tests. |

**Also in this folder (not part of the core set):**

| Document | Description |
|----------|-------------|
| [PROJECT_PROPOSAL.md](./PROJECT_PROPOSAL.md) | Earlier project proposal material (if present from planning phase). |

---

## Recommended reading order

### For supervisors and thesis evaluators (first review)

1. **[project-overview.md](./project-overview.md)** — scope and capabilities in ~10 minutes  
2. **[srs.md](./srs.md)** — requirements, use cases, and traceability (§5 for face AI, chatbot, i18n, RBAC)  
3. **[system-architecture.md](./system-architecture.md)** — how components interact; sequence diagrams for attendance  
4. **[database-design.md](./database-design.md)** — data model and integrity rules  
5. **[testing.md](./testing.md)** — what is verified and how to reproduce tests  
6. **[thesis-outline.md](./thesis-outline.md)** — how documentation maps to thesis chapters  

### For API / backend reviewers

1. [project-overview.md](./project-overview.md) §6–7  
2. [api-documentation.md](./api-documentation.md)  
3. [database-design.md](./database-design.md)  
4. [localization.md](./localization.md)  

### For UX / product evaluators

1. [user-manual.md](./user-manual.md)  
2. [srs.md](./srs.md) §2 (use cases)  
3. [project-overview.md](./project-overview.md) §5 (feature ↔ screen map)  

### For students writing the thesis

1. [thesis-outline.md](./thesis-outline.md)  
2. All core docs in chapter order (see thesis-outline cross-reference table)  
3. [localization.md](./localization.md) for Chapter 5/6 i18n depth  

---

## Quick links by topic

| Topic | Primary document | Supporting docs |
|-------|------------------|-----------------|
| Face recognition attendance | [srs.md §5.1](./srs.md), [system-architecture.md §4.2](./system-architecture.md) | [api-documentation.md §8](./api-documentation.md), [user-manual.md §3.1](./user-manual.md) |
| AI chatbot | [srs.md §5.2](./srs.md) | [api-documentation.md §13](./api-documentation.md) |
| English / Arabic | [localization.md](./localization.md), [srs.md §5.3](./srs.md) | [project-overview.md §7](./project-overview.md) |
| Role-based access | [srs.md §5.4](./srs.md) | [api-documentation.md](./api-documentation.md) (per-endpoint roles) |
| Weekly reports | [srs.md §3.8](./srs.md) | [api-documentation.md §10.2](./api-documentation.md) |
| Notifications | [srs.md §3.10](./srs.md) | [system-architecture.md §4.5](./system-architecture.md) |

---

## Project statistics (from codebase audit)

Figures below were extracted from the repository structure and source files (June 2026 audit).

| Metric | Count | Notes |
|--------|------:|-------|
| Django domain apps | **12** | `users`, `students`, `teachers`, `parents`, `subjects`, `classes`, `attendance`, `exams`, `reports`, `videos`, `notifications`, `chatbot` |
| Django ORM models | **19** | Including custom `User`; 18 domain models across apps |
| User roles | **4** | `ADMIN`, `TEACHER`, `STUDENT`, `PARENT` |
| API route modules | **12** | Under `/api/` via `smartSchool/urls.py` |
| DRF ViewSets (routers) | **17** | e.g. students, attendance-sessions, weekly-reports, video-progress |
| Custom `@action` endpoints | **27** | Dashboards, face register, process-classroom-image, weekly generate, etc. |
| Chatbot HTTP endpoints | **1** | `POST\|GET /api/chatbot/ask/` |
| Face microservice HTTP routes | **10** | FastAPI in `face_recognition_service/main.py` |
| WebSocket routes | **1** | `ws/notifications/` |
| React page components | **~35** | Under `frontend/app/src/pages/` |
| Supported UI languages | **2** | English (`en`), Arabic (`ar`) |
| Localization unit tests | **51** | `smartSchool/tests/test_localization.py` |
| Backend Python (approx.) | **~11,200** | Domain apps + `smartSchool` + face service |
| Frontend JS/JSX (approx.) | **~12,100** | `frontend/app/src/` |
| Database engine | **1** | Microsoft SQL Server |
| Face encoding storage | **Filesystem** | `face_recognition_service/face_encodings/*.pkl` (not in RDBMS) |

### Module ↔ documentation coverage

| Module | SRS section | API doc | User manual |
|--------|-------------|---------|-------------|
| Users & auth | §3.1 | §1–2 | §1 |
| Students | §3.2 | §3 | Admin §2.1, Student §4 |
| Teachers | §3.3 | §4 | §3 |
| Parents | §3.4 | §5 | §5 |
| Classes & subjects | §3.5 | §6–7 | §2–3 |
| Attendance | §3.6 | §8 | §3.1 |
| Exams & grades | §3.7 | §9 | §2–5 |
| Weekly reports | §3.8 | §10.2 | §2–5 |
| Videos | §3.9 | §11 | §3–4 |
| Notifications | §3.10 | §12 | §5.1 |
| Chatbot | §3.11 | §13 | §3.3, §5 |

---

## Running the system (evaluators)

Minimal services for a live demo:

| Service | Typical command / script | Port |
|---------|--------------------------|------|
| Django (ASGI) | `daphne smartSchool.asgi:application` or `runserver` | 8000 |
| Face recognition | `start_face_recognition_service.bat` / `.ps1` | 8001 |
| React dev server | `cd frontend/app && npm run dev` | 5173 (Vite) |
| SQL Server | Instance per `.env` / `settings.py` | — |

See [testing.md](./testing.md) for test commands and [user-manual.md](./user-manual.md) §8 for troubleshooting.

---

## Document conventions

- **TODO** markers appear only where information cannot be inferred from code (e.g. production hostnames, formal SLAs, UAT survey results).  
- Diagrams in architecture docs are **textual descriptions** suitable for redraw in PlantUML, draw.io, or thesis tools.  
- API paths are relative to `/api/` unless noted (face service uses its own base URL).  

---

## Suggested citation (thesis appendix)

> *Smart School Backend — Technical Documentation Set.* Repository: `smart-school-backend/docs/`. Audit date: June 2026. Documents: project-overview, srs, system-architecture, database-design, api-documentation, user-manual, testing, thesis-outline, localization.

---

## Graduation report (PDF)

A full **40–60 page** graduation-project report is generated from this documentation set:

| Output | Path |
|--------|------|
| **Smart School Management System** (PDF) | [pdf/SmartSchool_Thesis_Report.pdf](./pdf/SmartSchool_Thesis_Report.pdf) |

**Regenerate after doc or code changes:**

```bash
python docs/scripts/generate_thesis_pdf.py
```

The PDF includes: Abstract, Introduction, Problem Statement, Objectives, Literature Review, System Analysis, Requirements, Design, Database, Architecture, API, Face Recognition, AI Chatbot, Localization, Testing, Results, Future Work, Conclusion, References, and appendices (statistics, module reference, SRS/API/user-manual excerpts).

---

## Feedback and updates

When the implementation changes, update the affected document(s), refresh the statistics table in this README, and re-run `docs/scripts/generate_thesis_pdf.py`. The **source of truth** remains the application code; these files are derived documentation.

**Contact for institutional submission:** TODO — add supervisor name, department, and submission date as required by your university.
