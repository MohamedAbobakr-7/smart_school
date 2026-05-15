# Quick Testing Guide

## 1. Start the Server

```bash
python manage.py runserver
```

## 2. Create Test Data

```bash
python manage.py create_test_data
```

## 3. Test Authentication

### Login (Get JWT Token)

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"admin\", \"password\": \"admin123\"}"
```

Save the `access` token from the response.

## 4. Test Endpoints

Replace `YOUR_TOKEN` with the access token from step 3.

### Get Current User

```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List All Users (Admin)

```bash
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Students

```bash
curl -X GET http://localhost:8000/api/students/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Exams

```bash
curl -X GET http://localhost:8000/api/exams/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Questions

```bash
curl -X GET http://localhost:8000/api/questions/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Grades

```bash
curl -X GET http://localhost:8000/api/grades/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Attendance

```bash
curl -X GET http://localhost:8000/api/attendance/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 5. Test with Different Roles

### As Teacher

1. Login as `teacher1` / `teacher123`
2. Try creating an exam, question, grade, attendance
3. Should have access to all resources

### As Student

1. Login as `student1` / `student123`
2. Should only see own data
3. Cannot create/update/delete resources

### As Parent

1. Login as `parent1` / `parent123`
2. Should see children's data
3. Cannot create/update/delete resources

## 6. Automated Testing

Run the Python test script:

```bash
python test_api.py
```

Make sure the server is running first!

## Test Users

- **Admin**: `admin` / `admin123` (full access)
- **Teacher**: `teacher1` / `teacher123` (can create exams, questions, grades)
- **Student**: `student1` / `student123` (read-only, own data)
- **Parent**: `parent1` / `parent123` (read-only, children's data)

## Common Test Scenarios

### Create an Exam (Teacher/Admin)

```bash
curl -X POST http://localhost:8000/api/exams/ \
  -H "Authorization: Bearer TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test Exam\", \"subject\": 1, \"teacher\": 1, \"duration\": 60}"
```

### Create a Question (Teacher/Admin)

```bash
curl -X POST http://localhost:8000/api/questions/ \
  -H "Authorization: Bearer TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"exam\": 1, \"text\": \"What is 2+2?\", \"options\": [\"2\", \"3\", \"4\", \"5\"], \"correct_answer\": 2}"
```

### Create Attendance (Teacher/Admin)

```bash
curl -X POST http://localhost:8000/api/attendance/ \
  -H "Authorization: Bearer TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"student\": 1, \"date\": \"2024-01-20\", \"status\": \"present\", \"source\": \"manual\", \"marked_by\": 1}"
```

### Test Duplicate Attendance (Should Fail)

Try creating attendance for the same student on the same date twice - should return an error.

## Using Postman/Insomnia

1. Create a new request
2. Set method (GET, POST, etc.)
3. Set URL: `http://localhost:8000/api/endpoint/`
4. Add header: `Authorization: Bearer YOUR_TOKEN`
5. For POST/PUT: Add JSON body in the request body tab

## Django Shell Testing

```bash
python manage.py shell
```

```python
from users.models import User
from students.models import Student
from exams.models import Exam, Question, Grade

# Test user roles
user = User.objects.get(username='admin')
print(user.is_admin())  # True

# Test relationships
student = Student.objects.first()
print(student.parent)  # Parent object

# Test exam system
exam = Exam.objects.first()
print(exam.questions.count())  # Number of questions

grade = Grade.objects.first()
print(grade.get_percentage())  # Percentage
print(grade.get_grade_letter())  # Letter grade
```

For more detailed testing instructions, see `TESTING_GUIDE.md`.

