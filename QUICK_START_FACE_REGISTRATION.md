# Quick Start: Register Student Faces

## Problem
- System detected only **1 face** (should detect multiple)
- **0 matches** because no students have registered faces

## Solution: Register Student Faces First

### Step 1: Get Individual Student Photos

You need **one clear photo per student** showing their face clearly.

### Step 2: Register Each Student

**Option A: Using the script (Recommended)**

```bash
# Register a single student
python register_student_faces.py --student-id S001 --image "E:\WhatsApp Image 2026-02-06 at 10.25.58 PM.jpeg"

# Check if registered
python register_student_faces.py --check S001

# List all registered
python register_student_faces.py --list
```

**Option B: Using cURL**

```bash
curl -X POST "http://localhost:8001/register-face" \
  -F "student_id=S001" \
  -F "image=@student1_photo.jpg"
```

**Option C: Using Python**

```python
import requests

student_id = "S001"
image_path = "student1_photo.jpg"

with open(image_path, 'rb') as f:
    response = requests.post(
        'http://localhost:8001/register-face',
        files={'image': f},
        data={'student_id': student_id}
    )
print(response.json())
```

### Step 3: Test Batch Detection Again

After registering faces, run your test again:

```bash
python test_automated_attendance.py
```

## Why Only 1 Face Detected?

The `face_recognition` library may miss faces if:
- Faces are too small in the image
- Poor lighting or shadows
- Faces at extreme angles
- Faces partially obscured
- Faces too close together

**Tips for better detection:**
1. Use well-lit images
2. Ensure faces are clearly visible and not too small
3. Try different angles/distances
4. Use higher resolution images
5. Ensure faces are facing the camera

## Current Status

- **Registered students:** 0 (need to register first)
- **Faces detected in your image:** 1
- **Matches:** 0 (because no faces registered)

## Next Steps

1. Register at least 1-2 student faces using individual photos
2. Test batch detection again
3. If detection is still low, try a different image or adjust camera angle



