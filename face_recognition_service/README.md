# Face Recognition Service

FastAPI service for face recognition in the Smart School Backend system.

## Features

- Face verification for student attendance
- Face registration for students
- Integration with Django backend database
- RESTful API endpoints

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install dlib (required for face_recognition):**
   
   On Windows:
   ```bash
   pip install dlib
   ```
   
   If you encounter issues, you may need to install CMake first:
   ```bash
   pip install cmake
   pip install dlib
   ```

3. **Set up environment variables:**
   
   Create a `.env` file in the `face_recognition_service` directory:
   ```
   DB_HOST=DESKTOP-2ASDU43\SQLEXPRESS
   DB_NAME=smart-school
   ```

## Running the Service

```bash
cd face_recognition_service
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

The service will run on `http://localhost:8001`

## API Endpoints

### 1. Root
**GET** `/`
- Returns service information and available endpoints

### 2. Verify Face
**POST** `/verify-face`
- **Parameters:**
  - `student_id` (form data): Student ID to verify against
  - `image` (file): Image file containing face
- **Response:**
  ```json
  {
    "match": true,
    "student_id": "S001",
    "confidence": 95.5,
    "message": "Face verified successfully for student S001"
  }
  ```

### 3. Register Face
**POST** `/register-face`
- **Parameters:**
  - `student_id` (form data): Student ID
  - `image` (file): Image file containing face to register
- **Response:**
  ```json
  {
    "success": true,
    "message": "Face registered successfully for student S001",
    "student_id": "S001"
  }
  ```

### 4. Check Face Status
**GET** `/students/{student_id}/face-status`
- **Response:**
  ```json
  {
    "student_id": "S001",
    "has_registered_face": true,
    "message": "Face registered"
  }
  ```

## Usage Examples

### Using cURL

**Register a face:**
```bash
curl -X POST "http://localhost:8001/register-face" \
  -F "student_id=S001" \
  -F "image=@path/to/student_photo.jpg"
```

**Verify a face:**
```bash
curl -X POST "http://localhost:8001/verify-face" \
  -F "student_id=S001" \
  -F "image=@path/to/attendance_photo.jpg"
```

### Using Python requests

```python
import requests

# Register face
with open('student_photo.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8001/register-face',
        files={'image': f},
        data={'student_id': 'S001'}
    )
print(response.json())

# Verify face
with open('attendance_photo.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8001/verify-face',
        files={'image': f},
        data={'student_id': 'S001'}
    )
print(response.json())
```

## Integration with Django Backend

The service connects to the same SQL Server database as the Django backend to:
- Verify student existence
- Can be extended to automatically create attendance records

## Face Encoding Storage

Face encodings are stored locally in the `face_encodings/` directory as pickle files:
- Format: `{student_id}.pkl`
- Each file contains the face encoding array for that student

## Notes

- The service uses a tolerance of 0.6 for face matching (lower = more strict)
- Only the first face detected in an image is used
- Images should be clear and well-lit for best results
- Face encodings are stored locally, not in the database

## Troubleshooting

### dlib installation issues
If you have trouble installing dlib:
1. Install Visual Studio Build Tools (Windows)
2. Install CMake: `pip install cmake`
3. Then install dlib: `pip install dlib`

### Database connection issues
- Ensure SQL Server is running
- Check database credentials in `.env` file
- Verify ODBC Driver 17 for SQL Server is installed

