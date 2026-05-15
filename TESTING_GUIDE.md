# Smart School Backend - Testing Guide

This guide will help you test all the features of the Smart School Backend system.

## Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Start the Development Server**
   ```bash
   python manage.py runserver
   ```

## Step 1: Create Test Data

Create test users and sample data:

```bash
python manage.py create_test_data
```

This will create:
- **Admin User**: `admin` / `admin123`
- **Teacher User**: `teacher1` / `teacher123`
- **Student User**: `student2` / `student123`
- **Parent User**: `parent1` / `parent123`

Plus sample data for:
- Students, Teachers, Parents
- Subjects
- Attendance records
- Exams with questions
- Grades
- Reports

## Step 2: Test Authentication (JWT)

### Login Endpoint

**POST** `/api/auth/login/`

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@school.com",
    "role": "ADMIN",
    "role_display": "Admin"
  }
}
```

### Refresh Token

**POST** `/api/auth/refresh/`

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

## Step 3: Test API Endpoints

### Using Python Script

Run the automated test script:

```bash
python test_api.py
```

This will test all endpoints with different user roles.

### Manual Testing with cURL

#### 1. Get Current User Profile

```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 2. List All Users (Admin only)

```bash
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

#### 3. List Students

```bash
curl -X GET http://localhost:8000/api/students/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 4. List Exams

```bash
curl -X GET http://localhost:8000/api/exams/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 5. Get Exam Details (with questions)

```bash
curl -X GET http://localhost:8000/api/exams/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 6. List Questions

```bash
curl -X GET http://localhost:8000/api/questions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 7. List Grades

```bash
curl -X GET http://localhost:8000/api/grades/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 8. List Attendance

```bash
curl -X GET http://localhost:8000/api/attendance/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Step 4: Test Role-Based Access Control

### Test as Admin

1. Login as admin
2. Try accessing all endpoints - should have full access
3. Try creating/updating/deleting resources

### Test as Teacher

1. Login as teacher1
2. Should be able to:
   - View all students, exams, grades, attendance
   - Create/update exams, questions, grades, attendance
   - Cannot create/delete users (admin only)

### Test as Student

1. Login as student1
2. Should be able to:
   - View own profile, grades, exams, attendance
   - Cannot see other students' data
   - Cannot create/update/delete resources

### Test as Parent

1. Login as parent1
2. Should be able to:
   - View own profile
   - View children's grades, exams, attendance
   - Cannot see other students' data
   - Cannot create/update/delete resources

## Step 5: Test Creating Resources

### Create an Exam (Teacher/Admin only)

```bash
curl -X POST http://localhost:8000/api/exams/ \
  -H "Authorization: Bearer TEACHER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Final Exam 2024",
    "subject": 1,
    "teacher": 1,
    "duration": 90
  }'
```

### Create a Question (Teacher/Admin only)

```bash
curl -X POST http://localhost:8000/api/questions/ \
  -H "Authorization: Bearer TEACHER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exam": 1,
    "text": "What is the capital of France?",
    "options": ["London", "Berlin", "Paris", "Madrid"],
    "correct_answer": 2
  }'
```

### Create a Grade (Teacher/Admin only)

```bash
curl -X POST http://localhost:8000/api/grades/ \
  -H "Authorization: Bearer TEACHER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student": 1,
    "exam": 1,
    "score": 8.5
  }'
```

### Create Attendance (Teacher/Admin only)

```bash
curl -X POST http://localhost:8000/api/attendance/ \
  -H "Authorization: Bearer TEACHER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student": 1,
    "date": "2024-01-15",
    "status": "present",
    "source": "manual",
    "marked_by": 1
  }'
```

## Step 6: Test Using Django Shell

Test models and relationships:

```bash
python manage.py shell
```

```python
from users.models import User
from students.models import Student
from teachers.models import Teacher
from subjects.models import Subject
from exams.models import Exam, Question, Grade

# Test User roles
admin = User.objects.get(username='admin')
print(admin.is_admin())  # True
print(admin.role)  # ADMIN

# Test Student-Parent relationship
student = Student.objects.first()
print(student.parent)  # Parent object
print(student.parent.children.all())  # All children of parent

# Test Teacher-Subject relationship
teacher = Teacher.objects.first()
print(teacher.assigned_subjects.all())  # All subjects assigned to teacher

# Test Exam-Question relationship
exam = Exam.objects.first()
print(exam.questions.count())  # Number of questions
print(exam.get_questions_count())  # Helper method

# Test Grade calculations
grade = Grade.objects.first()
print(grade.get_percentage())  # Percentage score
print(grade.get_grade_letter())  # Letter grade (A, B, C, D, F)

# Test Attendance
from attendance.models import Attendance
attendance = Attendance.objects.first()
print(attendance.status)  # present or absent
print(attendance.source)  # manual or face_recognition
```

## Step 7: Test Constraints and Validations

### Test Duplicate Attendance (should fail)

```bash
curl -X POST http://localhost:8000/api/attendance/ \
  -H "Authorization: Bearer TEACHER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student": 1,
    "date": "2024-01-15",
    "status": "present",
    "source": "manual"
  }'
```

Should return error: "Attendance record already exists for this student on 2024-01-15"

### Test Duplicate Grade (should fail)

```bash
curl -X POST http://localhost:8000/api/grades/ \
  -H "Authorization: Bearer TEACHER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student": 1,
    "exam": 1,
    "score": 9.0
  }'
```

Should return error: "Grade already exists for this student and exam"

### Test Invalid Question (should fail)

```bash
curl -X POST http://localhost:8000/api/questions/ \
  -H "Authorization: Bearer TEACHER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exam": 1,
    "text": "Test question",
    "options": ["A", "B"],
    "correct_answer": 5
  }'
```

Should return error: "correct_answer index (5) must be less than number of options (2)"

## Step 8: Test Using Postman or Insomnia

1. **Import Collection**: Create a Postman collection with all endpoints
2. **Set Environment Variables**:
   - `base_url`: `http://localhost:8000/api`
   - `admin_token`: (get from login)
   - `teacher_token`: (get from login)
   - `student_token`: (get from login)
   - `parent_token`: (get from login)

3. **Test Workflow**:
   - Login → Get token
   - Use token in Authorization header: `Bearer {token}`
   - Test all CRUD operations

## Step 9: Run Django Tests (if available)

```bash
python manage.py test
```

## Common Issues and Solutions

### Issue: "Authentication credentials were not provided"
**Solution**: Make sure you're including the JWT token in the Authorization header:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Issue: "You do not have permission to perform this action"
**Solution**: Check the user's role. Some actions require ADMIN or TEACHER role.

### Issue: "Attendance record already exists"
**Solution**: The unique constraint prevents duplicate attendance per student per day. Use a different date or update the existing record.

### Issue: "Grade already exists"
**Solution**: Each student can only have one grade per exam. Update the existing grade instead of creating a new one.

## Testing Checklist

- [ ] JWT Authentication (login, refresh)
- [ ] User endpoints (list, retrieve, create, update)
- [ ] Student endpoints (with role-based filtering)
- [ ] Teacher endpoints
- [ ] Parent endpoints
- [ ] Subject endpoints
- [ ] Attendance endpoints (create, list, with constraints)
- [ ] Exam endpoints (create, list, retrieve with questions)
- [ ] Question endpoints (create, validate options)
- [ ] Grade endpoints (create, calculate percentage/letter)
- [ ] Report endpoints
- [ ] Role-based access control (test with different roles)
- [ ] Unique constraints (duplicate attendance, duplicate grade)
- [ ] Data validation (invalid question options, invalid scores)

## Next Steps

1. Test with real data
2. Test performance with large datasets
3. Test edge cases
4. Set up automated tests (pytest, Django TestCase)
5. Test API documentation (if using drf-spectacular or similar)

