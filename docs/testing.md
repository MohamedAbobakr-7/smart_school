# Testing Documentation

> Test assets and procedures identified in the repository audit.

---

## 1. Test Inventory

| Category | Location | Description |
|----------|----------|-------------|
| Localization (Django) | `smartSchool/tests/test_localization.py` | 51 tests: middleware, messages, model choices, face translations |
| App unit tests (stubs) | `*/tests.py` in apps | Mostly placeholder `tests.py` files — **minimal coverage** |
| Integration script | `test_automated_attendance.py` | End-to-end face attendance workflow |
| Manual guides | `TESTING_GUIDE.md`, `QUICK_START_FACE_REGISTRATION.md` | Human-driven test procedures |
| Face service | No automated pytest in `face_recognition_service/` | Manual HTTP testing |

---

## 2. Running Django Tests

From project root with virtual environment activated:

```bash
python manage.py test
```

### Localization suite only

```bash
python manage.py test smartSchool.tests.test_localization
```

**Covers:**

- `APILanguageMiddleware` — `?lang=`, `Accept-Language`, fallback
- `smartSchool.messages` — EN/AR strings
- Model choice label translation
- `.po` completeness and compiled `.mo`
- `face_recognition_service/translations.py` — `get_message`, `resolve_lang`

---

## 3. Automated Attendance Integration Test

**File:** `test_automated_attendance.py`

**Prerequisites:**

1. Django on `http://localhost:8000`
2. FastAPI face service on `http://localhost:8001`
3. Test data: `python manage.py create_test_data` (referenced in script comments)
4. Instructor credentials (default `teacher1` / `teacher123`)
5. Classroom image path configured in `TEST_IMAGE_PATH`

**Run:**

```bash
python test_automated_attendance.py
```

**Steps exercised:**

1. Instructor JWT login
2. FastAPI batch detection (optional direct call)
3. Create attendance session
4. `POST /api/attendance/process-classroom-image/`
5. Complete session
6. Verify attendance records

---

## 4. Manual Test Checklists

### 4.1 Authentication & RBAC

| # | Step | Expected |
|---|------|----------|
| 1 | Login as each role | Redirect to correct `/admin|teacher|student|parent` |
| 2 | Student login with `student_id` | Success when ID exists |
| 3 | Access other role URL | `/unauthorized` |
| 4 | Call API without token | 401 |

### 4.2 Face attendance

| # | Step | Expected |
|---|------|----------|
| 1 | Register face for student with photo + `student_id` | `face_registered=true` |
| 2 | Start session for class | All students absent |
| 3 | Upload class photo with known faces | Matched students → present |
| 4 | Complete session | Absent students' parents notified |
| 5 | Student from other class in photo | Listed in `skipped_class_mismatch` |

### 4.3 Exams & notifications

| # | Step | Expected |
|---|------|----------|
| 1 | Create grade below 60% | LOW_GRADE notification to student, parent, relevant teachers |
| 2 | Mark student absent | ATTENDANCE notification (signal on save) |

### 4.4 Chatbot

| # | Step | Expected |
|---|------|----------|
| 1 | Ask "my attendance" as student | Intent `attendance`, contextual reply |
| 2 | Without `GEMINI_API_KEY` | Fallback text with data, no crash |

### 4.5 Weekly reports

| # | Step | Expected |
|---|------|----------|
| 1 | Admin POST generate SCHOOL scope | `WeeklyReport` status READY |
| 2 | GET dashboard `?weeks=8` | Trend array populated |

### 4.6 Localization

| # | Step | Expected |
|---|------|----------|
| 1 | API with `Accept-Language: ar` | Arabic choice labels / messages |
| 2 | Face service with `Accept-Language: ar` | Arabic error/success messages |

---

## 5. Frontend Testing

**Configured:** ESLint (`npm run lint` in `frontend/app/`).

**Not configured in repo:** Jest, Vitest, Cypress, Playwright.

**Manual smoke:**

```bash
cd frontend/app
npm run dev
```

Verify login, navigation per role, attendance camera permission, notifications page load.

---

## 6. WebSocket Testing

1. Start ASGI server (Daphne): required for WebSockets.
2. Connect client to `ws://127.0.0.1:8000/ws/notifications/` with valid JWT.
3. Trigger notification (e.g. save low grade).
4. Confirm push payload received.

**TODO:** Add automated Channels consumer test if thesis requires measurable WebSocket coverage.

---

## 7. Performance & Load

**TODO:** Define load test scenarios (concurrent attendance uploads, chatbot rate limits). Not implemented in repository.

Face batch endpoint default timeout: **120 seconds** (`FACE_RECOGNITION_BATCH_TIMEOUT`).

---

## 8. CI/CD

**TODO:** Document CI pipeline if GitHub Actions or similar is added. No `.github/workflows` found in audit.

---

## 9. Test Data Management

| Command / script | Purpose |
|------------------|---------|
| `python manage.py create_test_data` | Referenced by attendance test script |
| `python manage.py backfill_student_ids` | Student ID backfill command |
| `python manage.py generate_weekly_reports` | Batch weekly report generation |

---

## 10. Defect Reporting Template (Thesis appendix)

| Field | Value |
|-------|-------|
| ID | |
| Role / screen | |
| Steps to reproduce | |
| Expected (per SRS) | |
| Actual | |
| API response / logs | |
| Severity | |

---

## 11. Related Documentation

- [srs.md](./srs.md) — requirements traceability
- [api-documentation.md](./api-documentation.md) — endpoint contracts
- [localization.md](./localization.md) — i18n test details
