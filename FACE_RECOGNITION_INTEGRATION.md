# Face Recognition Integration Guide

## Overview

The Django backend is now integrated with the FastAPI face recognition service. Students can mark their attendance by uploading a photo, which is verified against their registered face encoding.

## Architecture

```
Frontend/Client
    ↓
Django Backend (REST API)
    ↓
FastAPI Face Recognition Service
    ↓
Face Encoding Storage (Local)
```

## API Endpoint

### Mark Attendance via Face Recognition

**Endpoint:** `POST /api/attendance/face-recognition/`

**Authentication:** Required (JWT Token)

**Content-Type:** `multipart/form-data`

**Request Body:**
- `student_id` (string, required): Student ID to verify
- `image` (file, required): Image file containing the face

**Response (Success - Face Matches):**
```json
{
    "success": true,
    "attendance_id": 123,
    "student_id": "S001",
    "date": "2026-01-31",
    "match": true,
    "confidence": 95.5,
    "message": "Attendance marked successfully via face recognition",
    "attendance": {
        "id": 123,
        "student": 1,
        "student_id": "S001",
        "student_name": "John Doe",
        "date": "2026-01-31",
        "status": "present",
        "status_display": "Present",
        "source": "face_recognition",
        "source_display": "FaceRecognition",
        "notes": "Marked via face recognition. Confidence: 95.50%",
        "marked_by": null,
        "marked_by_name": null,
        "created_at": "2026-01-31T12:00:00Z",
        "updated_at": "2026-01-31T12:00:00Z"
    }
}
```

**Response (Error - Face Doesn't Match):**
```json
{
    "success": false,
    "student_id": "S001",
    "match": false,
    "confidence": 45.2,
    "message": "Face does not match registered face for student S001",
    "error": "face_mismatch"
}
```

**Response (Error - Student Not Found):**
```json
{
    "success": false,
    "message": "Student with ID S001 not found",
    "error": "student_not_found",
    "student_id": "S001"
}
```

**Response (Error - Service Unavailable):**
```json
{
    "success": false,
    "student_id": "S001",
    "match": false,
    "message": "Face recognition service is unavailable. Please try again later.",
    "error": "connection_error"
}
```

## Usage Examples

### Python (requests)

```python
import requests

# Get JWT token first
login_response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'student_user',
    'password': 'password123'
})
token = login_response.json()['access']

# Mark attendance via face recognition
headers = {'Authorization': f'Bearer {token}'}

with open('student_photo.jpg', 'rb') as f:
    files = {'image': f}
    data = {'student_id': 'S001'}
    response = requests.post(
        'http://localhost:8000/api/attendance/face-recognition/',
        headers=headers,
        files=files,
        data=data
    )
    print(response.json())
```

### JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append('student_id', 'S001');
formData.append('image', imageFile); // File object from input

fetch('http://localhost:8000/api/attendance/face-recognition/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Attendance marked!', data);
    } else {
        console.error('Face verification failed:', data.message);
    }
});
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/attendance/face-recognition/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "student_id=S001" \
  -F "image=@student_photo.jpg"
```

## Workflow

1. **Student uploads image** → Django backend receives request
2. **Django validates** → Checks student exists, permissions
3. **Django calls FastAPI** → Sends image to face recognition service
4. **FastAPI verifies** → Compares face with stored encoding
5. **FastAPI returns result** → Match (true/false) and confidence
6. **If match = true** → Django creates/updates attendance record
7. **If match = false** → Django returns error, no attendance marked

## Permissions

- **Students**: Can only mark their own attendance
- **Teachers/Admins**: Can mark attendance for any student
- **Parents**: Cannot mark attendance (read-only)

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Face Recognition Service URL
FACE_RECOGNITION_SERVICE_URL=http://localhost:8001

# Request timeout in seconds
FACE_RECOGNITION_TIMEOUT=30
```

### Settings

The settings are automatically loaded from environment variables:

```python
# In settings.py
FACE_RECOGNITION_SERVICE_URL = os.getenv('FACE_RECOGNITION_SERVICE_URL', 'http://localhost:8001')
FACE_RECOGNITION_TIMEOUT = int(os.getenv('FACE_RECOGNITION_TIMEOUT', '30'))
```

## Error Handling

The integration handles various error scenarios:

1. **Missing student_id or image** → 400 Bad Request
2. **Student not found** → 404 Not Found
3. **Permission denied** → 403 Forbidden
4. **Face doesn't match** → 400 Bad Request (with confidence score)
5. **Service unavailable** → 500 Internal Server Error
6. **Service timeout** → 500 Internal Server Error

## Attendance Record Behavior

- **New attendance**: Creates new record with `source=face_recognition`
- **Existing manual attendance**: Updates to `source=face_recognition`
- **Existing face recognition attendance**: Returns existing record (no duplicate)

## Prerequisites

1. **Face Recognition Service Running**: FastAPI service must be running on port 8001
2. **Student Face Registered**: Student must have registered their face first
3. **JWT Authentication**: User must be authenticated with valid JWT token

## Testing

1. **Start FastAPI service:**
   ```bash
   cd face_recognition_service
   python main.py
   ```

2. **Start Django server:**
   ```bash
   python manage.py runserver
   ```

3. **Register a student's face:**
   ```bash
   curl -X POST "http://localhost:8001/register-face" \
     -F "student_id=S001" \
     -F "image=@student_photo.jpg"
   ```

4. **Mark attendance:**
   ```bash
   curl -X POST "http://localhost:8000/api/attendance/face-recognition/" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "student_id=S001" \
     -F "image=@verification_photo.jpg"
   ```

## Files Created/Modified

### New Files
- `attendance/face_recognition_client.py` - Client for FastAPI service
- `attendance/face_recognition_serializers.py` - Serializers for face recognition endpoints

### Modified Files
- `attendance/views.py` - Added `face_recognition_attendance` action
- `smartSchool/settings.py` - Added face recognition service configuration
- `requirements.txt` - Added `requests` and `Pillow` dependencies

## Security Considerations

1. **Authentication Required**: All requests require JWT authentication
2. **Permission Checks**: Students can only mark their own attendance
3. **Input Validation**: Student ID and image file are validated
4. **Error Messages**: Generic error messages to prevent information leakage
5. **Timeout Protection**: Requests timeout after 30 seconds to prevent hanging

## Future Enhancements

- Batch face recognition for multiple students
- Face recognition attendance history
- Confidence threshold configuration
- Automatic retry on service errors
- Webhook notifications for attendance events

