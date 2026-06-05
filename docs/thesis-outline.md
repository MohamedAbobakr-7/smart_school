# Graduation Thesis Outline

> Suggested chapter structure aligned with the Smart School implementation documented in this repository.  
> Expand each section with screenshots, diagrams (from [system-architecture.md](./system-architecture.md)), and evaluation results.

---

## Front Matter

- Title page (institution name — **TODO:** insert official title format)
- Abstract (English)
- Abstract (Arabic) — **recommended** given bilingual scope
- Acknowledgments
- Table of contents
- List of figures and tables

---

## Chapter 1 — Introduction

1.1 Background and motivation for smart school systems  
1.2 Problem statement (manual attendance, fragmented parent communication, language barriers)  
1.3 Objectives  
1.4 Scope and limitations (four roles, MCQ exams, SQL Server, face service dependency)  
1.5 Thesis organization  

**Sources:** [project-overview.md](./project-overview.md)

---

## Chapter 2 — Literature Review & Related Work

2.1 School information systems and LMS  
2.2 Biometric and face-recognition attendance in education  
2.3 Conversational AI in educational dashboards  
2.4 Multilingual software design (RTL, gettext, content translation)  
2.5 Comparative analysis table (commercial vs this project)  

**TODO:** Add peer-reviewed citations per your university requirements.

---

## Chapter 3 — Requirements Analysis

3.1 Stakeholder identification (admin, teacher, student, parent)  
3.2 Functional requirements ([srs.md](./srs.md) sections 3.x)  
3.3 Non-functional requirements (security, i18n, performance)  
3.4 Use case diagrams (draw from [srs.md](./srs.md) §2)  
3.5 Requirements traceability matrix  

---

## Chapter 4 — System Design

4.1 Overall architecture ([system-architecture.md](./system-architecture.md) §1–2)  
4.2 Component diagram  
4.3 Deployment diagram (dev vs proposed production)  
4.4 Database design ([database-design.md](./database-design.md))  
4.5 API design overview ([api-documentation.md](./api-documentation.md))  
4.6 Security and role-based access control ([srs.md](./srs.md) §5.4)  

---

## Chapter 5 — Implementation

5.1 Technology stack justification (Django, React, FastAPI, SQL Server)  
5.2 Backend implementation (apps, JWT, Channels)  
5.3 Frontend implementation (routing, state, API client)  
5.4 **Face recognition attendance subsystem** (registration, sessions, batch match)  
5.5 **AI chatbot subsystem** (intent, context, Gemini integration)  
5.6 **Localization subsystem** (middleware, modeltranslation, face service dict)  
5.7 Notifications and real-time delivery  
5.8 Weekly analytics and PDF generation  

**Include:** Selected code listings with line references from repository.

---

## Chapter 6 — Dedicated Feature Deep Dives (Integrative)

*Can be merged into Chapter 5 or kept separate per advisor preference.*

6.1 Face Recognition Attendance — algorithms (HOG, tolerance 0.6), class filtering, privacy  
6.2 AI Chatbot — prompt design, hallucination controls, fallback behavior  
6.3 English/Arabic localization — three-layer model (API, DB, microservice)  
6.4 RBAC — permission matrix by endpoint  

---

## Chapter 7 — Testing & Evaluation

7.1 Test strategy ([testing.md](./testing.md))  
7.2 Unit and localization test results (`test_localization.py`)  
7.3 Integration test: automated attendance script  
7.4 User acceptance / survey results — **TODO:** conduct and insert scores  
7.5 Performance measurements (face batch latency, API response times) — **TODO:** benchmark data  
7.6 Discussion of limitations (in-memory Channels, DEBUG=True in settings)  

---

## Chapter 8 — Results & Discussion

8.1 Objectives achievement checklist  
8.2 Comparison: before vs after (manual attendance time, parent notification delay) — **TODO:** empirical study  
8.3 Lessons learned  
8.4 Ethical considerations (biometric data storage, consent)  

---

## Chapter 9 — Conclusion & Future Work

9.1 Summary of contributions  
9.2 Future enhancements:
- Production channel layer (Redis)
- Full React i18n coverage and RTL layout
- OpenAPI documentation
- Mobile app
- Liveness detection for face anti-spoofing
- Exam taking UI for students (currently grade entry by teacher)

---

## Appendices

| Appendix | Content |
|----------|---------|
| A | Full API endpoint list ([api-documentation.md](./api-documentation.md)) |
| B | Database schema / ERD printout |
| C | User manual excerpts ([user-manual.md](./user-manual.md)) |
| D | Installation and deployment guide (from README, `start_face_recognition_service.bat`) |
| E | Sample weekly report PDF |
| F | Chatbot example transcripts |
| G | Localization `.po` excerpt |

---

## Diagram Checklist for Thesis

| Diagram | Source description |
|---------|-------------------|
| Use case (4 actors) | [srs.md](./srs.md) §2 |
| ERD | [database-design.md](./database-design.md) §2 |
| Sequence: login | [system-architecture.md](./system-architecture.md) §4.1 |
| Sequence: face attendance | [system-architecture.md](./system-architecture.md) §4.2 |
| Component | [system-architecture.md](./system-architecture.md) §2 |
| Deployment | [system-architecture.md](./system-architecture.md) §3 |
| Activity: attendance session | Derive from teacher manual §3.1 |

---

## Suggested Page Count Guidance

| Chapter | Approx. pages (undergraduate) |
|---------|-------------------------------|
| 1–2 | 15–20 |
| 3 | 12–18 |
| 4 | 15–20 |
| 5–6 | 25–35 |
| 7–8 | 15–20 |
| 9 + appendices | 10–15 + appendices |

**TODO:** Confirm required length with your department.

---

## Cross-Reference Index

| Thesis topic | Primary doc |
|--------------|-------------|
| Features list | project-overview.md |
| Business rules | srs.md |
| Architecture | system-architecture.md |
| Tables & ERD | database-design.md |
| REST API | api-documentation.md |
| End users | user-manual.md |
| Tests | testing.md |
| i18n detail | localization.md |
