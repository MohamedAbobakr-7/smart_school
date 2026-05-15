"""
Test script for Automated Face Recognition Attendance System

This script tests the new instructor-controlled batch attendance workflow:
1. Instructor login
2. Create attendance session
3. Process classroom image (batch face detection)
4. Complete session
5. View attendance records

Usage:
    python test_automated_attendance.py
"""

import requests
import json
import os
from pathlib import Path

# Configuration
DJANGO_BASE_URL = "http://localhost:8000"
FASTAPI_BASE_URL = "http://localhost:8001"

# Test credentials (adjust based on your test data)
# Default credentials match create_test_data command:
# Run: python manage.py create_test_data
INSTRUCTOR_USERNAME = "teacher1"  # Change to your instructor username
INSTRUCTOR_PASSWORD = "teacher123"  # Change to your instructor password

# Test image path (use a classroom photo with multiple faces)
# Use raw string (r"...") for Windows paths with backslashes
TEST_IMAGE_PATH = r"E:\WhatsApp Image 2026-04-07 at 3.37.35 PM.jpeg"  # Change to your test image


class AutomatedAttendanceTester:
    """Test class for automated attendance system"""
    
    def __init__(self):
        self.django_url = DJANGO_BASE_URL
        self.fastapi_url = FASTAPI_BASE_URL
        self.token = None
        self.headers = {}
        self.session_id = None
    
    def login(self, username, password):
        """Login as instructor and get JWT token"""
        print("\n" + "="*60)
        print("STEP 1: Instructor Login")
        print("="*60)
        
        url = f"{self.django_url}/api/auth/login/"
        data = {
            "username": username,
            "password": password
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            self.token = result.get('access')
            self.headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            print(f"[OK] Login successful")
            print(f"  User: {username}")
            print(f"  Token: {self.token[:50]}...")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Login failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text}")
            return False
    
    def test_fastapi_batch_detection(self, image_path):
        """Test FastAPI batch face detection endpoint"""
        print("\n" + "="*60)
        print("STEP 2: Test FastAPI Batch Face Detection")
        print("="*60)
        
        if not os.path.exists(image_path):
            print(f"[ERROR] Test image not found: {image_path}")
            print("  Skipping FastAPI test...")
            return False
        
        url = f"{self.fastapi_url}/detect-faces-batch"
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                params = {'tolerance': 0.6, 'model': 'hog'}  # HOG is faster than CNN
                
                response = requests.post(url, files=files, params=params, timeout=120)
                response.raise_for_status()
                
                result = response.json()
                
                print(f"[OK] Batch detection successful")
                print(f"  Faces detected: {result.get('num_faces_detected', 0)}")
                print(f"  Matches found: {result.get('num_matches', 0)}")
                
                matches = result.get('matches', [])
                if matches:
                    print(f"\n  Match details:")
                    for i, match in enumerate(matches[:5]):  # Show first 5
                        if match.get('match'):
                            print(f"    Face {i+1}: Student {match.get('student_id')} "
                                  f"(Confidence: {match.get('confidence', 0):.2f}%)")
                        else:
                            print(f"    Face {i+1}: No match "
                                  f"(Best confidence: {match.get('confidence', 0):.2f}%)")
                
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] FastAPI batch detection failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text}")
            return False
    
    def create_session(self, date=None, class_name="Test Class"):
        """Create a new attendance session"""
        print("\n" + "="*60)
        print("STEP 3: Create Attendance Session")
        print("="*60)
        
        from datetime import date as date_class
        if date is None:
            date = date_class.today().isoformat()
        
        url = f"{self.django_url}/api/attendance-sessions/"
        data = {
            "date": date,
            "class_name": class_name,
            "notes": "Automated test session"
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            self.session_id = result.get('id')
            
            print(f"[OK] Session created successfully")
            print(f"  Session ID: {self.session_id}")
            print(f"  Date: {result.get('date')}")
            print(f"  Class: {result.get('class_name')}")
            print(f"  Status: {result.get('status_display')}")
            print(f"  Instructor: {result.get('instructor_name')}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Session creation failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text}")
            return False
    
    def process_classroom_image(self, image_path):
        """Process classroom image for batch attendance"""
        print("\n" + "="*60)
        print("STEP 4: Process Classroom Image")
        print("="*60)
        
        if not os.path.exists(image_path):
            print(f"[ERROR] Test image not found: {image_path}")
            return False
        
        if not self.session_id:
            print("[ERROR] No active session. Create a session first.")
            return False
        
        url = f"{self.django_url}/api/attendance/process-classroom-image/"
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {'session_id': self.session_id}
                
                # Remove Content-Type header for multipart/form-data
                headers = {k: v for k, v in self.headers.items() if k != 'Content-Type'}
                
                response = requests.post(url, files=files, data=data, headers=headers, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                
                print(f"[OK] Image processed successfully")
                print(f"  Faces detected: {result.get('num_faces_detected', 0)}")
                print(f"  Matches found: {result.get('num_matches', 0)}")
                print(f"  Attendance marked: {result.get('num_attendance_marked', 0)}")
                
                matched_students = result.get('matched_students', [])
                if matched_students:
                    print(f"\n  Matched students ({len(matched_students)}):")
                    for student_id in matched_students[:10]:  # Show first 10
                        print(f"    - {student_id}")
                    if len(matched_students) > 10:
                        print(f"    ... and {len(matched_students) - 10} more")
                
                attendance_records = result.get('attendance_records', [])
                if attendance_records:
                    print(f"\n  Attendance records created:")
                    for att in attendance_records[:5]:  # Show first 5
                        print(f"    - {att.get('student_name')} ({att.get('student_id')}) "
                              f"- {att.get('date')} - {att.get('status_display')}")
                
                return True
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Image processing failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text}")
            return False
    
    def get_session_details(self):
        """Get session details"""
        if not self.session_id:
            return None
        
        url = f"{self.django_url}/api/attendance-sessions/{self.session_id}/"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def complete_session(self):
        """Complete the attendance session"""
        print("\n" + "="*60)
        print("STEP 5: Complete Session")
        print("="*60)
        
        if not self.session_id:
            print("[ERROR] No active session")
            return False
        
        url = f"{self.django_url}/api/attendance-sessions/{self.session_id}/complete/"
        
        try:
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            session = result.get('session', {})
            
            print(f"[OK] Session completed successfully")
            print(f"  Session ID: {session.get('id')}")
            print(f"  Status: {session.get('status_display')}")
            print(f"  Total faces detected: {session.get('total_faces_detected', 0)}")
            print(f"  Total matches: {session.get('total_matches', 0)}")
            print(f"  Total attendance marked: {session.get('total_attendance_marked', 0)}")
            print(f"  Completed at: {session.get('completed_at')}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Session completion failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response: {e.response.text}")
            return False
    
    def list_attendance(self, date=None):
        """List attendance records for today"""
        print("\n" + "="*60)
        print("STEP 6: View Attendance Records")
        print("="*60)
        
        from datetime import date as date_class
        if date is None:
            date = date_class.today().isoformat()
        
        url = f"{self.django_url}/api/attendance/"
        params = {'date': date}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            attendances = result.get('results', result) if isinstance(result, dict) else result
            
            if not isinstance(attendances, list):
                attendances = [attendances] if attendances else []
            
            print(f"[OK] Found {len(attendances)} attendance record(s) for {date}")
            
            face_recognition_count = sum(1 for att in attendances 
                                        if att.get('source') == 'face_recognition')
            
            print(f"  Face recognition: {face_recognition_count}")
            print(f"  Manual: {len(attendances) - face_recognition_count}")
            
            if attendances:
                print(f"\n  Recent records:")
                for att in attendances[:10]:  # Show first 10
                    source = att.get('source_display', att.get('source', 'unknown'))
                    print(f"    - {att.get('student_name')} ({att.get('student_id')}) "
                          f"- {att.get('status_display')} ({source})")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to list attendance: {e}")
            return False
    
    def run_full_test(self, image_path=None):
        """Run complete test workflow"""
        print("\n" + "="*80)
        print("AUTOMATED ATTENDANCE SYSTEM - FULL TEST")
        print("="*80)
        
        if image_path is None:
            image_path = TEST_IMAGE_PATH
        
        # Step 1: Login
        if not self.login(INSTRUCTOR_USERNAME, INSTRUCTOR_PASSWORD):
            print("\n[ERROR] Test failed at login step")
            return False
        
        # Step 2: Test FastAPI (optional)
        self.test_fastapi_batch_detection(image_path)
        
        # Step 3: Create session
        if not self.create_session():
            print("\n[ERROR] Test failed at session creation step")
            return False
        
        # Step 4: Process image
        if not self.process_classroom_image(image_path):
            print("\n[ERROR] Test failed at image processing step")
            return False
        
        # Step 5: View attendance
        self.list_attendance()
        
        # Step 6: Complete session
        if not self.complete_session():
            print("\n[ERROR] Test failed at session completion step")
            return False
        
        print("\n" + "="*80)
        print("[OK] ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        return True


def main():
    """Main test function"""
    import sys
    
    # Check if image path provided as argument
    image_path = sys.argv[1] if len(sys.argv) > 1 else TEST_IMAGE_PATH
    
    # Check if services are running
    print("Checking services...")
    try:
        django_check = requests.get(f"{DJANGO_BASE_URL}/api/", timeout=5)
        print(f"[OK] Django backend is running at {DJANGO_BASE_URL}")
    except:
        print(f"[ERROR] Django backend is not running at {DJANGO_BASE_URL}")
        print("  Please start Django: python manage.py runserver")
        return
    
    try:
        fastapi_check = requests.get(f"{FASTAPI_BASE_URL}/", timeout=5)
        print(f"[OK] FastAPI service is running at {FASTAPI_BASE_URL}")
    except:
        print(f"[ERROR] FastAPI service is not running at {FASTAPI_BASE_URL}")
        print("  Please start FastAPI: cd face_recognition_service && python main.py")
        print("  (Continuing with Django-only tests...)")
    
    # Run tests
    tester = AutomatedAttendanceTester()
    tester.run_full_test(image_path)


if __name__ == "__main__":
    main()

