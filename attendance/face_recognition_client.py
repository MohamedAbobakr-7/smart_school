"""
Face Recognition Service Client

This module handles communication with the FastAPI face recognition service.
"""

import requests
from typing import List, Optional, Dict, Any
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Face recognition service URL (from settings or default)
FACE_RECOGNITION_SERVICE_URL = getattr(
    settings, 
    'FACE_RECOGNITION_SERVICE_URL', 
    'http://localhost:8001'
)


class FaceRecognitionClient:
    """Client for interacting with the Face Recognition FastAPI service"""
    
    def __init__(self, base_url: str = None):
        """
        Initialize the face recognition client
        
        Args:
            base_url: Base URL of the face recognition service
        """
        self.base_url = base_url or FACE_RECOGNITION_SERVICE_URL
        self.timeout = getattr(settings, 'FACE_RECOGNITION_TIMEOUT', 30)
        # Batch detection uses CNN by default and can take much longer
        self.batch_timeout = getattr(settings, 'FACE_RECOGNITION_BATCH_TIMEOUT', 120)
    
    def verify_face(self, student_id: str, image_file) -> Dict[str, Any]:
        """
        Verify a face against a registered student
        
        Args:
            student_id: Student ID to verify against
            image_file: File-like object or bytes containing the image
            
        Returns:
            Dictionary with verification result:
            {
                'match': bool,
                'student_id': str,
                'confidence': float (optional),
                'message': str,
                'success': bool,
                'error': str (optional)
            }
        """
        try:
            url = f"{self.base_url}/verify-face"
            
            # Prepare the request
            files = {'image': image_file}
            params = {'student_id': student_id}
            
            # Make the request
            response = requests.post(
                url,
                files=files,
                params=params,
                timeout=self.timeout
            )
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'match': result.get('match', False),
                    'student_id': result.get('student_id', student_id),
                    'confidence': result.get('confidence'),
                    'message': result.get('message', ''),
                    'error': None
                }
            else:
                # Handle error responses
                error_detail = response.json().get('detail', 'Unknown error')
                logger.error(
                    f"Face recognition service error for student {student_id}: "
                    f"Status {response.status_code}, Detail: {error_detail}"
                )
                return {
                    'success': False,
                    'match': False,
                    'student_id': student_id,
                    'confidence': None,
                    'message': f"Face recognition service error: {error_detail}",
                    'error': error_detail
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Face recognition service timeout for student {student_id}")
            return {
                'success': False,
                'match': False,
                'student_id': student_id,
                'confidence': None,
                'message': 'Face recognition service timeout. Please try again.',
                'error': 'timeout'
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Face recognition service connection error for student {student_id}")
            return {
                'success': False,
                'match': False,
                'student_id': student_id,
                'confidence': None,
                'message': (
                    f'Cannot connect to face service at {self.base_url}. '
                    'Start it from the repo: run start_face_recognition_service.ps1 (or .bat), '
                    'or set env FACE_RECOGNITION_SERVICE_URL to the correct URL.'
                ),
                'error': 'connection_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error in face recognition for student {student_id}: {str(e)}")
            return {
                'success': False,
                'match': False,
                'student_id': student_id,
                'confidence': None,
                'message': f'An error occurred during face recognition: {str(e)}',
                'error': str(e)
            }
    
    def register_face(self, student_id: str, image_file) -> Dict[str, Any]:
        """
        Register a face for a student
        
        Args:
            student_id: Student ID
            image_file: File-like object or bytes containing the image
            
        Returns:
            Dictionary with registration result
        """
        try:
            url = f"{self.base_url}/register-face"
            
            files = {'image': image_file}
            params = {'student_id': student_id}
            
            response = requests.post(
                url,
                files=files,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message': result.get('message', 'Face registered successfully'),
                    'student_id': result.get('student_id', student_id),
                    'created_at': result.get('created_at'),
                    'error': None
                }
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                logger.error(
                    f"Face registration error for student {student_id}: "
                    f"Status {response.status_code}, Detail: {error_detail}"
                )
                return {
                    'success': False,
                    'message': f"Face registration error: {error_detail}",
                    'student_id': student_id,
                    'error': error_detail
                }
                
        except Exception as e:
            logger.error(f"Error registering face for student {student_id}: {str(e)}")
            return {
                'success': False,
                'message': f'An error occurred during face registration: {str(e)}',
                'student_id': student_id,
                'error': str(e)
            }
    
    def get_face_status(self, student_id: str) -> Dict[str, Any]:
        """
        Check if a student has a registered face
        
        Args:
            student_id: Student ID
            
        Returns:
            Dictionary with face status
        """
        try:
            url = f"{self.base_url}/students/{student_id}/face-status"
            
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    **response.json(),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'has_registered_face': False,
                    'error': response.json().get('detail', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"Error checking face status for student {student_id}: {str(e)}")
            return {
                'success': False,
                'has_registered_face': False,
                'error': str(e)
            }
    
    def detect_faces_batch(self, image_file, tolerance: float = 0.6, model: str = 'hog', num_jitters: int = 1, student_ids: Optional[list] = None) -> Dict[str, Any]:
        """
        Detect all faces in an image and match them against stored student encodings
        
        Args:
            image_file: File-like object or bytes containing the image
            tolerance: Face matching tolerance (0.0-1.0, lower = more strict)
            model: Detection model - 'hog' (faster, default) or 'cnn' (more accurate, slower)
            num_jitters: Number of times to re-sample face when encoding (higher = more accurate)
            student_ids: Optional list of student IDs to restrict matching to.
                Only encodings for these students will be loaded, preventing
                false-positive matches against students from other classes.
            
        Returns:
            Dictionary with batch detection results:
            {
                'success': bool,
                'num_faces_detected': int,
                'num_matches': int,
                'matches': list of match results,
                'image_info': dict,
                'message': str,
                'error': str (optional)
            }
        """
        try:
            url = f"{self.base_url}/detect-faces-batch"
            
            files = {'image': image_file}
            params = {
                'tolerance': tolerance,
                'model': model,
                'num_jitters': num_jitters
            }
            # Pass student_ids as comma-separated string so the face service
            # only loads encodings for students in the target class
            if student_ids:
                params['student_ids'] = ','.join(student_ids)
            
            response = requests.post(
                url,
                files=files,
                params=params,
                timeout=self.batch_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    **result,
                    'error': None
                }
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                logger.error(f"Batch face detection error: Status {response.status_code}, Detail: {error_detail}")
                return {
                    'success': False,
                    'num_faces_detected': 0,
                    'num_matches': 0,
                    'matches': [],
                    'message': f"Face detection service error: {error_detail}",
                    'error': error_detail
                }
                
        except requests.exceptions.Timeout:
            logger.error("Face detection service timeout")
            return {
                'success': False,
                'num_faces_detected': 0,
                'num_matches': 0,
                'matches': [],
                'message': 'Face detection service timeout. Please try again.',
                'error': 'timeout'
            }
        except requests.exceptions.ConnectionError:
            logger.error("Face detection service connection error")
            return {
                'success': False,
                'num_faces_detected': 0,
                'num_matches': 0,
                'matches': [],
                'message': (
                    f'Cannot connect to face service at {self.base_url}. '
                    'Start the FastAPI app in face_recognition_service/ (default http://localhost:8001), '
                    'or set FACE_RECOGNITION_SERVICE_URL in the environment / Django settings.'
                ),
                'error': 'connection_error'
            }
        except Exception as e:
            logger.error(f"Unexpected error in batch face detection: {str(e)}")
            return {
                'success': False,
                'num_faces_detected': 0,
                'num_matches': 0,
                'matches': [],
                'message': f'An error occurred during face detection: {str(e)}',
                'error': str(e)
            }


# Singleton instance
_face_recognition_client = None


def get_face_recognition_client() -> FaceRecognitionClient:
    """
    Get or create the face recognition client instance
    
    Returns:
        FaceRecognitionClient instance
    """
    global _face_recognition_client
    if _face_recognition_client is None:
        _face_recognition_client = FaceRecognitionClient()
    return _face_recognition_client

