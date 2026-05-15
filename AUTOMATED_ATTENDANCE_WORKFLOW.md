# Automated Face Recognition Attendance Workflow

## Overview

The system now supports **fully automated attendance** where instructors control the process and students have no interaction. The system captures images from classroom cameras, detects all faces, matches them to students, and marks attendance automatically.

## Key Changes

### ✅ Instructor-Controlled Only
- **Only instructors** (teachers/admins) can start attendance sessions
- **Only instructors** can capture and process classroom images
- **Students cannot** upload images or mark their own attendance

### ✅ Batch Face Detection
- System detects **multiple faces** in a single classroom image
- Automatically matches each face to registered student encodings
- Marks attendance for all matched students in one operation

### ✅ Session-Based Workflow
- Instructors start an **attendance session**
- Capture one or more classroom images during the session
- System processes images and marks attendance automatically
- Session tracks statistics (faces detected, matches, attendance marked)

## Workflow

### 1. Instructor Starts Session

**Endpoint:** `POST /api/attendance-sessions/`

**Request:**
```json
{
    "date": "2026-01-31",
    "class_name": "Mathematics - Grade 10",
    "notes": "Morning class"
}
```

**Response:**
```json
{
    "id": 1,
    "instructor": 1,
    "instructor_id": "T001",
    "instructor_name": "John Teacher",
    "date": "2026-01-31",
    "status": "active",
    "status_display": "Active",
    "class_name": "Mathematics - Grade 10",
    "notes": "Morning class",
    "total_faces_detected": 0,
    "total_matches": 0,
    "total_attendance_marked": 0,
    "started_at": "2026-01-31T08:00:00Z"
}
```

### 2. Instructor Captures Classroom Image

The instructor uses their laptop/mobile camera to capture an image of the classroom.

### 3. System Processes Image

**Endpoint:** `POST /api/attendance/process-classroom-image/`

**Request (multipart/form-data):**
- `session_id`: Active session ID
- `image`: Image file from camera

**Response:**
```json
{
    "success": true,
    "session_id": 1,
    "num_faces_detected": 25,
    "num_matches": 23,
    "num_attendance_marked": 23,
    "matched_students": ["S001", "S002", "S003", ...],
    "matches": [
        {
            "face_index": 0,
            "student_id": "S001",
            "match": true,
            "confidence": 95.5,
            "face_location": [100, 200, 300, 400]
        },
        {
            "face_index": 1,
            "student_id": "S002",
            "match": true,
            "confidence": 92.3,
            "face_location": [150, 250, 350, 450]
        },
        {
            "face_index": 2,
            "student_id": null,
            "match": false,
            "confidence": 45.2,
            "face_location": [200, 300, 400, 500]
        }
    ],
    "attendance_records": [
        {
            "id": 101,
            "student_id": "S001",
            "student_name": "John Doe",
            "date": "2026-01-31",
            "status": "present",
            "source": "face_recognition",
            "session": 1,
            "notes": "Marked via batch face recognition. Confidence: 95.50%"
        },
        ...
    ],
    "message": "Processed 25 face(s), marked attendance for 23 student(s)"
}
```

### 4. Instructor Completes Session

**Endpoint:** `POST /api/attendance-sessions/{id}/complete/`

**Response:**
```json
{
    "success": true,
    "message": "Session completed successfully",
    "session": {
        "id": 1,
        "status": "completed",
        "total_faces_detected": 25,
        "total_matches": 23,
        "total_attendance_marked": 23,
        "completed_at": "2026-01-31T08:15:00Z"
    }
}
```

## API Endpoints

### Attendance Sessions

- `GET /api/attendance-sessions/` - List sessions (instructors see their own, admins see all)
- `POST /api/attendance-sessions/` - Create new session (instructors only)
- `GET /api/attendance-sessions/{id}/` - Get session details
- `PUT /api/attendance-sessions/{id}/` - Update session
- `POST /api/attendance-sessions/{id}/complete/` - Complete active session
- `POST /api/attendance-sessions/{id}/cancel/` - Cancel active session

### Batch Face Processing

- `POST /api/attendance/process-classroom-image/` - Process classroom image (instructors only)
  - Requires active session
  - Detects all faces
  - Matches to students
  - Marks attendance automatically

## FastAPI Service Endpoints

### Batch Face Detection

- `POST /detect-faces-batch` - Detect all faces and match against students
  - Returns list of matches with student IDs and confidence scores

## Permissions

- **Instructors (Teachers/Admins)**: Full control
  - Create sessions
  - Process images
  - Complete/cancel sessions
  - View their own sessions (teachers) or all sessions (admins)

- **Students**: No access to face recognition attendance
  - Cannot start sessions
  - Cannot upload images
  - Can only view their own attendance records (read-only)

- **Parents**: Read-only access
  - Can view their children's attendance
  - Cannot create sessions or process images

## Database Models

### AttendanceSession

Tracks instructor-controlled attendance sessions:
- `instructor`: Teacher who started the session
- `date`: Session date
- `status`: active, completed, cancelled
- `class_name`: Optional class/subject name
- `total_faces_detected`: Running count
- `total_matches`: Running count
- `total_attendance_marked`: Running count

### Attendance (Updated)

- Added `session` foreign key to link attendance records to sessions
- Tracks which session created each attendance record

## Usage Example

### Python (requests)

```python
import requests

# 1. Login as instructor
login_response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'teacher_user',
    'password': 'password123'
})
token = login_response.json()['access']
headers = {'Authorization': f'Bearer {token}'}

# 2. Start session
session_response = requests.post(
    'http://localhost:8000/api/attendance-sessions/',
    headers=headers,
    json={
        'date': '2026-01-31',
        'class_name': 'Mathematics - Grade 10'
    }
)
session_id = session_response.json()['id']

# 3. Process classroom image
with open('classroom_photo.jpg', 'rb') as f:
    files = {'image': f}
    data = {'session_id': session_id}
    process_response = requests.post(
        'http://localhost:8000/api/attendance/process-classroom-image/',
        headers=headers,
        files=files,
        data=data
    )
    print(process_response.json())

# 4. Complete session
complete_response = requests.post(
    f'http://localhost:8000/api/attendance-sessions/{session_id}/complete/',
    headers=headers
)
print(complete_response.json())
```

### JavaScript (Fetch API)

```javascript
// 1. Start session
const sessionResponse = await fetch('http://localhost:8000/api/attendance-sessions/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        date: '2026-01-31',
        class_name: 'Mathematics - Grade 10'
    })
});
const session = await sessionResponse.json();

// 2. Process image from camera
const formData = new FormData();
formData.append('session_id', session.id);
formData.append('image', imageFile); // From camera capture

const processResponse = await fetch('http://localhost:8000/api/attendance/process-classroom-image/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
});
const result = await processResponse.json();
console.log(`Matched ${result.num_matches} students`);
```

## Error Handling

### Common Errors

1. **No Active Session**
   ```json
   {
       "success": false,
       "message": "Active session with ID 1 not found",
       "error": "session_not_found"
   }
   ```

2. **Permission Denied**
   ```json
   {
       "success": false,
       "message": "Only instructors can process classroom images",
       "error": "permission_denied"
   }
   ```

3. **No Faces Detected**
   ```json
   {
       "success": true,
       "num_faces_detected": 0,
       "num_matches": 0,
       "message": "No faces detected in the image"
   }
   ```

4. **Service Unavailable**
   ```json
   {
       "success": false,
       "message": "Face detection service is unavailable",
       "error": "connection_error"
   }
   ```

## Migration Required

Run migrations to create the new `AttendanceSession` model:

```bash
python manage.py makemigrations attendance
python manage.py migrate
```

## Configuration

Ensure FastAPI service is running:

```bash
cd face_recognition_service
python main.py
```

Service should be accessible at `http://localhost:8001` (or configured URL).

## Benefits

1. **Fully Automated**: No student interaction required
2. **Batch Processing**: Multiple students marked in one operation
3. **Instructor Control**: Only authorized personnel can mark attendance
4. **Session Tracking**: Complete audit trail of attendance sessions
5. **Statistics**: Track faces detected, matches, and attendance marked
6. **Efficient**: Process entire classroom in seconds

## Security

- JWT authentication required
- Role-based permissions (instructors only)
- Session ownership validation
- No student access to face recognition endpoints
- All operations logged and tracked

