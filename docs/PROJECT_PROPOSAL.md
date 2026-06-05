# Project Proposal: Smart School Management System

## 1. Project Title

**Smart School Management System with AI-Powered Face Recognition Attendance**

## 2. Project Team

| Role | Name |
|------|------|
| Developer | Mohamed Abobakr |
| Supervisor | TODO: Add supervisor name |
| Institution | TODO: Add university/institution name |
| Department | TODO: Add department name |
| Academic Year | 2025-2026 |

## 3. Problem Statement

Traditional school management relies on manual processes for attendance tracking, grade management, report generation, and parent-teacher communication. These methods are:

- **Time-consuming**: Manual roll calls consume 5-10 minutes per class session
- **Error-prone**: Human errors in attendance marking and grade recording
- **Disconnected**: Parents lack real-time visibility into their children's academic performance
- **Non-scalable**: Paper-based systems cannot support data analytics or trend detection
- **Insecure**: Manual attendance is easily falsified (proxy attendance)

## 4. Proposed Solution

A comprehensive web-based Smart School Management System that integrates:

1. **AI-Powered Face Recognition Attendance** - Automated, fraud-proof attendance using deep learning (dlib ResNet CNN producing 128-dimensional face encodings)
2. **Role-Based Dashboard Platform** - Separate interfaces for Admin, Teacher, Student, and Parent roles
3. **Intelligent Chatbot** - Google Gemini-powered conversational assistant with intent detection
4. **Real-Time Notifications** - WebSocket-based instant alerts for attendance, grades, and reports
5. **Bilingual Interface** - Full English/Arabic localization with RTL support
6. **Analytics & Reporting** - Automated weekly performance reports with PDF export

## 5. Project Objectives

### Primary Objectives
1. Develop an AI-based face recognition system achieving >95% accuracy for automated attendance
2. Implement a secure, role-based web platform serving four user roles
3. Integrate real-time notification system for parent engagement
4. Provide data-driven weekly analytics reports

### Secondary Objectives
1. Support bilingual (EN/AR) interface with full RTL layout
2. Implement video streaming for educational content delivery
3. Build an AI chatbot for natural language queries about school data
4. Generate automated PDF reports for school administration

## 6. Scope

### In Scope
- User authentication and authorization (JWT-based)
- Student, Teacher, Parent, and Admin management
- Face registration and recognition for attendance
- Manual and AI-based attendance tracking
- Exam creation (MCQ) with automated grading
- Educational materials and video upload/streaming
- Real-time WebSocket notifications
- AI chatbot (Google Gemini integration)
- Weekly analytics reports with PDF export
- Bilingual UI (English/Arabic)
- Dark/Light theme support

### Out of Scope
- Mobile native application (future work)
- SMS/Email notification delivery
- Payment/Fee management
- Timetable/Schedule management
- Live video conferencing
- Biometric methods other than face recognition

## 7. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | React | 19.2.4 |
| State Management | Zustand | 5.0.12 |
| Routing | React Router | 7.14.1 |
| Charts | Recharts | 3.8.1 |
| i18n | i18next | 26.2.0 |
| Build Tool | Vite | 5.4.10 |
| Backend API | Django REST Framework | 3.15+ |
| Backend Framework | Django | 5.2.10 |
| WebSocket | Django Channels | - |
| AI Service | FastAPI | 0.104+ |
| Face Recognition | face_recognition (dlib) | 1.3+ |
| Computer Vision | OpenCV | 4.8+ |
| AI Chatbot | Google Gemini API | - |
| Database | MS SQL Server | Express |
| Authentication | JWT (Simple JWT) | - |
| PDF Generation | ReportLab/WeasyPrint | - |

## 8. System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                         │
│         (Vite + Zustand + React Router + i18next)        │
└────────────────┬────────────────────┬───────────────────┘
                 │ REST API            │ WebSocket
                 ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│              Django REST Backend                          │
│    (DRF + Channels + JWT + Role-Based Permissions)       │
└────────┬───────────────┬────────────────┬───────────────┘
         │               │                │
         ▼               ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│  MS SQL      │ │ Google       │ │ FastAPI Face          │
│  Server DB   │ │ Gemini API   │ │ Recognition Service   │
└──────────────┘ └──────────────┘ └──────────────────────┘
```

## 9. Project Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Analysis & Design | 3 weeks | SRS, ERD, Architecture Design |
| Phase 2: Backend Core | 4 weeks | User auth, Models, REST APIs |
| Phase 3: Frontend Development | 4 weeks | React UI, Role dashboards |
| Phase 4: AI Integration | 3 weeks | Face recognition, Chatbot |
| Phase 5: Testing & Refinement | 2 weeks | Testing, Bug fixes |
| Phase 6: Documentation | 2 weeks | Thesis, User manual |
| **Total** | **18 weeks** | |

## 10. Expected Outcomes

1. Fully functional web-based school management system
2. AI attendance system reducing roll-call time by >90%
3. Real-time parent engagement through notifications and chatbot
4. Data-driven decision making through automated analytics
5. Bilingual platform accessible to Arabic-speaking communities

## 11. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Face recognition accuracy in varied lighting | Medium | High | HOG + CNN dual model, configurable tolerance |
| Database performance with large datasets | Low | Medium | Indexed queries, pagination |
| WebSocket connection reliability | Medium | Low | REST polling fallback with exponential backoff |
| Browser camera API compatibility | Medium | Medium | Fallback to manual frame capture |
| Google Gemini API availability | Low | Low | Smart fallback responses without AI |

## 12. References

- Dlib Face Recognition: King, D.E. (2009). "Dlib-ml: A Machine Learning Toolkit"
- Django REST Framework: https://www.django-rest-framework.org/
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- face_recognition library: https://github.com/ageitgey/face_recognition
