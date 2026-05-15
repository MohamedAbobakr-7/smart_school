"""
FastAPI Face Recognition Service for Smart School Backend

This service handles face recognition for attendance tracking.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import face_recognition
import cv2
import numpy as np
import os
import pickle
import asyncio
from pathlib import Path
import pyodbc
from datetime import datetime

app = FastAPI(
    title="Face Recognition Service",
    description="Face recognition service for student attendance",
    version="1.0.0"
)

# CORS middleware to allow requests from Django backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Django backend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection settings (from environment variables)
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'server': os.getenv('DB_HOST', 'DESKTOP-2ASDU43\\SQLEXPRESS'),
    'database': os.getenv('DB_NAME', 'smart-school'),
    'driver': 'ODBC Driver 17 for SQL Server',
    'trusted_connection': 'yes',
    'TrustServerCertificate': 'yes'
}

# Directory to store face encodings
FACE_ENCODINGS_DIR = Path("face_encodings")
FACE_ENCODINGS_DIR.mkdir(exist_ok=True)


class FaceVerificationRequest(BaseModel):
    """Request model for face verification"""
    student_id: str


class FaceVerificationResponse(BaseModel):
    """Response model for face verification"""
    match: bool
    student_id: str
    confidence: Optional[float] = None
    message: str


def get_db_connection():
    """Get database connection"""
    try:
        conn_str = (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
            f"TrustServerCertificate={DB_CONFIG['TrustServerCertificate']};"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


def get_student_face_encoding(student_id: str) -> Optional[np.ndarray]:
    """
    Get stored face encoding for a student
    
    Args:
        student_id: Student ID
        
    Returns:
        Face encoding array or None if not found
    """
    encoding_file = FACE_ENCODINGS_DIR / f"{student_id}.pkl"
    
    if not encoding_file.exists():
        return None
    
    try:
        with open(encoding_file, 'rb') as f:
            data = pickle.load(f)
            # Handle both old format (just encoding) and new format (dict with metadata)
            if isinstance(data, dict):
                encoding = data.get('encoding')
                if encoding is None:
                    return None
                # Validate encoding shape
                if not isinstance(encoding, np.ndarray) or encoding.shape != (128,):
                    return None
                return encoding
            elif isinstance(data, np.ndarray):
                # Old format - just the encoding array
                if data.shape == (128,):
                    return data
        return None
    except Exception as e:
        print(f"Error loading encoding for {student_id}: {str(e)}")
        return None


def get_student_face_encoding_metadata(student_id: str) -> Optional[dict]:
    """
    Get face encoding metadata for a student
    
    Args:
        student_id: Student ID
        
    Returns:
        Dictionary with encoding metadata or None if not found
    """
    encoding_file = FACE_ENCODINGS_DIR / f"{student_id}.pkl"
    
    if not encoding_file.exists():
        return None
    
    try:
        with open(encoding_file, 'rb') as f:
            data = pickle.load(f)
            if isinstance(data, dict):
                return data
            elif isinstance(data, np.ndarray):
                # Old format - return minimal metadata
                return {
                    'encoding': data,
                    'created_at': None,
                    'student_id': student_id,
                    'format_version': '1.0'
                }
        return None
    except Exception as e:
        print(f"Error loading encoding metadata for {student_id}: {str(e)}")
        return None


def save_student_face_encoding(
    student_id: str, 
    encoding: np.ndarray,
    image_info: Optional[dict] = None
):
    """
    Save face encoding for a student with metadata
    
    Args:
        student_id: Student ID
        encoding: Face encoding array (must be shape (128,))
        image_info: Optional dictionary with image metadata (size, format, etc.)
    """
    if not isinstance(encoding, np.ndarray) or encoding.shape != (128,):
        raise ValueError(f"Invalid encoding shape. Expected (128,), got {encoding.shape}")
    
    encoding_file = FACE_ENCODINGS_DIR / f"{student_id}.pkl"
    
    # Create encoding data with metadata
    encoding_data = {
        'encoding': encoding,
        'student_id': student_id,
        'created_at': datetime.now().isoformat(),
        'format_version': '2.0',
        'encoding_shape': encoding.shape,
        'image_info': image_info or {}
    }
    
    try:
        # Create backup of existing encoding if it exists
        if encoding_file.exists():
            backup_file = FACE_ENCODINGS_DIR / f"{student_id}.pkl.backup"
            if not backup_file.exists():
                import shutil
                shutil.copy2(encoding_file, backup_file)
        
        # Save encoding with metadata
        with open(encoding_file, 'wb') as f:
            pickle.dump(encoding_data, f)
        
        return True
    except Exception as e:
        print(f"Error saving encoding for {student_id}: {str(e)}")
        raise


def delete_student_face_encoding(student_id: str) -> bool:
    """
    Delete face encoding for a student
    
    Args:
        student_id: Student ID
        
    Returns:
        True if deleted, False if not found
    """
    encoding_file = FACE_ENCODINGS_DIR / f"{student_id}.pkl"
    
    if not encoding_file.exists():
        return False
    
    try:
        encoding_file.unlink()
        # Also delete backup if exists
        backup_file = FACE_ENCODINGS_DIR / f"{student_id}.pkl.backup"
        if backup_file.exists():
            backup_file.unlink()
        return True
    except Exception as e:
        print(f"Error deleting encoding for {student_id}: {str(e)}")
        return False


def list_all_encodings() -> list:
    """
    List all stored face encodings
    
    Returns:
        List of dictionaries with student_id and metadata
    """
    encodings = []
    
    if not FACE_ENCODINGS_DIR.exists():
        return encodings
    
    for encoding_file in FACE_ENCODINGS_DIR.glob("*.pkl"):
        if encoding_file.name.endswith(".backup"):
            continue
        
        student_id = encoding_file.stem
        metadata = get_student_face_encoding_metadata(student_id)
        
        if metadata:
            encodings.append({
                'student_id': student_id,
                'created_at': metadata.get('created_at'),
                'has_encoding': metadata.get('encoding') is not None,
                'file_size': encoding_file.stat().st_size
            })
    
    return encodings


def validate_encoding_file(student_id: str) -> dict:
    """
    Validate encoding file integrity
    
    Args:
        student_id: Student ID
        
    Returns:
        Dictionary with validation results
    """
    encoding_file = FACE_ENCODINGS_DIR / f"{student_id}.pkl"
    
    result = {
        'student_id': student_id,
        'exists': False,
        'valid': False,
        'has_encoding': False,
        'errors': []
    }
    
    if not encoding_file.exists():
        result['errors'].append("Encoding file does not exist")
        return result
    
    result['exists'] = True
    
    try:
        metadata = get_student_face_encoding_metadata(student_id)
        if metadata is None:
            result['errors'].append("Failed to load encoding file")
            return result
        
        encoding = metadata.get('encoding')
        if encoding is None:
            result['errors'].append("No encoding found in file")
            return result
        
        if not isinstance(encoding, np.ndarray):
            result['errors'].append("Encoding is not a numpy array")
            return result
        
        if encoding.shape != (128,):
            result['errors'].append(f"Invalid encoding shape: {encoding.shape}, expected (128,)")
            return result
        
        result['has_encoding'] = True
        result['valid'] = True
        result['metadata'] = {
            'created_at': metadata.get('created_at'),
            'format_version': metadata.get('format_version'),
            'image_info': metadata.get('image_info', {})
        }
        
    except Exception as e:
        result['errors'].append(f"Validation error: {str(e)}")
    
    return result


def verify_student_exists(student_id: str) -> bool:
    """
    Verify that student exists in the database
    
    Args:
        student_id: Student ID
        
    Returns:
        True if student exists, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students WHERE student_id = ?", (student_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error checking student: {str(e)}")
        return False


def process_image(image_bytes: bytes) -> tuple[Optional[np.ndarray], Optional[dict]]:
    """
    Process image and extract face encoding with image metadata
    
    Args:
        image_bytes: Image file bytes
        
    Returns:
        Tuple of (face encoding array or None, image metadata dict or None)
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None, None
        
        # Get image metadata
        height, width = img.shape[:2]
        image_info = {
            'width': width,
            'height': height,
            'channels': img.shape[2] if len(img.shape) > 2 else 1,
            'size_bytes': len(image_bytes)
        }
        
        # Convert BGR to RGB (face_recognition uses RGB)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Find face locations
        face_locations = face_recognition.face_locations(rgb_img)
        
        if len(face_locations) == 0:
            return None, image_info
        
        # Get face encodings (use first face if multiple found)
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
        
        if len(face_encodings) == 0:
            return None, image_info
        
        # Add face location info to metadata
        image_info['face_location'] = face_locations[0]
        image_info['num_faces_detected'] = len(face_locations)
        
        return face_encodings[0], image_info
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None, None


def process_image_batch(image_bytes: bytes, model: str = 'hog', num_jitters: int = 1) -> tuple[list, dict]:
    """
    Process image and extract ALL face encodings (batch detection)
    
    Args:
        image_bytes: Image file bytes
        model: Detection model - 'hog' (faster, less accurate) or 'cnn' (slower, more accurate)
        num_jitters: Number of times to re-sample the face when calculating encoding (higher = more accurate)
        
    Returns:
        Tuple of (list of face encodings, image metadata dict)
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return [], {}
        
        # Get image metadata
        height, width = img.shape[:2]
        image_info = {
            'width': width,
            'height': height,
            'channels': img.shape[2] if len(img.shape) > 2 else 1,
            'size_bytes': len(image_bytes)
        }
        
        # Convert BGR to RGB (face_recognition uses RGB)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Use requested model only (HOG recommended on CPU; CNN is slow without GPU)
        face_locations = face_recognition.face_locations(rgb_img, model=model)
        image_info['detection_model_used'] = model
        
        # If no faces found, try with upsample for smaller faces (same model, no CNN fallback)
        if len(face_locations) == 0:
            print("No faces found, trying with upsample (for smaller faces)...")
            face_locations = face_recognition.face_locations(rgb_img, model=model, number_of_times_to_upsample=2)
            if len(face_locations) > 0:
                image_info['detection_model_used'] = f'{model}_upsampled'
        
        if len(face_locations) == 0:
            image_info['num_faces_detected'] = 0
            image_info['message'] = 'No faces detected. Try: better lighting, higher resolution, or different angle.'
            return [], image_info
        
        # Get all face encodings with jittering for better accuracy
        face_encodings = face_recognition.face_encodings(
            rgb_img, 
            face_locations,
            num_jitters=num_jitters
        )
        
        # Add face location info to metadata
        image_info['face_locations'] = face_locations
        image_info['num_faces_detected'] = len(face_locations)
        image_info['num_encodings_generated'] = len(face_encodings)
        
        print(f"Detected {len(face_locations)} face(s) using {image_info.get('detection_model_used', model)} model")
        
        return face_encodings, image_info
    except Exception as e:
        print(f"Error processing image batch: {str(e)}")
        import traceback
        traceback.print_exc()
        return [], {}


def match_faces_batch(face_encodings: list, tolerance: float = 0.6) -> list:
    """
    Match multiple face encodings against all stored student encodings
    
    Args:
        face_encodings: List of face encoding arrays to match
        tolerance: Matching tolerance (lower = more strict)
        
    Returns:
        List of match results, each containing:
        {
            'face_index': int,
            'student_id': str or None,
            'match': bool,
            'confidence': float or None,
            'face_location': tuple or None
        }
    """
    matches = []
    
    # Get all student encodings
    if not FACE_ENCODINGS_DIR.exists():
        return matches
    
    # Load all student encodings
    student_encodings = {}
    for encoding_file in FACE_ENCODINGS_DIR.glob("*.pkl"):
        if encoding_file.name.endswith(".backup"):
            continue
        
        student_id = encoding_file.stem
        encoding = get_student_face_encoding(student_id)
        if encoding is not None:
            student_encodings[student_id] = encoding
    
    if not student_encodings:
        return matches
    
    # Convert to lists for batch comparison
    student_ids = list(student_encodings.keys())
    stored_encodings = list(student_encodings.values())
    
    # Match each detected face
    for idx, face_encoding in enumerate(face_encodings):
        match_result = {
            'face_index': idx,
            'student_id': None,
            'match': False,
            'confidence': None,
            'face_location': None
        }
        
        # Compare with all stored encodings
        face_distances = face_recognition.face_distance(stored_encodings, face_encoding)
        best_match_index = face_distances.argmin()
        best_distance = face_distances[best_match_index]
        
        # Check if match is within tolerance
        if best_distance <= tolerance:
            match_result['match'] = True
            match_result['student_id'] = student_ids[best_match_index]
            match_result['confidence'] = max(0, (1 - best_distance) * 100)
        else:
            match_result['confidence'] = max(0, (1 - best_distance) * 100)
        
        matches.append(match_result)
    
    return matches


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Face Recognition Service",
        "version": "1.0.0",
        "endpoints": {
            "verify_face": "POST /verify-face",
            "register_face": "POST /register-face"
        }
    }


@app.post("/verify-face", response_model=FaceVerificationResponse)
async def verify_face(
    student_id: str,
    image: UploadFile = File(...)
):
    """
    Verify if the uploaded face image matches the registered face for the student
    
    Args:
        student_id: Student ID to verify against
        image: Image file containing face
        
    Returns:
        FaceVerificationResponse with match result
    """
    # Verify student exists
    if not verify_student_exists(student_id):
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Check if student has registered face
    stored_encoding = get_student_face_encoding(student_id)
    if stored_encoding is None:
        return FaceVerificationResponse(
            match=False,
            student_id=student_id,
            message=f"No face registered for student {student_id}. Please register face first."
        )
    
    # Read image file
    image_bytes = await image.read()
    
    # Process image and extract face encoding
    face_encoding, image_info = process_image(image_bytes)
    
    if face_encoding is None:
        raise HTTPException(
            status_code=400,
            detail="No face detected in the image. Please upload an image with a clear face."
        )
    
    # Compare faces
    # face_recognition.compare_faces returns a list of boolean values
    # tolerance is how much distance between faces to consider it a match (lower = more strict)
    matches = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)
    match = matches[0]
    
    # Calculate face distance for confidence
    face_distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
    confidence = max(0, (1 - face_distance) * 100)  # Convert to percentage
    
    if match:
        return FaceVerificationResponse(
            match=True,
            student_id=student_id,
            confidence=round(confidence, 2),
            message=f"Face verified successfully for student {student_id}"
        )
    else:
        return FaceVerificationResponse(
            match=False,
            student_id=student_id,
            confidence=round(confidence, 2),
            message=f"Face does not match registered face for student {student_id}"
        )


@app.post("/register-face")
async def register_face(
    student_id: str,
    image: UploadFile = File(...)
):
    """
    Register a face encoding for a student
    
    Args:
        student_id: Student ID
        image: Image file containing face to register
        
    Returns:
        Success message
    """
    # Verify student exists
    if not verify_student_exists(student_id):
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Read image file
    image_bytes = await image.read()
    
    # Process image and extract face encoding
    face_encoding, image_info = process_image(image_bytes)
    
    if face_encoding is None:
        raise HTTPException(
            status_code=400,
            detail="No face detected in the image. Please upload an image with a clear face."
        )
    
    # Save face encoding with metadata
    save_student_face_encoding(student_id, face_encoding, image_info)
    
    # Get metadata for response
    metadata = get_student_face_encoding_metadata(student_id)
    
    return {
        "success": True,
        "message": f"Face registered successfully for student {student_id}",
        "student_id": student_id,
        "created_at": metadata.get('created_at') if metadata else None,
        "image_info": image_info
    }


@app.get("/students/{student_id}/face-status")
async def get_face_status(student_id: str):
    """
    Check if a student has a registered face with metadata
    
    Args:
        student_id: Student ID
        
    Returns:
        Status of face registration with metadata
    """
    # Verify student exists
    if not verify_student_exists(student_id):
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    metadata = get_student_face_encoding_metadata(student_id)
    has_face = metadata is not None and metadata.get('encoding') is not None
    
    response = {
        "student_id": student_id,
        "has_registered_face": has_face,
        "message": "Face registered" if has_face else "No face registered"
    }
    
    if has_face and metadata:
        response.update({
            "created_at": metadata.get('created_at'),
            "format_version": metadata.get('format_version'),
            "image_info": metadata.get('image_info', {})
        })
    
    return response


@app.get("/encodings")
async def list_encodings():
    """
    List all stored face encodings
    
    Returns:
        List of all registered face encodings with metadata
    """
    encodings = list_all_encodings()
    
    return {
        "total": len(encodings),
        "encodings": encodings
    }


@app.delete("/encodings/{student_id}")
async def delete_encoding(student_id: str):
    """
    Delete face encoding for a student
    
    Args:
        student_id: Student ID
        
    Returns:
        Success message
    """
    # Verify student exists
    if not verify_student_exists(student_id):
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    deleted = delete_student_face_encoding(student_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"No face encoding found for student {student_id}"
        )
    
    return {
        "success": True,
        "message": f"Face encoding deleted successfully for student {student_id}",
        "student_id": student_id
    }


@app.get("/encodings/{student_id}/validate")
async def validate_encoding(student_id: str):
    """
    Validate face encoding file integrity
    
    Args:
        student_id: Student ID
        
    Returns:
        Validation results
    """
    # Verify student exists
    if not verify_student_exists(student_id):
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    validation_result = validate_encoding_file(student_id)
    
    return validation_result


@app.post("/encodings/{student_id}/update")
async def update_encoding(
    student_id: str,
    image: UploadFile = File(...)
):
    """
    Update face encoding for a student (re-register face)
    
    Args:
        student_id: Student ID
        image: New image file containing face
        
    Returns:
        Success message with new metadata
    """
    # Verify student exists
    if not verify_student_exists(student_id):
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Read image file
    image_bytes = await image.read()
    
    # Process image and extract face encoding
    face_encoding, image_info = process_image(image_bytes)
    
    if face_encoding is None:
        raise HTTPException(
            status_code=400,
            detail="No face detected in the image. Please upload an image with a clear face."
        )
    
    # Save face encoding with metadata (will create backup of old one)
    save_student_face_encoding(student_id, face_encoding, image_info)
    
    # Get metadata for response
    metadata = get_student_face_encoding_metadata(student_id)
    
    return {
        "success": True,
        "message": f"Face encoding updated successfully for student {student_id}",
        "student_id": student_id,
        "created_at": metadata.get('created_at') if metadata else None,
        "image_info": image_info
    }


def _run_batch_detection(image_bytes: bytes, model: str, num_jitters: int, tolerance: float):
    """Run CPU-bound batch detection in a thread (called via asyncio.to_thread)."""
    face_encodings, image_info = process_image_batch(image_bytes, model=model, num_jitters=num_jitters)
    matches = match_faces_batch(face_encodings, tolerance) if face_encodings else []
    return face_encodings, image_info, matches


@app.post("/detect-faces-batch")
async def detect_faces_batch(
    image: UploadFile = File(...),
    tolerance: float = 0.6,
    model: str = 'hog',
    num_jitters: int = 1
):
    """
    Detect all faces in an image and match them against stored student encodings
    
    This endpoint is used for batch attendance marking where an instructor
    captures a classroom image and the system automatically detects and matches
    all faces to students.
    
    Args:
        image: Image file containing multiple faces
        tolerance: Face matching tolerance (0.0-1.0, lower = more strict)
        model: Detection model - 'hog' (faster, default) or 'cnn' (slower, more accurate)
        num_jitters: Number of times to re-sample face when encoding (higher = more accurate)
        
    Returns:
        Dictionary with:
        - num_faces_detected: Number of faces found
        - matches: List of match results for each face
        - image_info: Image metadata
    """
    image_bytes = await image.read()
    
    # Run CPU-bound face detection and matching in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    if hasattr(asyncio, 'to_thread'):
        face_encodings, image_info, matches = await asyncio.to_thread(
            _run_batch_detection, image_bytes, model, num_jitters, tolerance
        )
    else:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            face_encodings, image_info, matches = await loop.run_in_executor(
                pool, lambda: _run_batch_detection(image_bytes, model, num_jitters, tolerance)
            )
    
    if len(face_encodings) == 0:
        return {
            "success": True,
            "num_faces_detected": 0,
            "matches": [],
            "image_info": image_info,
            "message": "No faces detected in the image"
        }
    
    # Add face locations to matches if available
    if 'face_locations' in image_info:
        for i, match in enumerate(matches):
            if i < len(image_info['face_locations']):
                match['face_location'] = image_info['face_locations'][i]
    
    # Count successful matches
    successful_matches = sum(1 for m in matches if m['match'])
    
    return {
        "success": True,
        "num_faces_detected": len(face_encodings),
        "num_matches": successful_matches,
        "matches": matches,
        "image_info": image_info,
        "message": f"Detected {len(face_encodings)} face(s), matched {successful_matches} student(s)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

