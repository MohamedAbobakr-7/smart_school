# Testing Guide: Automated Face Recognition Attendance

This guide explains how to test the new automated attendance system with instructor-controlled batch face recognition.

## Prerequisites

1. **Django Backend Running**
   ```bash
   python manage.py runserver
   ```
   Should be accessible at `http://localhost:8000`

2. **FastAPI Service Running**
   ```bash
   cd face_recognition_service
   python main.py
   ```
   Should be accessible at `http://localhost:8001`

3. **Database Migrations Applied**
   ```bash
   python manage.py makemigrations attendance
   python manage.py migrate
   ```

4. **Test Data Created**
   ```bash
   python manage.py create_test_data
   ```
   This creates test users (instructors, students) and registers face encodings.

5. **Test Image**
   - A classroom photo with multiple faces
   - Students in the image should have registered face encodings
   - Save as `test_classroom.jpg` (or specify path)

## Quick Test

### Using the Test Script

```bash
# Basic test (uses default image path)
python test_automated_attendance.py

# With custom image path
python test_automated_attendance.py path/to/classroom_image.jpg
```

The script will:
1. Login as instructor
2. Test FastAPI batch detection
3. Create attendance session
4. Process classroom image
5. View attendance records
6. Complete session

## Manual Testing

### 1. Login as Instructor

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "teacher1",
    "password": "password123"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Save the `access` token for next steps.

### 2. Create Attendance Session

```bash
TOKEN="your_access_token_here"

curl -X POST http://localhost:8000/api/attendance-sessions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-01-31",
    "class_name": "Mathematics - Grade 10",
    "notes": "Morning class session"
  }'
```

**Response:**
```json
{
  "id": 1,
  "instructor": 1,
  "date": "2026-01-31",
  "status": "active",
  "class_name": "Mathematics - Grade 10",
  "total_faces_detected": 0,
  "total_matches": 0,
  "total_attendance_marked": 0
}
```

Save the `id` as `SESSION_ID`.

### 3. Test FastAPI Batch Detection (Optional)

```bash
curl -X POST http://localhost:8001/detect-faces-batch \
  -F "image=@test_classroom.jpg" \
  -F "tolerance=0.6"
```

**Response:**
```json
{
  "success": true,
  "num_faces_detected": 25,
  "num_matches": 23,
  "matches": [
    {
      "face_index": 0,
      "student_id": "S001",
      "match": true,
      "confidence": 95.5
    },
    ...
  ]
}
```

### 4. Process Classroom Image

```bash
SESSION_ID=1  # From step 2

curl -X POST http://localhost:8000/api/attendance/process-classroom-image/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "session_id=$SESSION_ID" \
  -F "image=@test_classroom.jpg"
```

**Response:**
```json
{
  "success": true,
  "session_id": 1,
  "num_faces_detected": 25,
  "num_matches": 23,
  "num_attendance_marked": 23,
  "matched_students": ["S001", "S002", "S003", ...],
  "attendance_records": [
    {
      "id": 101,
      "student_id": "S001",
      "student_name": "John Doe",
      "date": "2026-01-31",
      "status": "present",
      "source": "face_recognition"
    },
    ...
  ]
}
```

### 5. View Session Details

```bash
curl -X GET http://localhost:8000/api/attendance-sessions/$SESSION_ID/ \
  -H "Authorization: Bearer $TOKEN"
```

### 6. View Attendance Records

```bash
curl -X GET "http://localhost:8000/api/attendance/?date=2026-01-31" \
  -H "Authorization: Bearer $TOKEN"
```

### 7. Complete Session

```bash
curl -X POST http://localhost:8000/api/attendance-sessions/$SESSION_ID/complete/ \
  -H "Authorization: Bearer $TOKEN"
```

## Python Testing

### Using requests library

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = None

# 1. Login
response = requests.post(f"{BASE_URL}/api/auth/login/", json={
    "username": "teacher1",
    "password": "password123"
})
TOKEN = response.json()["access"]
headers = {"Authorization": f"Bearer {TOKEN}"}

# 2. Create session
session_response = requests.post(
    f"{BASE_URL}/api/attendance-sessions/",
    headers=headers,
    json={
        "date": "2026-01-31",
        "class_name": "Test Class"
    }
)
session_id = session_response.json()["id"]

# 3. Process image
with open("test_classroom.jpg", "rb") as f:
    files = {"image": f}
    data = {"session_id": session_id}
    process_response = requests.post(
        f"{BASE_URL}/api/attendance/process-classroom-image/",
        headers={k: v for k, v in headers.items() if k != "Content-Type"},
        files=files,
        data=data
    )
    print(process_response.json())

# 4. Complete session
complete_response = requests.post(
    f"{BASE_URL}/api/attendance-sessions/{session_id}/complete/",
    headers=headers
)
print(complete_response.json())
```

## JavaScript/TypeScript Testing

```javascript
const BASE_URL = 'http://localhost:8000';
let token = null;
let sessionId = null;

// 1. Login
async function login() {
    const response = await fetch(`${BASE_URL}/api/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: 'teacher1',
            password: 'password123'
        })
    });
    const data = await response.json();
    token = data.access;
    return token;
}

// 2. Create session
async function createSession() {
    const response = await fetch(`${BASE_URL}/api/attendance-sessions/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            date: '2026-01-31',
            class_name: 'Test Class'
        })
    });
    const data = await response.json();
    sessionId = data.id;
    return sessionId;
}

// 3. Process image from camera
async function processImage(imageFile) {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('image', imageFile);
    
    const response = await fetch(`${BASE_URL}/api/attendance/process-classroom-image/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    const data = await response.json();
    console.log(`Matched ${data.num_matches} students`);
    return data;
}

// 4. Complete session
async function completeSession() {
    const response = await fetch(`${BASE_URL}/api/attendance-sessions/${sessionId}/complete/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return await response.json();
}

// Usage
(async () => {
    await login();
    await createSession();
    
    // Capture image from camera
    const imageFile = await captureFromCamera(); // Your camera capture function
    await processImage(imageFile);
    await completeSession();
})();
```

## Testing Scenarios

### Scenario 1: Successful Batch Attendance

1. Start session
2. Process image with 25 faces
3. 23 faces match registered students
4. 23 attendance records created
5. Complete session

**Expected:** All matched students marked as present.

### Scenario 2: No Faces Detected

1. Start session
2. Process image with no faces (empty classroom, wrong angle)

**Expected:** 
- `num_faces_detected: 0`
- `num_matches: 0`
- No attendance records created
- Success response with message

### Scenario 3: Faces Detected but No Matches

1. Start session
2. Process image with faces of unregistered students

**Expected:**
- `num_faces_detected: > 0`
- `num_matches: 0`
- No attendance records created
- Matches array shows `match: false` for all faces

### Scenario 4: Partial Matches

1. Start session
2. Process image with mix of registered and unregistered students

**Expected:**
- Some faces match, some don't
- Only matched students get attendance records
- Response shows both matched and unmatched faces

### Scenario 5: Duplicate Attendance

1. Start session
2. Process image (marks attendance)
3. Process same image again

**Expected:**
- Second processing doesn't create duplicate records
- Existing attendance records remain
- Session statistics update correctly

### Scenario 6: Permission Denied

1. Login as student (not instructor)
2. Try to create session

**Expected:**
- `403 Forbidden` error
- Message: "Only instructors can process classroom images"

### Scenario 7: Invalid Session

1. Create session
2. Complete session
3. Try to process image with completed session

**Expected:**
- `404 Not Found` or `400 Bad Request`
- Message: "Active session with ID X not found"

## Troubleshooting

### Issue: "No faces detected"

**Causes:**
- Image quality too low
- No faces in image
- Wrong image format
- Face recognition service not working

**Solutions:**
- Use clear, well-lit images
- Ensure faces are clearly visible
- Check FastAPI service is running
- Verify image format (JPG, PNG)

### Issue: "Face detection service unavailable"

**Causes:**
- FastAPI service not running
- Wrong service URL in settings
- Network connectivity issues

**Solutions:**
- Start FastAPI service: `cd face_recognition_service && python main.py`
- Check `FACE_RECOGNITION_SERVICE_URL` in Django settings
- Verify service is accessible: `curl http://localhost:8001/`

### Issue: "No matches found"

**Causes:**
- Students not registered in system
- Face encodings not created
- Tolerance too strict
- Image quality issues

**Solutions:**
- Register student faces first: `POST /register-face`
- Check face encodings exist: `GET /students/{id}/face-status`
- Adjust tolerance (default 0.6, lower = stricter)
- Use better quality images

### Issue: "Permission denied"

**Causes:**
- User not logged in
- User is student (not instructor)
- Wrong JWT token

**Solutions:**
- Login as instructor/teacher
- Check user role: `GET /api/users/me/`
- Verify JWT token is valid
- Refresh token if expired

### Issue: "Session not found"

**Causes:**
- Session ID incorrect
- Session already completed/cancelled
- Session belongs to different instructor

**Solutions:**
- Use correct session ID
- Create new session
- Check session status: `GET /api/attendance-sessions/{id}/`
- Verify session ownership

## Expected Results

### Successful Test Output

```
================================================================================
AUTOMATED ATTENDANCE SYSTEM - FULL TEST
================================================================================

============================================================
STEP 1: Instructor Login
============================================================
✓ Login successful
  User: teacher1
  Token: eyJ0eXAiOiJKV1QiLCJhbGc...

============================================================
STEP 2: Test FastAPI Batch Face Detection
============================================================
✓ Batch detection successful
  Faces detected: 25
  Matches found: 23

============================================================
STEP 3: Create Attendance Session
============================================================
✓ Session created successfully
  Session ID: 1
  Date: 2026-01-31
  Class: Test Class
  Status: Active

============================================================
STEP 4: Process Classroom Image
============================================================
✓ Image processed successfully
  Faces detected: 25
  Matches found: 23
  Attendance marked: 23

============================================================
STEP 5: Complete Session
============================================================
✓ Session completed successfully
  Total faces detected: 25
  Total matches: 23
  Total attendance marked: 23

================================================================================
✓ ALL TESTS COMPLETED SUCCESSFULLY!
================================================================================
```

## Next Steps

After successful testing:

1. **Register Student Faces**: Ensure all students have registered face encodings
2. **Train Instructors**: Show instructors how to use the system
3. **Monitor Sessions**: Review session statistics and attendance records
4. **Optimize Settings**: Adjust tolerance and image quality based on results
5. **Scale Testing**: Test with larger classrooms and multiple sessions

## Additional Resources

- `AUTOMATED_ATTENDANCE_WORKFLOW.md` - Complete workflow documentation
- `face_recognition_service/README.md` - FastAPI service documentation
- `test_automated_attendance.py` - Automated test script

