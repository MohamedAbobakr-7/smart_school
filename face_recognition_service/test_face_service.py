"""
Test script for Face Recognition Service

Usage:
    python test_face_service.py
"""

import requests
import os

BASE_URL = "http://localhost:8001"

def test_register_face(student_id, image_path):
    """Test face registration"""
    print(f"\n{'='*60}")
    print(f"Testing: Register Face for {student_id}")
    print(f"{'='*60}")
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return False
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {'student_id': student_id}
        response = requests.post(f"{BASE_URL}/register-face", files=files, data=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200


def test_verify_face(student_id, image_path):
    """Test face verification"""
    print(f"\n{'='*60}")
    print(f"Testing: Verify Face for {student_id}")
    print(f"{'='*60}")
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return False
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {'student_id': student_id}
        response = requests.post(f"{BASE_URL}/verify-face", files=files, data=data)
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {result}")
    
    if response.status_code == 200:
        print(f"Match: {result.get('match')}")
        print(f"Confidence: {result.get('confidence')}%")
    
    return response.status_code == 200


def test_face_status(student_id):
    """Test face status check"""
    print(f"\n{'='*60}")
    print(f"Testing: Face Status for {student_id}")
    print(f"{'='*60}")
    
    response = requests.get(f"{BASE_URL}/students/{student_id}/face-status")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FACE RECOGNITION SERVICE - TESTING")
    print("="*60)
    
    # Test root endpoint
    print("\n1. Testing Root Endpoint")
    print("-" * 60)
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test face status (before registration)
    print("\n2. Testing Face Status (Before Registration)")
    test_face_status("S001")
    
    # Test register face (you need to provide an image file)
    print("\n3. Testing Face Registration")
    print("Note: You need to provide a path to a student photo")
    # Uncomment and provide image path:
    # test_register_face("S001", "path/to/student_photo.jpg")
    
    # Test verify face (you need to provide an image file)
    print("\n4. Testing Face Verification")
    print("Note: You need to provide a path to a photo for verification")
    # Uncomment and provide image path:
    # test_verify_face("S001", "path/to/verification_photo.jpg")
    
    # Test face status (after registration)
    print("\n5. Testing Face Status (After Registration)")
    test_face_status("S001")
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\nTo test with actual images:")
    print("1. Prepare student photos")
    print("2. Uncomment the test_register_face and test_verify_face calls")
    print("3. Update the image paths")

