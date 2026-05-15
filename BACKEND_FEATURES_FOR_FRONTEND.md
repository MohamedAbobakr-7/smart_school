# Backend Features for Frontend

## Base URL
- API base: `/api/`
- API root (اختياري للاكتشاف): `/`

## Authentication & Session
- `POST /api/auth/login/`
  - Login بـ `username` + `password`
  - بيرجع `access` و `refresh` + بيانات المستخدم (حسب serializer الحالي)
- `POST /api/auth/refresh/`
  - تجديد الـ access token

### Frontend Notes
- ابعت `Authorization: Bearer <access_token>` في كل requests المحمية.
- عند `401` اعمل refresh ثم retry request.

---

## Users
- `GET /api/users/` (list)
- `GET /api/users/{id}/` (details)
- `POST /api/users/` (create - admin)
- `PUT/PATCH /api/users/{id}/` (update - admin)
- `DELETE /api/users/{id}/` (delete - admin)
- `GET /api/users/me/`
- `GET /api/users/by_role/?role=ADMIN|TEACHER|STUDENT|PARENT` (admin)

### Frontend Features
- شاشة Profile الحالية من `/api/users/me/`
- فلترة المستخدمين حسب الدور للـ admin panel

---

## Students / Teachers / Parents / Subjects

### Students
- `GET /api/students/`
- `GET /api/students/{id}/`
- `POST /api/students/` (admin/teacher)
- `PUT/PATCH /api/students/{id}/` (admin/teacher)
- `DELETE /api/students/{id}/` (admin/teacher)

### Teachers
- `GET /api/teachers/`
- `GET /api/teachers/{id}/`
- `POST /api/teachers/` (admin)
- `PUT/PATCH /api/teachers/{id}/` (admin)
- `DELETE /api/teachers/{id}/` (admin)

### Parents
- `GET /api/parents/`
- `GET /api/parents/{id}/`
- `POST /api/parents/` (admin)
- `PUT/PATCH /api/parents/{id}/` (admin)
- `DELETE /api/parents/{id}/` (admin)

### Subjects
- `GET /api/subjects/`
- `GET /api/subjects/{id}/`
- `POST /api/subjects/` (admin/teacher)
- `PUT/PATCH /api/subjects/{id}/` (admin/teacher)
- `DELETE /api/subjects/{id}/` (admin/teacher)

### Frontend Features
- CRUD شاشات الإدارة
- Role-based visibility لكل شاشة حسب user role

---

## Attendance

### Attendance Records
- `GET /api/attendance/`
- `GET /api/attendance/{id}/`
- `POST /api/attendance/`
- `PUT/PATCH /api/attendance/{id}/`
- `DELETE /api/attendance/{id}/`

### Attendance Sessions
- `GET /api/attendance-sessions/`
- `GET /api/attendance-sessions/{id}/`
- `POST /api/attendance-sessions/` (teacher/admin)
- `PUT/PATCH /api/attendance-sessions/{id}/`
- `DELETE /api/attendance-sessions/{id}/`
- `POST /api/attendance-sessions/{id}/complete/`
- `POST /api/attendance-sessions/{id}/cancel/`

### Face Recognition (batch classroom image)
- `POST /api/attendance/process-classroom-image/`
  - `multipart/form-data`
  - fields:
    - `session_id`
    - `image`

### Frontend Features
- شاشة تشغيل Session للحصة
- زر upload/camera لصورة الفصل
- عرض نتيجة المطابقة:
  - عدد الوجوه
  - عدد الطلبة المتسجلين حضور
  - قائمة المطابقات

---

## Exams / Questions / Grades

### Exams
- `GET /api/exams/`
- `GET /api/exams/{id}/`
- `POST /api/exams/` (admin/teacher)
- `PUT/PATCH /api/exams/{id}/`
- `DELETE /api/exams/{id}/`

### Questions
- `GET /api/questions/`
- `GET /api/questions/{id}/`
- `POST /api/questions/` (admin/teacher)
- `PUT/PATCH /api/questions/{id}/`
- `DELETE /api/questions/{id}/`

### Grades
- `GET /api/grades/`
- `GET /api/grades/{id}/`
- `POST /api/grades/` (admin/teacher)
- `PUT/PATCH /api/grades/{id}/`
- `DELETE /api/grades/{id}/`

### Frontend Features
- إدارة الامتحانات والأسئلة
- إدخال الدرجات
- صفحات الطالب/ولي الأمر لعرض الدرجات (حسب الصلاحيات)

---

## Reports

### Student Reports
- `GET /api/reports/`
- `GET /api/reports/{id}/`
- `POST /api/reports/` (admin/teacher)
- `PUT/PATCH /api/reports/{id}/`
- `DELETE /api/reports/{id}/`

### Weekly Reports (analytics snapshots)
- `GET /api/weekly-reports/`
- `GET /api/weekly-reports/{id}/`
- `GET /api/weekly-reports/dashboard/?weeks=8`
- `POST /api/weekly-reports/generate/`
- `GET /api/weekly-reports/{id}/download-pdf/`

### Frontend Features
- Dashboard charts من `weekly-reports/dashboard`
- زر generate report (admin/teacher)
- زر download PDF لكل weekly report

---

## Videos

### Video Catalog
- `GET /api/videos/`
  - filters supported:
    - `?subject=<id>`
    - `?category=<value>`
- `GET /api/videos/{id}/`
- `POST /api/videos/` (admin/teacher)
- `PUT/PATCH /api/videos/{id}/` (owner teacher أو admin)
- `DELETE /api/videos/{id}/` (owner teacher أو admin)

### Video Streaming
- `GET /api/videos/{id}/stream/?access=<JWT>`
  - يدعم Range requests

### Video Progress
- `GET /api/video-progress/`
- `GET /api/video-progress/{id}/`
- `POST /api/video-progress/sync/` (student only)

### Frontend Features
- Video player + seek resume
- حفظ تقدم المشاهدة كل فترة (sync)
- صفحة teacher لمتابعة progress

---

## Notifications

### REST
- `GET /api/notifications/`
  - filters:
    - `?unread=true`
    - `?type=<notification_type>`
- `GET /api/notifications/{id}/`
- `POST /api/notifications/{id}/mark-read/`
- `POST /api/notifications/mark-all-read/`
- `GET /api/notification-preferences/`
- `PUT/PATCH /api/notification-preferences/`

### WebSocket (real-time)
- endpoint: `/ws/notifications/?access=<JWT>`
- كل user بينضم لجروب خاص به، وبيوصله push notifications مباشرة

### Frontend Features
- Notification bell + unread badge
- real-time toast/in-app alerts من websocket
- صفحة preferences لتفعيل/إيقاف أنواع الإشعارات

---

## Suggested Frontend Implementation Order
1. Auth flow (login + refresh + protected routes)
2. Profile + role-based navigation (`/api/users/me/`)
3. Dashboard analytics (`/api/weekly-reports/dashboard/`)
4. Notifications (REST first, then WebSocket)
5. Core CRUD (students/teachers/subjects/exams/grades)
6. Attendance sessions + classroom image processing
7. Videos + stream + progress sync
8. Reports + PDF download

---

## Quick Checklist (Frontend)
- Token storage + refresh strategy
- Centralized API client + interceptor
- Role guards (admin/teacher/student/parent)
- Loading/error empty states لكل module
- Realtime socket reconnect handling
- Pagination/search/filter UI where needed

