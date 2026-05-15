# How to Change Classroom Image for Testing

## Option 1: Edit the Test Script (Recommended)

Open `test_automated_attendance.py` and change line **31**:

```python
# Change this line:
TEST_IMAGE_PATH = r"E:\WhatsApp Image 2026-02-06 at 9.55.11 PM.jpeg"

# To your image path:
TEST_IMAGE_PATH = r"E:\Your\Path\To\Classroom\Image.jpg"
```

**Important:** Use raw string (`r"..."`) for Windows paths with backslashes.

### Examples:

```python
# Windows path with backslashes (use raw string)
TEST_IMAGE_PATH = r"E:\Photos\Classroom\classroom_photo.jpg"

# Or use forward slashes (works on Windows too)
TEST_IMAGE_PATH = "E:/Photos/Classroom/classroom_photo.jpg"

# Relative path (from project root)
TEST_IMAGE_PATH = "test_images/classroom1.jpg"
```

## Option 2: Pass Image as Command Line Argument

You can pass the image path as an argument when running the script:

```bash
python test_automated_attendance.py "E:\Your\Path\To\Image.jpg"
```

The script will use the provided path instead of `TEST_IMAGE_PATH`.

## Option 3: Use cURL Directly

Test with a different image using cURL:

```bash
# 1. Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher1","password":"teacher123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access'])")

# 2. Create session
SESSION_ID=$(curl -X POST http://localhost:8000/api/attendance-sessions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-02-06","class_name":"Test"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['id'])")

# 3. Process your image
curl -X POST http://localhost:8000/api/attendance/process-classroom-image/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "session_id=$SESSION_ID" \
  -F "image=@E:\Your\Path\To\Image.jpg"
```

## Option 4: Use Python Script

Create a simple script to test with any image:

```python
import requests
import sys

# Get image path from command line or use default
image_path = sys.argv[1] if len(sys.argv) > 1 else r"E:\Your\Image.jpg"

# Login
response = requests.post('http://localhost:8000/api/auth/login/', json={
    'username': 'teacher1',
    'password': 'teacher123'
})
token = response.json()['access']
headers = {'Authorization': f'Bearer {token}'}

# Create session
session_response = requests.post(
    'http://localhost:8000/api/attendance-sessions/',
    headers=headers,
    json={'date': '2026-02-06', 'class_name': 'Test'}
)
session_id = session_response.json()['id']

# Process image
with open(image_path, 'rb') as f:
    files = {'image': f}
    data = {'session_id': session_id}
    process_response = requests.post(
        'http://localhost:8000/api/attendance/process-classroom-image/',
        headers={k: v for k, v in headers.items() if k != 'Content-Type'},
        files=files,
        data=data
    )
    print(process_response.json())
```

Save as `test_image.py` and run:
```bash
python test_image.py "E:\Your\Image.jpg"
```

## Quick Reference

### In test_automated_attendance.py:
- **Line 31**: Change `TEST_IMAGE_PATH` to your image path
- **Use raw string** (`r"..."`) for Windows paths

### Command line:
```bash
python test_automated_attendance.py "path\to\your\image.jpg"
```

### Image Requirements:
- ✅ Clear, well-lit image
- ✅ Multiple faces visible
- ✅ Faces facing camera
- ✅ Good resolution (not too small)
- ✅ Formats: JPG, JPEG, PNG

## Current Image Path

Currently set to:
```python
TEST_IMAGE_PATH = r"E:\WhatsApp Image 2026-02-06 at 9.55.11 PM.jpeg"
```

Change this to your new classroom image path!

