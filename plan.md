# Localization Plan: Smart School Backend (EN + AR)

## Project Overview

- **Framework**: Django 5.2 + Django REST Framework
- **Database**: SQL Server (via mssql-django)
- **Current State**: `USE_I18N = True` in settings but zero localization infrastructure exists. All user-facing strings are hardcoded English.
- **Goal**: Full EN/AR localization for all API responses, validation messages, model choices, and translatable database content.
- **Primary Language**: English (en)
- **Secondary Language**: Arabic (ar)

---

## Phase 1: Django i18n Infrastructure Setup

**Goal**: Configure Django's built-in internationalization system and create the translation pipeline.

### 1.1 Update `smartSchool/settings.py`

Add/modify these settings:

```python
from django.utils.translation import gettext_lazy as _

# Replace existing LANGUAGE_CODE line
LANGUAGE_CODE = 'en'

# Add these new settings after LANGUAGE_CODE
LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Add LocaleMiddleware to MIDDLEWARE list — it MUST be placed after
# SessionMiddleware and before CommonMiddleware:
# MIDDLEWARE = [
#     ...
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.locale.LocaleMiddleware',        # <-- add this line
#     'django.middleware.common.CommonMiddleware',
#     ...
# ]
```

### 1.2 Create Locale Directory Structure

Create the following directories from the project root (`E:\smart-school-backend`):

```
locale/
  en/
    LC_MESSAGES/
  ar/
    LC_MESSAGES/
```

### 1.3 Create a Custom Language Middleware

Create file: `smartSchool/middleware.py`

This middleware detects the requested language from the `Accept-Language` header or a `?lang=` query parameter and activates it. This is needed because DRF APIs don't use Django's session/cookie-based language detection.

```python
from django.utils import translation
from django.conf import settings


class APILanguageMiddleware:
    """
    Detects language from:
      1. `Accept-Language` header (e.g., "ar", "en")
      2. `?lang=` query parameter (e.g., ?lang=ar)
    Falls back to settings.LANGUAGE_CODE ('en').
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.GET.get('lang')
        if not lang:
            lang = request.headers.get('Accept-Language', '').split(',')[0].strip()[:2]

        supported = [code for code, _ in settings.LANGUAGES]
        if lang not in supported:
            lang = settings.LANGUAGE_CODE

        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        translation.deactivate()
        return response
```

Then in `smartSchool/settings.py`, replace Django's `LocaleMiddleware` with this custom one:

```python
MIDDLEWARE = [
    ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'smartSchool.middleware.APILanguageMiddleware',   # custom language middleware
    'django.middleware.common.CommonMiddleware',
    ...
]
```

### 1.4 Generate Initial Translation Files

Run from the project root:

```bash
python manage.py makemessages -l ar
python manage.py makemessages -l en
```

This generates `locale/ar/LC_MESSAGES/django.po` and `locale/en/LC_MESSAGES/django.po`.

After adding translations to the `.po` files, compile them:

```bash
python manage.py compilemessages
```

### 1.5 Verification

- Send a request with `Accept-Language: ar` header and confirm `request.LANGUAGE_CODE` is `ar`.
- Send a request with `?lang=ar` query param and confirm the same.
- Default (no header/param) should resolve to `en`.

---

## Phase 2: Localize Model Choice Fields

**Goal**: Wrap all `TextChoices` and choice tuples with `gettext_lazy` so Django can translate enum display values.

### Files to modify:

#### 2.1 `users/models.py` — User.Role choices

```python
from django.utils.translation import gettext_lazy as _

class Role(models.TextChoices):
    ADMIN = 'admin', _('Admin')
    TEACHER = 'teacher', _('Teacher')
    STUDENT = 'student', _('Student')
    PARENT = 'parent', _('Parent')
```

#### 2.2 `exams/models.py` — Exam type choices, Question choices

```python
from django.utils.translation import gettext_lazy as _

# Exam.EXAM_TYPE_CHOICES or TextChoices class — wrap labels:
QUIZ = 'quiz', _('Quiz')
MIDTERM = 'midterm', _('Midterm')
FINAL = 'final', _('Final')
ASSIGNMENT = 'assignment', _('Assignment')
```

#### 2.3 `attendance/models.py` — Status and Source choices

```python
from django.utils.translation import gettext_lazy as _

# Attendance.STATUS_CHOICES
PRESENT = 'present', _('Present')
ABSENT = 'absent', _('Absent')

# Attendance.SOURCE_CHOICES
MANUAL = 'manual', _('Manual')
FACE_RECOGNITION = 'face_recognition', _('Face Recognition')

# AttendanceSession.STATUS_CHOICES
ACTIVE = 'active', _('Active')
COMPLETED = 'completed', _('Completed')
CANCELLED = 'cancelled', _('Cancelled')
```

#### 2.4 `notifications/models.py` — Notification.Type choices

```python
from django.utils.translation import gettext_lazy as _

LOW_GRADE = 'low_grade', _('Low Grade')
ATTENDANCE = 'attendance', _('Attendance')
NEW_STUDENT_REPORT = 'new_student_report', _('New Student Report')
NEW_WEEKLY_REPORT = 'new_weekly_report', _('New Weekly Report')
SYSTEM = 'system', _('System')
```

#### 2.5 `reports/models.py` — WeeklyReport Scope and Status choices

```python
from django.utils.translation import gettext_lazy as _

# Scope choices
SCHOOL = 'school', _('School')
TEACHER = 'teacher', _('Teacher')

# Status choices
PENDING = 'pending', _('Pending')
READY = 'ready', _('Ready')
FAILED = 'failed', _('Failed')
```

#### 2.6 `videos/models.py` — Video.Category choices

Wrap all category choice labels with `_()`.

### Important Notes

- `gettext_lazy` (`_`) returns a lazy string that is translated at render time, so it's safe to use at module/class level.
- These changes do NOT require database migrations because choice labels are not stored in the database — only the choice values are.
- After all changes, run `python manage.py makemessages -l ar` to extract the new strings.

---

## Phase 3: Localize API Response Messages

**Goal**: Replace all hardcoded English strings in views, serializers, and permissions with translatable strings.

### 3.1 Create a Central Messages Module

Create file: `smartSchool/messages.py`

This file centralizes all user-facing API messages in one place for easy translation management.

```python
from django.utils.translation import gettext_lazy as _

# ──── Generic ────
MSG_NOT_FOUND = _('Resource not found.')
MSG_FORBIDDEN = _('You do not have permission to perform this action.')
MSG_BAD_REQUEST = _('Invalid request.')
MSG_SUCCESS = _('Operation completed successfully.')
MSG_CREATED = _('Created successfully.')
MSG_UPDATED = _('Updated successfully.')
MSG_DELETED = _('Deleted successfully.')

# ──── Auth / Users ────
MSG_LOGIN_SUCCESS = _('Login successful.')
MSG_INVALID_CREDENTIALS = _('Invalid credentials.')
MSG_TOKEN_EXPIRED = _('Token has expired.')

# ──── Students ────
MSG_STUDENT_ID_GENERATED = _('Successfully generated IDs for {count} student(s).')
MSG_ALL_STUDENTS_HAVE_IDS = _('All students already have IDs. Nothing to update.')
MSG_NO_IMAGE_PROVIDED = _('No image file provided. Send the image as "photo" field.')
MSG_FACE_REGISTRATION_FAILED = _('Face registration failed.')
MSG_INVALID_DATE_FORMAT = _('Invalid date format. Use YYYY-MM-DD.')

# ──── Attendance ────
MSG_INSTRUCTOR_ONLY = _('Only instructors can process classroom images.')
MSG_ATTENDANCE_DUPLICATE = _('Attendance record already exists for this student on {date}.')
MSG_FACE_VERIFIED = _('Face verified successfully for student {student_id}.')

# ──── Exams ────
MSG_OPTIONS_MUST_BE_LIST = _('Options must be a list/array.')
MSG_MIN_OPTIONS = _('At least 2 options are required for MCQ.')
MSG_CORRECT_ANSWER_INDEX = _('correct_answer index ({index}) must be less than number of options ({count}).')
MSG_GRADE_DUPLICATE = _('Grade already exists for this student and exam.')
MSG_SCORE_EXCEEDS_TOTAL = _('Score cannot exceed total questions.')

# ──── Classes ────
MSG_CLASS_NAME_REQUIRED = _('Class name is required.')
MSG_CLASS_ALREADY_EXISTS = _('A class "{label}" already exists.')

# ──── Chatbot ────
MSG_MESSAGE_REQUIRED = _('Message is required.')
MSG_MESSAGE_TOO_LONG = _('Message too long (max {max} characters).')

# ──── Notifications ────
# (add as needed)

# ──── Reports ────
# (add as needed)

# ──── Videos ────
MSG_NO_FILE = _('No file.')
```

**Note on dynamic strings**: Messages with `{count}`, `{date}`, etc. use Python `.format()` — the translation string contains the placeholder and `.format()` is called at the call site. Example usage:

```python
from smartSchool.messages import MSG_STUDENT_ID_GENERATED

# In the view:
return Response({
    'message': str(MSG_STUDENT_ID_GENERATED).format(count=len(updated_students))
})
```

### 3.2 Update Views to Use Centralized Messages

Replace hardcoded strings in every view file. Work through each app one at a time:

| App | File(s) to Update |
|-----|-------------------|
| students | `students/views.py` |
| attendance | `attendance/views.py` |
| exams | `exams/views.py` |
| classes | `classes/views.py` |
| reports | `reports/views.py` |
| videos | `videos/views.py` |
| notifications | `notifications/views.py` |
| chatbot | `chatbot/views.py` |
| users | `users/views.py` |
| smartSchool | `smartSchool/views.py` |

For each file:
1. Add `from smartSchool.messages import ...` at the top.
2. Replace every hardcoded English string in `Response(...)` calls with the corresponding message constant.
3. For messages with dynamic values, call `.format(...)` on the string.

### 3.3 Update Serializers to Use Centralized Messages

Update validation error messages in serializers:

| App | File(s) to Update |
|-----|-------------------|
| classes | `classes/serializers.py` |
| exams | `exams/serializers.py` |
| attendance | `attendance/serializers.py` |
| reports | `reports/serializers.py` |

For each file:
1. Import the relevant message constants.
2. Replace `raise serializers.ValidationError('...')` with the corresponding constant.

### 3.4 Update Model `clean()` Methods

Update `ValidationError` messages in model `clean()` methods:

| App | File(s) to Update |
|-----|-------------------|
| exams | `exams/models.py` — `Question.clean()` |
| attendance | `attendance/models.py` — `Attendance.clean()` |

### 3.5 Update Permission Classes

File: `users/permissions.py`

If permission classes return custom `message` attributes, wrap them with `_()`.

### 3.6 Verification

- After all replacements, run `python manage.py makemessages -l ar` to collect all new translatable strings.
- Verify that the `.po` file contains all expected messages.
- Test that `Response({'message': MSG_SOMETHING})` returns English by default and Arabic when `Accept-Language: ar` is sent.

---

## Phase 4: Write Arabic Translations

**Goal**: Populate the Arabic `.po` file with all translations.

### 4.1 Edit `locale/ar/LC_MESSAGES/django.po`

For every `msgid` in the file, add the corresponding `msgstr` Arabic translation. Examples:

```po
msgid "Resource not found."
msgstr "المورد غير موجود."

msgid "Admin"
msgstr "مدير"

msgid "Teacher"
msgstr "معلم"

msgid "Student"
msgstr "طالب"

msgid "Parent"
msgstr "ولي أمر"

msgid "Class name is required."
msgstr "اسم الفصل مطلوب."

msgid "Invalid date format. Use YYYY-MM-DD."
msgstr "صيغة التاريخ غير صحيحة. استخدم YYYY-MM-DD."

msgid "Only instructors can process classroom images."
msgstr "يمكن للمعلمين فقط معالجة صور الفصل."
```

**Provide the full list of Arabic translations for every message** in `smartSchool/messages.py` and every choice label wrapped in Phase 2.

### 4.2 Compile Messages

```bash
python manage.py compilemessages
```

This generates the binary `.mo` files that Django reads at runtime.

### 4.3 Verification

- Request any endpoint with `Accept-Language: ar` and confirm Arabic responses.
- Request with `Accept-Language: en` or no header and confirm English responses.
- Test validation errors (e.g., submit an invalid exam) with `Accept-Language: ar`.

---

## Phase 5: Localize Database Content (Translatable Fields)

**Goal**: Support bilingual content for models where admins enter translatable text (subject names, class names, exam names, question text, notifications).

### 5.1 Install `django-modeltranslation`

```bash
pip install django-modeltranslation
```

Add to `INSTALLED_APPS` in `smartSchool/settings.py` — it **must** come before `django.contrib.admin`:

```python
INSTALLED_APPS = [
    'modeltranslation',          # <-- add BEFORE admin
    'django.contrib.admin',
    ...
]
```

### 5.2 Create `translation.py` Files

For each app with translatable model fields, create a `translation.py` file:

#### `subjects/translation.py`

```python
from modeltranslation.translator import register, TranslationOptions
from .models import Subject, Material

@register(Subject)
class SubjectTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

@register(Material)
class MaterialTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
```

#### `classes/translation.py`

```python
from modeltranslation.translator import register, TranslationOptions
from .models import SchoolClass

@register(SchoolClass)
class SchoolClassTranslationOptions(TranslationOptions):
    fields = ('name', 'description')
```

#### `exams/translation.py`

```python
from modeltranslation.translator import register, TranslationOptions
from .models import Exam, Question

@register(Exam)
class ExamTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(Question)
class QuestionTranslationOptions(TranslationOptions):
    fields = ('text',)
    # Note: 'options' is a JSONField — handle separately in serializer
```

#### `notifications/translation.py`

```python
from modeltranslation.translator import register, TranslationOptions
from .models import Notification

@register(Notification)
class NotificationTranslationOptions(TranslationOptions):
    fields = ('title', 'body')
```

### 5.3 Generate and Run Migrations

After creating all `translation.py` files:

```bash
python manage.py makemigrations
python manage.py migrate
```

This adds `name_en`, `name_ar`, `description_en`, `description_ar`, etc. columns to the relevant tables. `django-modeltranslation` automatically returns the correct language field based on the active language.

### 5.4 Backfill Existing Data

Create a data migration or management command to copy existing field values into the `_en` columns:

```bash
python manage.py update_translation_fields
```

This copies the current value of `name` into `name_en` for all registered models.

### 5.5 Update Serializers (Optional Enhancement)

If you want API consumers to be able to submit/read both languages explicitly:

```python
# Example: subjects/serializers.py
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'name_en', 'name_ar', 'description', 'description_en', 'description_ar', ...]
```

- `name` returns the value for the active language (auto-resolved by `django-modeltranslation`).
- `name_en` / `name_ar` allow explicit access to both translations.

### 5.6 Handle Question Options (JSONField)

Since `Question.options` is a JSONField containing a list of strings, `django-modeltranslation` won't handle it natively. Options:

**Option A — Duplicate JSONField**:
Register `options` in TranslationOptions. This creates `options_en` and `options_ar` as separate JSONFields. Admins fill both.

**Option B — Structured JSON**:
Change the options format from `["Option A", "Option B"]` to `[{"en": "Option A", "ar": "الخيار أ"}, ...]` and resolve in the serializer based on active language.

**Recommended**: Option A (simpler, consistent with `django-modeltranslation` patterns).

### 5.7 Verification

- Create a Subject with `name_en="Mathematics"` and `name_ar="رياضيات"`.
- GET `/api/subjects/` with `Accept-Language: en` returns `"name": "Mathematics"`.
- GET `/api/subjects/` with `Accept-Language: ar` returns `"name": "رياضيات"`.

---

## Phase 6: Localize the Face Recognition Microservice

**Goal**: The face recognition service (`face_recognition_service/main.py`) is a separate FastAPI app. Its responses also need localization.

### 6.1 Approach

Since this is a standalone FastAPI service (not Django), use a lightweight approach:

1. Create a `translations.py` file in `face_recognition_service/`.
2. Define a simple dictionary-based translation map.
3. Read the `Accept-Language` header in each endpoint and resolve messages.

```python
# face_recognition_service/translations.py

TRANSLATIONS = {
    'en': {
        'face_verified': 'Face verified successfully for student {student_id}.',
        'no_face_detected': 'No face detected in the image. Please upload an image with a clear face.',
        'face_registered': 'Face registered successfully.',
        # ... all messages
    },
    'ar': {
        'face_verified': 'تم التحقق من الوجه بنجاح للطالب {student_id}.',
        'no_face_detected': 'لم يتم اكتشاف وجه في الصورة. يرجى رفع صورة بوجه واضح.',
        'face_registered': 'تم تسجيل الوجه بنجاح.',
        # ... all messages
    }
}

def get_message(key: str, lang: str = 'en', **kwargs) -> str:
    lang = lang if lang in TRANSLATIONS else 'en'
    msg = TRANSLATIONS[lang].get(key, TRANSLATIONS['en'].get(key, key))
    return msg.format(**kwargs) if kwargs else msg
```

### 6.2 Update FastAPI Endpoints

In each endpoint in `face_recognition_service/main.py`:

```python
from translations import get_message

@app.post("/verify")
async def verify_face(request: Request, ...):
    lang = request.headers.get("accept-language", "en")[:2]
    ...
    return {"message": get_message("face_verified", lang, student_id=student_id)}
```

### 6.3 Verification

- Call the face recognition service with `Accept-Language: ar` and confirm Arabic messages.

---

## Phase 7: Testing & Quality Assurance

**Goal**: Verify the entire localization system works correctly end-to-end.

### 7.1 Create Translation Tests

Create file: `smartSchool/tests/test_localization.py`

```python
from django.test import TestCase, RequestFactory
from django.utils import translation

class LocalizationTests(TestCase):

    def test_default_language_is_english(self):
        response = self.client.get('/api/')
        self.assertEqual(response.json()['message'], 'Smart School Backend API')

    def test_arabic_language_via_header(self):
        response = self.client.get('/api/', HTTP_ACCEPT_LANGUAGE='ar')
        # Assert Arabic response

    def test_arabic_language_via_query_param(self):
        response = self.client.get('/api/?lang=ar')
        # Assert Arabic response

    def test_unsupported_language_falls_back_to_english(self):
        response = self.client.get('/api/', HTTP_ACCEPT_LANGUAGE='fr')
        self.assertEqual(response.json()['message'], 'Smart School Backend API')

    def test_validation_error_in_arabic(self):
        # POST invalid data with Accept-Language: ar
        # Assert validation error messages are in Arabic
        pass

    def test_model_choices_translated(self):
        translation.activate('ar')
        # Assert User.Role.ADMIN.label is Arabic
        translation.deactivate()
```

### 7.2 Verify No Missing Translations

After `makemessages`, check the `.po` file for any `msgstr ""` (empty translations):

```bash
python -c "
import polib
po = polib.pofile('locale/ar/LC_MESSAGES/django.po')
untranslated = po.untranslated_entries()
print(f'{len(untranslated)} untranslated strings')
for entry in untranslated:
    print(f'  - {entry.msgid}')
"
```

### 7.3 Test Checklist

| Test Case | Method | Expected |
|-----------|--------|----------|
| Default language | GET `/api/` (no header) | English response |
| Arabic via header | GET `/api/` + `Accept-Language: ar` | Arabic response |
| Arabic via query param | GET `/api/?lang=ar` | Arabic response |
| Unknown language fallback | GET `/api/` + `Accept-Language: fr` | English response |
| Validation error (EN) | POST invalid data | English error |
| Validation error (AR) | POST invalid data + `Accept-Language: ar` | Arabic error |
| Model choices (EN) | GET exam types | English labels |
| Model choices (AR) | GET exam types + `Accept-Language: ar` | Arabic labels |
| DB content (EN) | GET subject | `name` = English |
| DB content (AR) | GET subject + `Accept-Language: ar` | `name` = Arabic |
| Face recognition (AR) | POST to face service + `Accept-Language: ar` | Arabic message |

---

## Phase 8: Documentation & Developer Guide

**Goal**: Document the localization system so future developers can maintain and extend it.

### 8.1 Add to Project README or Create `docs/localization.md`

Document:

1. **How language detection works**: `Accept-Language` header or `?lang=` query parameter.
2. **How to add a new translatable string**:
   - Add message constant to `smartSchool/messages.py` wrapped in `_()`.
   - Use the constant in views/serializers.
   - Run `python manage.py makemessages -l ar`.
   - Add Arabic translation in `locale/ar/LC_MESSAGES/django.po`.
   - Run `python manage.py compilemessages`.
3. **How to add a new language**:
   - Add language tuple to `LANGUAGES` in settings.
   - Run `python manage.py makemessages -l <code>`.
   - Translate all strings in the new `.po` file.
   - Compile messages.
4. **How to add translatable fields to a new model**:
   - Create or update `translation.py` in the app.
   - Register the model with `@register` and list translatable fields.
   - Run `makemigrations` and `migrate`.
5. **Face recognition service**: Uses dictionary-based translations in `translations.py`.

---

## Summary: Execution Order

| Phase | Description | Dependencies | Files Created/Modified |
|-------|-------------|--------------|----------------------|
| 1 | i18n infrastructure setup | None | `settings.py`, `smartSchool/middleware.py`, `locale/` dirs |
| 2 | Model choice localization | Phase 1 | `*/models.py` (6 apps) |
| 3 | API message localization | Phase 1 | `smartSchool/messages.py`, `*/views.py`, `*/serializers.py` |
| 4 | Arabic translations | Phases 2 + 3 | `locale/ar/LC_MESSAGES/django.po` |
| 5 | Database content translation | Phase 1 | `*/translation.py` (4 apps), new migrations |
| 6 | Face recognition service | None (independent) | `face_recognition_service/translations.py`, `main.py` |
| 7 | Testing | Phases 1-6 | `smartSchool/tests/test_localization.py` |
| 8 | Documentation | Phases 1-7 | `docs/localization.md` |

**Phases 2, 3, and 6 can run in parallel** since they modify different files and have no cross-dependencies (all only depend on Phase 1).

---

## Critical Rules for the Implementor

1. **Always use `gettext_lazy` (imported as `_`) at module level** (models, serializers, message constants). Use `gettext` (non-lazy) only inside functions/views if the string must be evaluated immediately.
2. **Never change model field `choices` values** (e.g., `'admin'`, `'quiz'`). Only wrap the **labels** (display text) with `_()`. The stored database values remain English.
3. **Run `makemessages` after every phase** that adds new translatable strings to collect them into the `.po` file.
4. **Run `compilemessages` after editing any `.po` file** to generate the binary `.mo` files.
5. **Do not modify database migration files** from previous phases. Each phase creates its own new migrations if needed.
6. **Keep `smartSchool/messages.py` as the single source of truth** for all API response messages. Views/serializers should import from it, not define their own strings.
7. **Format strings**: Use `str(MSG_CONSTANT).format(key=value)` for messages with dynamic placeholders. The `.format()` call must happen at the call site, not in `messages.py`.
8. **Test with both languages** after each phase to catch issues early.
