# Face Encoding Storage System

## Overview

The face recognition service implements a robust local storage system for face encodings. All encodings are stored locally on disk using Python's pickle serialization format. No cloud services are used.

## Storage Location

- **Directory**: `face_encodings/` (relative to service root)
- **Format**: Pickle files (`.pkl`)
- **Naming**: `{student_id}.pkl`

## Storage Format

### Version 2.0 (Current)

Encodings are stored as dictionaries with metadata:

```python
{
    'encoding': np.ndarray,  # Shape (128,) - the face encoding
    'student_id': str,       # Student ID
    'created_at': str,       # ISO format timestamp
    'format_version': '2.0', # Format version
    'encoding_shape': tuple, # Shape of encoding array
    'image_info': {          # Image metadata
        'width': int,
        'height': int,
        'channels': int,
        'size_bytes': int,
        'face_location': tuple,  # Optional
        'num_faces_detected': int  # Optional
    }
}
```

### Version 1.0 (Legacy)

Old format stored only the encoding array. The system automatically handles both formats.

## Features

### 1. **Automatic Backup**
- When updating an encoding, the old file is automatically backed up as `{student_id}.pkl.backup`
- Backups are created only if they don't already exist

### 2. **Encoding Validation**
- Validates encoding shape (must be (128,))
- Checks file integrity
- Validates numpy array type

### 3. **Metadata Tracking**
- Creation timestamp
- Image dimensions and properties
- Face detection information
- Format version for compatibility

### 4. **Error Handling**
- Graceful handling of corrupted files
- Automatic fallback for legacy format
- Detailed error messages

## API Endpoints

### Register Face
```http
POST /register-face
```
- Registers a new face encoding
- Stores encoding with metadata
- Returns creation timestamp and image info

### Verify Face
```http
POST /verify-face
```
- Loads stored encoding
- Compares with uploaded image
- Returns match result and confidence

### Get Face Status
```http
GET /students/{student_id}/face-status
```
- Returns registration status
- Includes metadata if available

### List All Encodings
```http
GET /encodings
```
- Lists all registered encodings
- Returns student IDs and metadata

### Delete Encoding
```http
DELETE /encodings/{student_id}
```
- Deletes encoding file
- Also removes backup if exists

### Update Encoding
```http
POST /encodings/{student_id}/update
```
- Updates existing encoding
- Creates backup of old encoding
- Returns new metadata

### Validate Encoding
```http
GET /encodings/{student_id}/validate
```
- Validates encoding file integrity
- Returns validation results and errors

## Functions

### Core Functions

- `get_student_face_encoding(student_id)` - Get encoding array
- `get_student_face_encoding_metadata(student_id)` - Get full metadata
- `save_student_face_encoding(student_id, encoding, image_info)` - Save with metadata
- `delete_student_face_encoding(student_id)` - Delete encoding
- `list_all_encodings()` - List all encodings
- `validate_encoding_file(student_id)` - Validate file integrity

## File Structure

```
face_recognition_service/
├── face_encodings/
│   ├── S001.pkl          # Student encoding
│   ├── S001.pkl.backup   # Backup (if updated)
│   ├── S002.pkl
│   └── ...
├── main.py
└── ...
```

## Security Considerations

1. **Local Storage Only**: All data stays on the server
2. **No Cloud Services**: No external dependencies
3. **File Permissions**: Ensure proper file system permissions
4. **Backup Strategy**: Consider regular backups of the `face_encodings/` directory

## Migration

The system automatically handles migration from Version 1.0 to 2.0:
- Old encodings (arrays only) are loaded correctly
- New encodings are saved in Version 2.0 format
- No manual migration needed

## Best Practices

1. **Regular Backups**: Backup the `face_encodings/` directory regularly
2. **Validation**: Periodically validate encodings using the validation endpoint
3. **Monitoring**: Monitor encoding file sizes and counts
4. **Cleanup**: Remove encodings for deleted students

## Example Usage

### Register a Face
```python
import requests

with open('student_photo.jpg', 'rb') as f:
    files = {'image': f}
    data = {'student_id': 'S001'}
    response = requests.post('http://localhost:8001/register-face', files=files, data=data)
    print(response.json())
```

### Verify a Face
```python
import requests

with open('verification_photo.jpg', 'rb') as f:
    files = {'image': f}
    data = {'student_id': 'S001'}
    response = requests.post('http://localhost:8001/verify-face', files=files, data=data)
    print(response.json())
```

### List All Encodings
```python
import requests

response = requests.get('http://localhost:8001/encodings')
print(response.json())
```

### Validate Encoding
```python
import requests

response = requests.get('http://localhost:8001/encodings/S001/validate')
print(response.json())
```

