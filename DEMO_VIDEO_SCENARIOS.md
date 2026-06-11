# 🎬 Smart School — Demo Video Scenarios Guide

> Follow these scenarios step-by-step while recording to produce a compelling, complete demo video.

---

## 📋 Pre-Recording Checklist

| Item | Details |
|------|---------|
| **Backend** | Django server running (`python manage.py runserver`) |
| **Face Service** | Face recognition service running (`start_face_recognition_service.bat`) |
| **Frontend** | React app running (`npm run dev`) |
| **Seed Data** | At least 2–3 students per class, 1 teacher, 1 parent, exams with grades |
| **Browser** | Chrome/Edge (for FaceDetector API support in attendance camera) |
| **Screen Resolution** | 1920×1080 or higher — record in full-screen mode |
| **Recording Tool** | OBS Studio, Loom, or built-in screen recorder |
| **Language** | Start in **English**, then switch to **Arabic** mid-demo to show i18n |

---

## 🎞️ Scenario 1 — Login & Language Switch (≈ 30 sec)

**Purpose:** Show authentication flow and bilingual support.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Open browser to the login page | "Smart School — a unified platform for admins, teachers, students, and parents." |
| 2 | Click the **Language Selector** (🌐) and switch to **Arabic** | "Full Arabic and English support — all labels, messages, and data adapt instantly." |
| 3 | Switch back to **English** | Point out that every page respects the chosen language. |
| 4 | Type **admin** credentials and click **Login** | "Let's start as the school administrator." |
| 5 | Show the redirect to `/admin` dashboard | "Each role lands on their own tailored dashboard." |

---

## 🎞️ Scenario 2 — Admin Dashboard Overview (≈ 45 sec)

**Purpose:** Show the admin's bird's-eye view of the entire school.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Show the **4 stat cards**: Total Students, Total Teachers, Total Classes, Attendance Rate | "The admin dashboard gives an instant snapshot — students, teachers, classes, and this week's attendance." |
| 2 | Hover over the **Attendance Rate** card — show the hint tooltip | "Contextual hints explain every metric." |
| 3 | Scroll down to the **Area Chart** (attendance trend over weeks) | "Trends over time help spot patterns — is attendance improving or declining?" |
| 4 | Show the **Bar Chart** (grade distribution or subject comparison) | "Compare performance across subjects and grades." |
| 5 | Scroll to **Recent Activity** feed | "Recent exams, new enrollments, and alerts — all in one place." |
| 6 | Open the **Sidebar** — show all admin navigation items | "Full management access: students, teachers, parents, subjects, classes, exams, weekly reports." |

---

## 🎞️ Scenario 3 — Admin Manages Students (≈ 1 min)

**Purpose:** Show CRUD operations on the most important entity.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Click **Students** in sidebar → `/admin/students` | "The admin can manage all student records." |
| 2 | Show the **student table** with search bar and class filter | "Search by name or filter by class — instant results." |
| 3 | Use the **Class Filter** dropdown → select a class | "Filtering narrows down to just one class." |
| 4 | Click **+ Add Student** button → fill in the modal (name, email, class, parent, photo) | "Adding a student is one click — assign class, link parent, even upload a photo for face recognition." |
| 5 | Upload a **student photo** in the create modal | "This photo registers the student's face for automated attendance." |
| 6 | Click **Save** → show the new student appearing in the table | "The student appears instantly in the list." |
| 7 | Click the **Edit (✏️)** icon on a student → change their class | "Easy updates — reassign class, change parent, update photo." |
| 8 | Click **Save** → confirm the change reflected in the table | "Changes are saved and reflected immediately." |

---

## 🎞️ Scenario 4 — Admin Manages Classes & Subjects (≈ 30 sec)

**Purpose:** Show the structural setup of the school.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Click **Classes** in sidebar → `/admin/classes` | "Classes represent grade groups — e.g., Grade 5-A." |
| 2 | Show the class list with student count per class | "Each class shows how many students are enrolled." |
| 3 | Click **Subjects** in sidebar → `/admin/subjects` | "Subjects are linked to classes and teachers." |
| 4 | Show subject list with assigned teacher names | "Every subject has a responsible teacher." |

---

## 🎞️ Scenario 5 — Teacher Login & Dashboard (≈ 45 sec)

**Purpose:** Transition to the teacher perspective — show their focused view.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | **Logout** from admin (click avatar → Logout) | "Now let's switch to a teacher's perspective." |
| 2 | Login with **teacher** credentials | "Teachers see only what's relevant to them." |
| 3 | Show the **Teacher Dashboard**: My Classes, Students Taught, Sessions This Week, Avg Score | "A teacher's dashboard focuses on their classes, student count, and performance metrics." |
| 4 | Hover over **My Classes** card — show class names in the hint | "All assigned classes listed at a glance." |
| 5 | Show the **Dashboard Charts** (attendance + score trends for their classes) | "Charts track how their students are doing week by week." |
| 6 | Show **Recent Activity** (recent exams they created) | "Recent exam activity is always visible." |

---

## 🎞️ Scenario 6 — Teacher Takes Attendance with Face Recognition (≈ 1 min 30 sec) ⭐ KEY FEATURE

**Purpose:** This is the **hero feature** — automated attendance via face recognition. Give it the most screen time.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Click **Attendance** or navigate to attendance session page | "Now the magic — automated attendance using face recognition." |
| 2 | Show the **Attendance Sessions** table | "Sessions are created per class per day." |
| 3 | Click **+ New Session** → select a class → create session | "The teacher starts a session for their class." |
| 4 | Show the session detail with the **Camera Capture** component | "The camera opens — ready to scan the classroom." |
| 5 | Click **Start Camera** → show the live video feed | "A live camera feed activates." |
| 6 | Click **Scan / Capture** → show the face detection rectangles overlay | "Face detection highlights each student in the frame." |
| 7 | Wait for the **processing result** to appear | "The image is sent to the face recognition service..." |
| 8 | Show the **result panel**: number of faces detected, students matched, attendance marked | "...and within seconds, students are identified and marked present automatically." |
| 9 | Show the **matched student list** with names + confidence scores | "Each match shows the student name and confidence level." |
| 10 | Show any **unmatched faces** (if present) | "Unrecognized faces are flagged for manual review." |
| 11 | Click **Complete Session** → show attendance summary | "The teacher completes the session — all present students are recorded." |

---

## 🎞️ Scenario 7 — Teacher Creates an Exam & Enters Grades (≈ 1 min)

**Purpose:** Show the assessment lifecycle from creation to grading.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Click **Exams** in sidebar → `/teacher/exams` | "Teachers manage their own exams." |
| 2 | Click **+ Create Exam** → fill in: name, subject, grade, exam type, total grade | "Creating an exam — name, subject, grade level, and total score." |
| 3 | Show the exam appearing in the list | "The exam is ready for grading." |
| 4 | Click on an exam → show **grade entry** for students in that class | "Now enter grades for each student." |
| 5 | Type scores for 2–3 students → click **Save Grades** | "Individual scores are saved per student." |
| 6 | Show the **average score** updating | "The class average updates instantly." |

---

## 🎞️ Scenario 8 — Teacher Uploads Materials & Videos (≈ 30 sec)

**Purpose:** Show content delivery capabilities.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Click **Materials** in sidebar → `/teacher/materials` | "Teachers can upload study materials — PDFs, documents, links." |
| 2 | Click **+ Add Material** → upload a file, set target classes | "Materials are targeted to specific classes." |
| 3 | Click **Videos** in sidebar → `/teacher/videos` | "Video lessons can be uploaded and streamed." |
| 4 | Show a video entry with streaming capability | "Students watch videos with progress tracking." |

---

## 🎞️ Scenario 9 — Student Login & Portal (≈ 45 sec)

**Purpose:** Show what students see — their personal academic view.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | **Logout** from teacher | "Now let's see the student experience." |
| 2 | Login with **student** credentials | "Students access their own personalized portal." |
| 3 | Show **Student Dashboard**: Attendance Rate, Avg Score, My Subjects, Exams Taken | "A clean dashboard — attendance, scores, subjects, and exam count." |
| 4 | Show the **Dashboard Charts** (their own attendance + score trends) | "Students can track their own progress over time." |
| 5 | Click **Grades** in sidebar → show grade list with per-exam scores | "Every exam result with percentage and details." |
| 6 | Show the **Average Grade** card at the top | "An overall average gives a quick performance summary." |
| 7 | Click **Subjects** → show enrolled subjects with teacher names | "All their subjects and who teaches them." |
| 8 | Click **Videos** → show available videos with progress indicators | "Video lessons with watch-progress — resume where they left off." |

---

## 🎞️ Scenario 10 — Parent Login & Dashboard (≈ 45 sec)

**Purpose:** Show parental oversight — the key value proposition for families.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | **Logout** from student | "Finally, the parent perspective — monitoring their children." |
| 2 | Login with **parent** credentials | "Parents get a supervisory view of all their children." |
| 3 | Show **Parent Dashboard**: My Children, Avg Attendance, Avg Score, Notifications | "At a glance — how many children, their average attendance and scores." |
| 4 | Show the **Child Cards** section — each child with name, attendance %, avg score | "Each child gets a card — color-coded: green for good, amber for concerning, red for at-risk." |
| 5 | Point out **color coding**: a child with ≥80% attendance is green, <60% is red | "Color coding makes it easy to spot which child needs attention." |
| 6 | Click **Children** in sidebar → show detailed children list | "Full details for each enrolled child." |
| 7 | Click **Attendance** → show per-child attendance records | "Drill into attendance history for any child." |
| 8 | Click **Grades** → show per-child grade breakdown | "See every exam score for each child." |

---

## 🎞️ Scenario 11 — Parent Uses the AI Chatbot (≈ 30 sec) ⭐ SMART FEATURE

**Purpose:** Show the AI assistant that gives parents instant answers.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Click the **Chatbot icon** (🤖) in the bottom-right corner | "Smart School includes an AI chatbot tailored to each role." |
| 2 | The chatbot opens with **"Parent Chatbot"** label | "As a parent, the chatbot knows about your children." |
| 3 | Type: **"How is my child doing in Math?"** | "Ask about any child's performance..." |
| 4 | Show the bot's response with attendance + score data | "...and get an instant summary with real data from the system." |
| 5 | Type: **"Is my child at risk?"** | "Ask about at-risk status..." |
| 6 | Show the bot's response identifying any at-risk indicators | "...the bot checks attendance and grade thresholds to flag concerns." |
| 7 | Type: **"What exams are coming up?"** | "Ask about upcoming exams..." |
| 8 | Show the bot listing upcoming exams for the child | "...and get scheduled exam details." |

---

## 🎞️ Scenario 12 — Notifications (Real-Time) (≈ 30 sec)

**Purpose:** Show the real-time notification system.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Switch back to **Admin** or **Teacher** login | "The notification system keeps everyone informed in real time." |
| 2 | Show the **Notification Bell** 🔔 with unread badge count | "A badge shows unread notifications." |
| 3 | Click the bell → show the notification dropdown | "Click to see recent alerts — exam reminders, at-risk warnings, attendance alerts." |
| 4 | Click **Mark All Read** → badge disappears | "Manage notifications easily." |
| 5 | Navigate to **Notifications Page** → show full list with filters | "Filter by type — exam reminders, at-risk alerts, attendance warnings." |
| 6 | Show **Notification Preferences** page → toggle types on/off | "Customize which notifications you receive." |

---

## 🎞️ Scenario 13 — Weekly Reports & PDF Download (≈ 30 sec)

**Purpose:** Show the reporting engine with PDF export.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | As **Admin**, click **Weekly Reports** in sidebar | "Weekly analytics reports track school-wide trends." |
| 2 | Show the **Dashboard Analytics** view with 8-week trends | "Eight weeks of data — attendance, scores, enrollment." |
| 3 | Click **Generate Report** → show the generation process | "Generate a new weekly snapshot with one click." |
| 4 | Show the generated report in the list | "The report appears with a download option." |
| 5 | Click **Download PDF** → show the PDF opening | "A professional PDF report — ready to share with stakeholders." |

---

## 🎞️ Scenario 14 — Arabic Language Full Switch (≈ 30 sec)

**Purpose:** Prove full bilingual coverage — not just labels but data too.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Switch language to **Arabic** using the language selector | "Now let's see the full Arabic experience." |
| 2 | Show the **Sidebar** — all navigation labels in Arabic | "Navigation fully translated." |
| 3 | Show the **Dashboard** — stat card labels in Arabic | "Dashboard metrics in Arabic." |
| 4 | Show a **Student Detail** — Arabic name fields, Arabic subject names | "Student data supports Arabic names and content." |
| 5 | Show an **Exam** — Arabic exam name, Arabic question options | "Exams are fully bilingual — name, questions, options." |
| 6 | Show **Notifications** — Arabic body text | "Notification messages in Arabic." |
| 7 | Show the **Chatbot** responding in Arabic | "Even the AI chatbot responds in Arabic." |

---

## 🎞️ Scenario 15 — At-Risk Student Detection (≈ 20 sec) ⭐ SMART FEATURE

**Purpose:** Show the intelligent at-risk detection that auto-notifies parents.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | As **Admin**, show a student with low attendance (<70%) and low grades (<50%) | "Smart School automatically detects at-risk students." |
| 2 | Show the **At-Risk Notification** that was auto-generated | "When attendance or grades drop below thresholds, the system flags the student." |
| 3 | Switch to **Parent** → show the at-risk notification in their bell | "Parents receive an automatic alert — no manual intervention needed." |
| 4 | Show the **Chatbot** confirming at-risk status when asked | "The chatbot reinforces the alert with detailed context." |

---

## 🎞️ Scenario 16 — Profile & Logout (≈ 15 sec)

**Purpose:** Clean ending — show user management basics.

| Step | Action | Narration Tip |
|------|--------|---------------|
| 1 | Click **Profile** in sidebar → show user details (name, role, email, photo) | "Each user has a profile with their details." |
| 2 | Click **Logout** → return to login page | "Secure logout — session cleared." |
| 3 | Show the login page again as the final frame | "Smart School — one platform, every role, fully bilingual, AI-powered." |

---

## 🏁 Suggested Video Structure

| Section | Time | Scenarios |
|---------|------|-----------|
| **Intro** | 0:00–0:30 | Scenario 1 (Login + Language) |
| **Admin View** | 0:30–2:15 | Scenarios 2, 3, 4 |
| **Teacher View** | 2:15–4:45 | Scenarios 5, 6 ⭐, 7, 8 |
| **Student View** | 4:45–5:30 | Scenario 9 |
| **Parent View** | 5:30–6:45 | Scenarios 10, 11 ⭐ |
| **Smart Features** | 6:45–7:35 | Scenarios 12, 13, 15 ⭐ |
| **Bilingual Proof** | 7:35–8:05 | Scenario 14 |
| **Outro** | 8:05–8:20 | Scenario 16 |

**Total estimated length: ≈ 8 minutes**

---

## 💡 Recording Tips

1. **Zoom in** on important details (stat cards, face detection rectangles, chatbot responses) — use browser zoom `Ctrl +` or OBS zoom filter.
2. **Pause 2 seconds** after each click before narrating — lets the viewer see the result.
3. **Use smooth mouse movements** — avoid jerky scrolling.
4. **Record in one continuous session** then edit cuts — easier to maintain flow.
5. **Add text overlays** for key terms: "Face Recognition Attendance", "AI Chatbot", "At-Risk Detection", "Bilingual EN/AR".
6. **Highlight the ⭐ scenarios** — these are your differentiators. Spend more time on face recognition (Scenario 6) and the chatbot (Scenario 11).
7. **Close unnecessary browser tabs** and hide bookmarks bar for a clean look.
8. **Use a consistent window size** throughout — don't resize mid-recording.
9. **Mute notifications** on your OS and phone while recording.
10. **Record audio separately** if needed — you can narrate after recording the screen for cleaner audio.

---

## 🎯 Key Differentiators to Emphasize

| Feature | Why It Matters | Where to Show |
|---------|---------------|---------------|
| **Face Recognition Attendance** | Eliminates manual roll call, saves 10+ min per class | Scenario 6 |
| **AI Chatbot per Role** | Instant answers without navigating multiple pages | Scenario 11 |
| **At-Risk Auto-Detection** | Proactive intervention before students fail | Scenario 15 |
| **Full Arabic/English** | Accessibility for Arabic-speaking schools | Scenario 14 |
| **Role-Tailored Dashboards** | Each role sees only what they need | Scenarios 2, 5, 9, 10 |
| **Weekly PDF Reports** | Professional reporting for stakeholders | Scenario 13 |
| **Real-Time Notifications** | WebSocket-powered instant alerts | Scenario 12 |