"""
API Testing Script for Smart School Backend

This script helps test all the API endpoints.
Make sure the Django server is running: python manage.py runserver

Usage:
    python test_api.py
"""

import requests
import json
from datetime import date, timedelta

# Base URL - adjust if your server runs on a different port
BASE_URL = "http://localhost:8000/api"

# Test credentials (you'll need to create these users first)
TEST_CREDENTIALS = {
    'admin': {'username': 'admin', 'password': 'admin123'},
    'teacher': {'username': 'teacher1', 'password': 'teacher123'},
    'student': {'username': 'student1', 'password': 'student123'},
    'parent': {'username': 'parent1', 'password': 'parent123'},
}

class APITester:
    def __init__(self):
        self.tokens = {}
        self.headers = {}
    
    def login(self, username, password):
        """Login and get JWT token"""
        url = f"{BASE_URL}/auth/login/"
        response = requests.post(url, json={'username': username, 'password': password})
        if response.status_code == 200:
            data = response.json()
            token = data['access']
            self.tokens[username] = token
            self.headers[username] = {'Authorization': f'Bearer {token}'}
            print(f"[OK] Logged in as {username}")
            return True
        else:
            print(f"[FAIL] Login failed for {username}: {response.status_code} - {response.text}")
            return False
    
    def test_endpoint(self, method, endpoint, username=None, data=None, description=""):
        """Test an API endpoint"""
        url = f"{BASE_URL}{endpoint}"
        headers = self.headers.get(username, {}) if username else {}
        
        print(f"\n{'='*60}")
        print(f"Testing: {description}")
        print(f"Method: {method} | Endpoint: {endpoint}")
        if username:
            print(f"User: {username}")
        print(f"{'='*60}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code < 400:
                print("[SUCCESS]")
                try:
                    result = response.json()
                    if isinstance(result, dict) and 'results' in result:
                        print(f"Results: {len(result['results'])} items")
                    elif isinstance(result, list):
                        print(f"Results: {len(result)} items")
                    else:
                        print(f"Response: {json.dumps(result, indent=2)[:200]}...")
                except:
                    print(f"Response: {response.text[:200]}")
            else:
                print("[FAILED]")
                print(f"Error: {response.text[:200]}")
            
            return response
        except Exception as e:
            print(f"[ERROR]: {str(e)}")
            return None
    
    def run_tests(self):
        """Run all API tests"""
        print("\n" + "="*60)
        print("SMART SCHOOL BACKEND - API TESTING")
        print("="*60)
        
        # Test 1: Login
        print("\n1. Testing Authentication")
        print("-" * 60)
        for role, creds in TEST_CREDENTIALS.items():
            self.login(creds['username'], creds['password'])
        
        # Test 2: User endpoints
        print("\n2. Testing User Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/users/', 'admin', description="List all users (Admin)")
        self.test_endpoint('GET', '/users/me/', 'admin', description="Get current user profile")
        
        # Test 3: Student endpoints
        print("\n3. Testing Student Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/students/', 'admin', description="List all students (Admin)")
        self.test_endpoint('GET', '/students/', 'student1', description="List students (Student - own only)")
        
        # Test 4: Teacher endpoints
        print("\n4. Testing Teacher Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/teachers/', 'teacher1', description="List all teachers")
        
        # Test 5: Subject endpoints
        print("\n5. Testing Subject Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/subjects/', 'teacher1', description="List all subjects")
        
        # Test 6: Attendance endpoints
        print("\n6. Testing Attendance Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/attendance/', 'teacher1', description="List all attendance (Teacher)")
        self.test_endpoint('GET', '/attendance/', 'student1', description="List attendance (Student - own only)")
        
        # Test 7: Exam endpoints
        print("\n7. Testing Exam Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/exams/', 'teacher1', description="List all exams (Teacher)")
        self.test_endpoint('GET', '/exams/', 'student1', description="List exams (Student)")
        
        # Test 8: Question endpoints
        print("\n8. Testing Question Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/questions/', 'teacher1', description="List all questions (Teacher)")
        
        # Test 9: Grade endpoints
        print("\n9. Testing Grade Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/grades/', 'teacher1', description="List all grades (Teacher)")
        self.test_endpoint('GET', '/grades/', 'student1', description="List grades (Student - own only)")
        
        # Test 10: Parent endpoints
        print("\n10. Testing Parent Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/parents/', 'parent1', description="List parents (Parent - own only)")
        
        # Test 11: Report endpoints
        print("\n11. Testing Report Endpoints")
        print("-" * 60)
        self.test_endpoint('GET', '/reports/', 'teacher1', description="List all reports (Teacher)")
        
        print("\n" + "="*60)
        print("TESTING COMPLETE")
        print("="*60)

if __name__ == "__main__":
    tester = APITester()
    tester.run_tests()

