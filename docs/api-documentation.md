# API Documentation

> Base URL (development): `http://127.0.0.1:8000/api/`  
> Authentication: `Authorization: Bearer <access_token>` unless noted.  
> Language: `Accept-Language: en|ar` or `?lang=ar`  
> Pagination: `PageNumberPagination`, `page_size=20` default.

---

## 1. Authentication

| Method | Path | Auth | Body / params | Response |
|--------|------|------|---------------|----------|
| POST | `/auth/login/` | No | `{ "username", "password" }` | `{ access, refresh, user }` |
| POST | `/auth/refresh/` | No | `{ "refresh" }` | New tokens |

**Login notes:**

- `username` may be a student's `student_id` if no matching username exists.
- `user` includes `role`, `role_display`, optional `student_id`, `photo_url`.

---

## 2. Users

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/users/` | Auth (filtered) | List users |
| POST | `/users/` | ADMIN | Create user |
| GET/PATCH/DELETE | `/users/{id}/` | ADMIN / self rules | User detail |
| GET/PATCH | `/users/me/` | Auth | Current profile + role profiles |
| GET | `/users/by_role/?role=TEACHER` | ADMIN | Filter by role |
| GET | `/users/admin-dashboard/` | ADMIN | School KPIs, charts |

---

## 3. Students

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET/POST | `/students/` | Auth / Admin+Teacher write | List/create; filters: `class_id`, `parent_id`, `subject_id` |
| GET/PATCH/DELETE | `/students/{id}/` | Scoped | Student detail |
| POST | `/students/backfill-ids/` | ADMIN | Auto-assign missing `student_id` |
| GET | `/students/all-stats/` | ADMIN | Per-student attendance/grade aggregates |
| GET | `/students/weekly-report/` | STUDENT | Weekly analytics; `?week_start=&week_end=` |
| GET | `/students/dashboard/` | STUDENT | Student dashboard KPIs |
| POST | `/students/{id}/register-face/` | Admin+Teacher | Multipart `photo` → face service |
| GET | `/students/{id}/face-status/` | Auth | DB + service face status |

---

## 4. Teachers

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET/POST | `/teachers/` | Admin+Teacher read; Admin write | |
| GET/PATCH/DELETE | `/teachers/{id}/` | Admin write | |
| GET | `/teachers/dashboard/` | TEACHER | Teacher dashboard metrics |

---

## 5. Parents

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET/POST | `/parents/` | Auth read; Admin write | |
| GET/PATCH/DELETE | `/parents/{id}/` | | |
| GET | `/parents/dashboard/` | PARENT | Children KPIs + chatbot hints |

---

## 6. Classes

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET/POST | `/classes/` | Auth | `SchoolClass` CRUD |
| GET/PATCH/DELETE | `/classes/{id}/` | | |

---

## 7. Subjects & Materials

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET/POST | `/subjects/` | Auth | Subject CRUD |
| GET/PATCH/DELETE | `/subjects/{id}/` | | |
| GET/POST | `/materials/` | Auth | File upload material |
| GET/PATCH/DELETE | `/materials/{id}/` | | |

---

## 8. Attendance

### 8.1 Attendance records

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/attendance/` | Auth (scoped) | List records |
| POST | `/attendance/` | TEACHER | Create; **upserts** if same student+date exists |
| GET/PATCH/DELETE | `/attendance/{id}/` | TEACHER write | |
| POST | `/attendance/process-classroom-image/` | TEACHER | Multipart: `session_id`, `image` |

**process-classroom-image response (success):**

```json
{
  "success": true,
  "session_id": 1,
  "num_faces_detected": 5,
  "num_matches": 3,
  "matched_students": ["STU001"],
  "skipped_class_mismatch": [],
  "matches": [],
  "roster": { "present": [], "absent": [] },
  "message": "..."
}
```

### 8.2 Attendance sessions

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET/POST | `/attendance-sessions/` | Admin+Teacher read; Teacher write | |
| GET/PATCH/DELETE | `/attendance-sessions/{id}/` | | |
| GET | `/attendance-sessions/active/` | Admin+Teacher | `{ active, session }` |
| GET | `/attendance-sessions/{id}/roster/` | Admin+Teacher | Present/absent lists |
| POST | `/attendance-sessions/{id}/complete/` | TEACHER | Completes; parent absence notifications |
| POST | `/attendance-sessions/{id}/cancel/` | TEACHER | |
| GET | `/attendance-sessions/{id}/history/` | Admin+Teacher | Full class roster + status |
| GET | `/attendance-sessions/class-history/` | Admin+Teacher | `?school_class=&status=` |

---

## 9. Exams, Questions, Grades

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET/POST | `/exams/` | Auth read; Admin+Teacher write | |
| GET | `/exams/upcoming/` | STUDENT | Exams not yet taken in enrolled subjects |
| GET/PATCH/DELETE | `/exams/{id}/` | | Detail uses `ExamDetailSerializer` |
| GET/POST | `/questions/` | Auth / Admin+Teacher write | |
| GET/POST | `/grades/` | Auth scoped / Admin+Teacher write | |

---

## 10. Reports

### 10.1 Student reports

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET/POST | `/reports/` | Auth scoped / Admin+Teacher write | Academic/behavioral reports |

### 10.2 Weekly reports

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/weekly-reports/` | Admin; Teacher (school + own) | List snapshots |
| GET | `/weekly-reports/{id}/` | | Detail |
| GET | `/weekly-reports/dashboard/?weeks=8` | Admin+Teacher | Trend + latest |
| POST | `/weekly-reports/generate/` | Admin+Teacher | Body: `scope`, `week_start`, `week_end`, `write_pdf`, `all_teachers` |
| GET | `/weekly-reports/{id}/download-pdf/` | Admin+Teacher | PDF file download |

**Generate body example:**

```json
{
  "scope": "SCHOOL",
  "week_start": "2026-05-26",
  "week_end": "2026-06-01",
  "write_pdf": true,
  "all_teachers": false
}
```

---

## 11. Videos

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET/POST | `/videos/` | Auth | Teacher upload; students read published |
| GET/PATCH/DELETE | `/videos/{id}/` | | |
| GET/POST | `/video-progress/` | STUDENT | Watch progress |
| POST | `/video-progress/sync/` | STUDENT | Batch sync positions |

---

## 12. Notifications

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/notifications/` | Auth | `?unread=true`, `?type=LOW_GRADE` |
| GET | `/notifications/{id}/` | Auth | |
| POST | `/notifications/{id}/mark-read/` | Auth | |
| POST | `/notifications/mark-all-read/` | Auth | `{ marked_read: N }` |
| GET/PATCH | `/notification-preferences/` | Auth | User toggles |

**WebSocket:** `ws://host/ws/notifications/` — JWT in connection (see `notifications/middleware.py`).

---

## 13. Chatbot

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| POST | `/chatbot/ask/` | Auth | `{ "message": "..." }` max 500 chars |
| GET | `/chatbot/ask/` | Auth | `{ greeting, suggestions }` |

**POST response:**

```json
{
  "reply": "...",
  "suggestions": ["My grades", "..."],
  "intent": "grades"
}
```

---

## 14. Face Recognition Microservice

Base URL: `FACE_RECOGNITION_SERVICE_URL` (default `http://localhost:8001`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info |
| POST | `/verify-face?student_id=` | Single face verify (multipart `image`) |
| POST | `/register-face?student_id=` | Register encoding |
| GET | `/students/{student_id}/face-status` | Registration status |
| POST | `/detect-faces-batch` | Batch detect; query: `tolerance`, `model`, `num_jitters`, `student_ids` |
| GET | `/encodings` | List all encodings |
| DELETE | `/encodings/{student_id}` | Delete encoding |
| GET | `/encodings/{student_id}/validate` | Integrity check |
| POST | `/encodings/{student_id}/update` | Re-register face |

Called by Django only (not directly by React in production flow).

---

## 15. Root & Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` (non-api) | `api_root` JSON welcome |
| * | `/admin/` | Django admin |

---

## 16. Error Handling

- DRF standard: `{ "detail": "..." }` or field errors.
- Localized messages from `smartSchool.messages` when middleware language is `ar`.
- Face/attendance endpoints often return `{ "success": false, "message", "error" }` with 4xx/5xx.

---

## 17. Standard ViewSet Operations

For each router-registered resource, DRF provides unless overridden:

- `GET /resource/` — list
- `POST /resource/` — create
- `GET /resource/{id}/` — retrieve
- `PUT/PATCH /resource/{id}/` — update
- `DELETE /resource/{id}/` — destroy

Permissions vary per viewset; see [srs.md](./srs.md).

---

## 18. TODO

- OpenAPI/Swagger schema generation is **not** present in the repo. **TODO:** Add `drf-spectacular` or export Postman collection if required for thesis appendix.
