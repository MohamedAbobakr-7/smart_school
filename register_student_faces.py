"""
Script to register student faces for face recognition

This script helps register face encodings for students so they can be
matched during batch attendance processing.

Usage:
    python register_student_faces.py
    # Or with specific student and image:
    python register_student_faces.py --student-id S001 --image path/to/student_photo.jpg
"""

import requests
import argparse
import os
import sys

FASTAPI_BASE_URL = "http://localhost:8001"


def register_face(student_id: str, image_path: str) -> bool:
    """
    Register a face encoding for a student
    
    Args:
        student_id: Student ID (e.g., 'S001')
        image_path: Path to image file with student's face
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(image_path):
        print(f"✗ Image not found: {image_path}")
        return False
    
    url = f"{FASTAPI_BASE_URL}/register-face"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
            params = {'student_id': student_id}
            
            response = requests.post(url, files=files, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Face registered successfully for {student_id}")
                print(f"  Image info: {result.get('image_info', {})}")
                return True
            else:
                print(f"[ERROR] Registration failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to FastAPI service at {FASTAPI_BASE_URL}")
        print("  Make sure the service is running: cd face_recognition_service && python main.py")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return False


def check_face_status(student_id: str) -> bool:
    """
    Check if a student has a registered face
    
    Args:
        student_id: Student ID
        
    Returns:
        True if face is registered, False otherwise
    """
    url = f"{FASTAPI_BASE_URL}/students/{student_id}/face-status"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            has_face = result.get('has_registered_face', False)
            
            if has_face:
                print(f"[OK] Student {student_id} has registered face")
                metadata = result.get('image_info', {})
                if metadata:
                    print(f"  Registered image: {metadata.get('width')}x{metadata.get('height')}")
            else:
                print(f"[WARNING] Student {student_id} does NOT have registered face")
            
            return has_face
        else:
            print(f"[ERROR] Failed to check status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error checking status: {str(e)}")
        return False


def list_all_registered() -> list:
    """
    List all students with registered faces
    
    Returns:
        List of student IDs with registered faces
    """
    url = f"{FASTAPI_BASE_URL}/encodings"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            encodings = result.get('encodings', [])
            
            student_ids = [enc.get('student_id') for enc in encodings if enc.get('student_id')]
            return student_ids
        else:
            print(f"[ERROR] Failed to list encodings: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"[ERROR] Error listing encodings: {str(e)}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Register student faces for face recognition')
    parser.add_argument('--student-id', '-s', help='Student ID (e.g., S001)')
    parser.add_argument('--image', '-i', help='Path to student photo')
    parser.add_argument('--check', '-c', help='Check if student has registered face', metavar='STUDENT_ID')
    parser.add_argument('--list', '-l', action='store_true', help='List all registered students')
    
    args = parser.parse_args()
    
    # Check if FastAPI service is running
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/", timeout=5)
        print("[OK] FastAPI service is running\n")
    except:
        print("[ERROR] FastAPI service is not running!")
        print("  Please start it: cd face_recognition_service && python main.py\n")
        sys.exit(1)
    
    # List all registered
    if args.list:
        print("Registered Students:")
        print("=" * 60)
        student_ids = list_all_registered()
        if student_ids:
            for sid in student_ids:
                print(f"  - {sid}")
            print(f"\nTotal: {len(student_ids)} students")
        else:
            print("  No students registered yet")
        return
    
    # Check status
    if args.check:
        print(f"Checking face status for {args.check}...")
        print("=" * 60)
        check_face_status(args.check)
        return
    
    # Register face
    if args.student_id and args.image:
        print(f"Registering face for {args.student_id}...")
        print("=" * 60)
        register_face(args.student_id, args.image)
        return
    
    # Interactive mode
    print("Student Face Registration")
    print("=" * 60)
    print("\nOptions:")
    print("1. Register a face")
    print("2. Check face status")
    print("3. List all registered students")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        student_id = input("Enter student ID (e.g., S001): ").strip()
        image_path = input("Enter image path: ").strip()
        
        if student_id and image_path:
            print()
            register_face(student_id, image_path)
        else:
            print("✗ Student ID and image path are required")
    
    elif choice == '2':
        student_id = input("Enter student ID to check: ").strip()
        if student_id:
            print()
            check_face_status(student_id)
        else:
            print("✗ Student ID is required")
    
    elif choice == '3':
        print()
        student_ids = list_all_registered()
        if student_ids:
            print("\nRegistered Students:")
            for sid in student_ids:
                print(f"  - {sid}")
            print(f"\nTotal: {len(student_ids)} students")
        else:
            print("No students registered yet")
    
    elif choice == '4':
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()

