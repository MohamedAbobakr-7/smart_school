# Localization (i18n) Guide

This document describes the bilingual (English / Arabic) localization system implemented in the Smart School Backend. It covers how language detection works, how to add new translatable strings, how to add a new language, how to add translatable model fields, and how the standalone Face Recognition microservice handles translations.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Language Detection](#language-detection)
3. [Adding a New Translatable String](#adding-a-new-translatable-string)
4. [Adding a New Language](#adding-a-new-language)
5. [Adding Translatable Fields to a Model](#adding-translatable-fields-to-a-model)
6. [Face Recognition Service Translations](#face-recognition-service-translations)
7. [Testing](#testing)
8. [Key Files Reference](#key-files-reference)
9. [Common Pitfalls](#common-pitfalls)

---

## Architecture Overview

The localization system uses two complementary approaches:

| Layer | Mechanism | Scope |
|-------|-----------|-------|
| **Django main app** | GNU gettext (`django.utils.translation`) | API response messages, model choice labels, serializer/validation errors |
| **Database content** | `django-modeltranslation` | Translatable model fields (e.g., subject names, notification titles) |
| **Face Recognition service** | Dictionary-based (`TRANSLATIONS` dict) | Standalone FastAPI microservice messages |

### Django i18n Settings

Defined in [`smartSchool/settings.py`](smartSchool/settings.py:170):

```python
LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

USE_I18N = True
```

The `modeltranslation` package is listed in `INSTALLED_APPS` **before** `django.contrib.admin` to ensure translated fields appear correctly in the admin interface.

---

## Language Detection

Language detection is handled by [`APILanguageMiddleware`](smartSchool/middleware.py:5), registered in [`MIDDLEWARE`](smartSchool/settings.py:77) **after** `SessionMiddleware` and **before** `CommonMiddleware`.

### Detection Order

The middleware checks two sources in priority order:

1. **Query parameter** — `?lang=ar` or `?lang=en`
2. **HTTP header** — `Accept-Language: ar` (first language in the header, truncated to 2 characters)

If neither source provides a supported language code, the middleware falls back to `settings.LANGUAGE_CODE` (`'en'`).

### How It Works

```python
class APILanguageMiddleware:
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

### Client Usage Examples

**Using query parameter (highest priority):**

```bash
curl "http://localhost:8000/api/students/?lang=ar"
```

**Using Accept-Language header:**

```bash
curl -H "Accept-Language: ar" "http://localhost:8000/api/students/"
```

**Complex Accept-Language header** (first language wins):

```bash
curl -H "Accept-Language: ar;q=0.9, en;q=0.8" "http://localhost:8000/api/students/"
# → Arabic is selected (first in the list)
```

**Unsupported language** (falls back to English):

```bash
curl -H "Accept-Language: fr" "http://localhost:8000/api/students/"
# → Falls back to 'en'
```

---

## Adding a New Translatable String

All API response messages are centralized in [`smartSchool/messages.py`](smartSchool/messages.py) as the **single source of truth**. Views and serializers must import constants from this module — never define raw strings inline.

### Step-by-Step

#### 1. Add the message constant to `messages.py`

Open [`smartSchool/messages.py`](smartSchool/messages.py) and add your new constant, wrapped in `_()` (which is `gettext_lazy`):

```python
from django.utils.translation import gettext_lazy as _

# Add your new message:
MSG_YOUR_NEW_MESSAGE = _('Your new message text with {placeholder}.')
```

> **Important:** Always use `gettext_lazy` (`_`) for module-level constants. Use `gettext` (non-lazy) only inside function bodies when the string must be evaluated immediately.

#### 2. Use the constant in your view or serializer

```python
from smartSchool.messages import MSG_YOUR_NEW_MESSAGE

# In a view:
return Response({'detail': str(MSG_YOUR_NEW_MESSAGE).format(placeholder='value')},
                status=status.HTTP_400_BAD_REQUEST)

# In a serializer validate() method:
raise serializers.ValidationError(str(MSG_YOUR_NEW_MESSAGE).format(placeholder='value'))
```

> **Note:** When using lazy strings with `.format()`, you must wrap them with `str()` first to force evaluation. This is because `_()` returns a `Promise` object at module level, not a plain string.

#### 3. Collect the new string into the `.po` file

```bash
python manage.py makemessages -l ar
```

This scans all Python files for `_()` calls and adds new entries to [`locale/ar/LC_MESSAGES/django.po`](locale/ar/LC_MESSAGES/django.po).

#### 4. Add the Arabic translation

Open [`locale/ar/LC_MESSAGES/django.po`](locale/ar/LC_MESSAGES/django.po) and find the new entry (it will have an empty `msgstr`). Fill in the Arabic translation:

```po
msgid "Your new message text with {placeholder}."
msgstr "نص رسالتك الجديدة مع {placeholder}."
```

#### 5. Compile the messages

```bash
python manage.py compilemessages
```

This generates the binary `.mo` file that Django actually reads at runtime.

#### 6. Verify

Run the localization tests to confirm everything works:

```bash
python manage.py test smartSchool.tests.test_localization
```

---

## Adding a New Language

To add a third language (e.g., French — `fr`) to the system:

### Step 1: Add the language tuple to settings

In [`smartSchool/settings.py`](smartSchool/settings.py:175), add the new language to the `LANGUAGES` list:

```python
LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
    ('fr', _('French')),   # ← new
]
```

### Step 2: Create the locale directory

```bash
mkdir locale\fr\LC_MESSAGES
```

Place a `.gitkeep` file inside to ensure Git tracks the empty directory:

```bash
echo. > locale\fr\LC_MESSAGES\.gitkeep
```

### Step 3: Generate the `.po` file

```bash
python manage.py makemessages -l fr
```

This creates `locale/fr/LC_MESSAGES/django.po` with all translatable strings extracted from the codebase. Each entry will have an empty `msgstr` awaiting translation.

### Step 4: Translate all strings

Open `locale/fr/LC_MESSAGES/django.po` and fill in every `msgstr` with the French translation.

### Step 5: Compile messages

```bash
python manage.py compilemessages
```

This generates `locale/fr/LC_MESSAGES/django.mo`.

### Step 6: Update the Face Recognition service (if needed)

If the new language also needs to be supported by the Face Recognition microservice, add a new dictionary entry in [`face_recognition_service/translations.py`](face_recognition_service/translations.py:14):

```python
TRANSLATIONS = {
    'en': { ... },
    'ar': { ... },
    'fr': {   # ← new
        'student_not_found': 'Étudiant avec ID {student_id} non trouvé',
        # ... translate all 15 keys
    },
}
```

### Step 7: Update tests

Add the new language to the test assertions in [`smartSchool/tests/test_localization.py`](smartSchool/tests/test_localization.py).

---

## Adding Translatable Fields to a Model

Database content translation (e.g., subject names, notification titles) is handled by `django-modeltranslation`. This package automatically creates `_en` and `_ar` field suffixes for each registered field, allowing bilingual content to be stored in the database.

### Step-by-Step

#### 1. Create or update `translation.py` in your app

Each app that needs translatable model fields must have a `translation.py` file at the app root. This file registers models with `django-modeltranslation`.

**Example — adding translatable fields to a new model:**

```python
# myapp/translation.py
from modeltranslation.translator import register, TranslationOptions
from .models import MyModel


@register(MyModel)
class MyModelTranslationOptions(TranslationOptions):
    fields = ('title', 'description')  # fields that need _en / _ar variants
```

#### 2. Existing registration examples

The project currently has four apps with `translation.py` files:

| App | File | Models & Fields |
|-----|------|-----------------|
| `subjects` | [`subjects/translation.py`](subjects/translation.py) | `Subject`: name, description · `Material`: title, description |
| `classes` | [`classes/translation.py`](classes/translation.py) | `SchoolClass`: name, description |
| `exams` | [`exams/translation.py`](exams/translation.py) | `Exam`: name · `Question`: text, options |
| `notifications` | [`notifications/translation.py`](notifications/translation.py) | `Notification`: title, body |

#### 3. Generate and run migrations

After creating or updating `translation.py`, generate the schema migration:

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates new columns like `title_en`, `title_ar`, `description_en`, `description_ar` on the registered models.

#### 4. Backfill existing data

If the model already had data, the new `_ar` fields will be empty. Run a data migration or use the Django shell to backfill:

```python
# Example: copy English content as default for Arabic fields
from subjects.models import Subject
for obj in Subject.objects.all():
    if not obj.name_ar:
        obj.name_ar = obj.name_en or obj.name
        obj.save()
```

#### 5. Update serializers (optional enhancement)

To expose both language variants in the API, update the serializer:

```python
class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ('id', 'title_en', 'title_ar', 'description_en', 'description_ar')
```

Or use a dynamic approach that returns the field matching the current request language:

```python
from django.utils.translation import get_language

class MyModelSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        lang = get_language()
        return getattr(obj, f'title_{lang}', obj.title_en)
```

---

## Face Recognition Service Translations

The Face Recognition microservice is a standalone FastAPI application (not Django), so it uses a **dictionary-based** translation approach instead of gettext.

### File: [`face_recognition_service/translations.py`](face_recognition_service/translations.py)

This module contains:

- **`TRANSLATIONS`** — A dictionary with `'en'` and `'ar'` keys, each mapping 15 message keys to localized template strings.
- **`get_message(key, lang='en', **kwargs)`** — Retrieves a localized message by key and language. Supports Python `str.format()` placeholders. Falls back to English if the language is unsupported, or to the key itself if the key is missing.
- **`resolve_lang(request)`** — Extracts the language code from a FastAPI `Request` object's `Accept-Language` header.

### Usage in Endpoints

Each endpoint in [`face_recognition_service/main.py`](face_recognition_service/main.py) accepts a `request: Request` parameter and follows this pattern:

```python
from fastapi import Request
from translations import get_message, resolve_lang

@app.post("/verify-face")
async def verify_face(request: Request, ...):
    lang = resolve_lang(request)
    # ...
    return {"detail": get_message("face_verified", lang, student_id=student_id)}
```

### Available Message Keys

| Key | English Template | Has Placeholders |
|-----|-----------------|-----------------|
| `student_not_found` | `Student with ID {student_id} not found` | ✅ `student_id` |
| `no_face_detected` | `No face detected in the image...` | ❌ |
| `no_face_registered` | `No face registered for student {student_id}...` | ✅ `student_id` |
| `no_face_registered_short` | `No face registered` | ❌ |
| `face_registered_short` | `Face registered` | ❌ |
| `face_verified` | `Face verified successfully for student {student_id}` | ✅ `student_id` |
| `face_not_matched` | `Face does not match registered face for student {student_id}` | ✅ `student_id` |
| `face_registered` | `Face registered successfully for student {student_id}` | ✅ `student_id` |
| `face_encoding_updated` | `Face encoding updated successfully for student {student_id}` | ✅ `student_id` |
| `face_encoding_deleted` | `Face encoding deleted successfully for student {student_id}` | ✅ `student_id` |
| `no_face_encoding_found` | `No face encoding found for student {student_id}` | ✅ `student_id` |
| `no_faces_detected_batch` | `No faces detected in the image` | ❌ |
| `faces_detected_matched` | `Detected {num_faces} face(s), matched {num_matches} student(s)` | ✅ `num_faces`, `num_matches` |
| `no_faces_detected_try` | `No faces detected. Try: better lighting...` | ❌ |
| `db_connection_error` | `Database connection error: {error}` | ✅ `error` |
| `encoding_file_not_exist` | `Encoding file does not exist` | ❌ |
| `encoding_load_failed` | `Failed to load encoding file` | ❌ |
| `no_encoding_in_file` | `No encoding found in file` | ❌ |
| `encoding_not_numpy` | `Encoding is not a numpy array` | ❌ |
| `invalid_encoding_shape` | `Invalid encoding shape: {shape}, expected (128,)` | ✅ `shape` |
| `validation_error` | `Validation error: {error}` | ✅ `error` |

### Adding a New Message to the Face Recognition Service

1. Add the English template string to the `'en'` dict in `TRANSLATIONS`
2. Add the Arabic translation to the `'ar'` dict in `TRANSLATIONS`
3. Use `get_message('your_new_key', lang, **kwargs)` in the endpoint

No `.po` file or compilation step is needed — changes take effect immediately on service restart.

---

## Testing

The localization test suite is in [`smartSchool/tests/test_localization.py`](smartSchool/tests/test_localization.py) with **51 tests** across 6 test classes:

| Test Class | Count | What It Tests |
|------------|-------|---------------|
| `APILanguageMiddlewareTests` | 8 | Query param detection, header detection, fallback behavior, priority order |
| `APIRootLocalizationTests` | 4 | API root response in EN, AR (via header and query param), unsupported fallback |
| `MessagesModuleTests` | 10 | All message constants return correct EN/AR strings, dynamic format strings |
| `ModelChoiceTranslationTests` | 16 | Choice labels for `User.Role`, `Attendance`, `AttendanceSession`, `Exam`, `Notification.Type`, `WeeklyReport.Status`, `Video.Category` |
| `TranslationCompletenessTests` | 2 | No untranslated strings in `.po` file, `.mo` file exists |
| `FaceRecognitionTranslationTests` | 11 | `get_message()` EN/AR, fallback, `resolve_lang()`, all keys have Arabic entries |

### Running the Tests

```bash
python manage.py test smartSchool.tests.test_localization
```

### Important: Choice Field Access Patterns

The project uses two patterns for model choices, and tests must access them differently:

**TextChoices inner classes** (have `.label` attribute):

```python
# User.Role, Notification.Type, WeeklyReport.Status, Video.Category
label = User.Role.ADMIN.label  # → 'Admin' (localized)
value = User.Role.ADMIN.value  # → 'ADMIN' (stored value, NOT localized)
```

**Plain choice tuples** (need helper function):

```python
# Attendance.STATUS_CHOICES, Attendance.SOURCE_CHOICES,
# AttendanceSession.STATUS_CHOICES, Exam.EXAM_TYPE_CHOICES
def _get_choice_label(choices_list, value):
    for val, label in choices_list:
        if val == value:
            return str(label)
    return value

label = _get_choice_label(Attendance.STATUS_CHOICES, 'present')  # → 'Present' (localized)
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| [`smartSchool/settings.py`](smartSchool/settings.py:170) | `LANGUAGES`, `LOCALE_PATHS`, `USE_I18N`, `LANGUAGE_CODE` settings |
| [`smartSchool/middleware.py`](smartSchool/middleware.py:5) | `APILanguageMiddleware` — language detection per request |
| [`smartSchool/messages.py`](smartSchool/messages.py) | Centralized API response message constants (single source of truth) |
| [`locale/ar/LC_MESSAGES/django.po`](locale/ar/LC_MESSAGES/django.po) | Arabic gettext translations |
| [`locale/en/LC_MESSAGES/django.po`](locale/en/LC_MESSAGES/django.po) | English gettext translations (reference) |
| [`subjects/translation.py`](subjects/translation.py) | `Subject` + `Material` field translations |
| [`classes/translation.py`](classes/translation.py) | `SchoolClass` field translations |
| [`exams/translation.py`](exams/translation.py) | `Exam` + `Question` field translations |
| [`notifications/translation.py`](notifications/translation.py) | `Notification` field translations |
| [`face_recognition_service/translations.py`](face_recognition_service/translations.py) | Dictionary-based translations for FastAPI microservice |
| [`face_recognition_service/main.py`](face_recognition_service/main.py) | FastAPI endpoints using `get_message()` + `resolve_lang()` |
| [`smartSchool/tests/test_localization.py`](smartSchool/tests/test_localization.py) | 51 localization tests |

---

## Common Pitfalls

### 1. Using `gettext` instead of `gettext_lazy` at module level

**Wrong:**
```python
from django.utils.translation import gettext as _
MSG_FOO = _('Foo')  # evaluated at import time — always returns default language
```

**Correct:**
```python
from django.utils.translation import gettext_lazy as _
MSG_FOO = _('Foo')  # lazy — evaluated per-request with active language
```

### 2. Forgetting `str()` when formatting lazy strings

**Wrong:**
```python
MSG_FOO.format(count=5)  # TypeError: Promise object has no .format()
```

**Correct:**
```python
str(MSG_FOO).format(count=5)  # forces evaluation first, then formats
```

### 3. Changing choice **values** instead of choice **labels**

Choice **values** are stored in the database and must remain English. Only wrap the **labels** (display text) with `_()`:

**Wrong:**
```python
ADMIN = _('admin')  # changes stored value — breaks existing data!
```

**Correct:**
```python
ADMIN = 'ADMIN', _('Admin')  # value stays 'ADMIN', label is translatable
```

### 4. Forgetting to run `compilemessages` after editing `.po`

Django reads `.mo` (binary) files at runtime, not `.po` (text) files. After any `.po` edit:

```bash
python manage.py compilemessages
```

### 5. Forgetting `modeltranslation` before `django.contrib.admin` in `INSTALLED_APPS`

`modeltranslation` must appear before `django.contrib.admin` to properly register translated fields in the admin interface. See [`smartSchool/settings.py`](smartSchool/settings.py:40).

### 6. Not propagating `lang` through helper functions in the Face Recognition service

When calling helper functions from endpoints, the `lang` parameter must be passed through the entire call chain:

```python
# Endpoint → helper → helper
async def verify_face(request: Request, ...):
    lang = resolve_lang(request)
    if not verify_student_exists(student_id, lang=lang):
        return {"detail": get_message("student_not_found", lang, student_id=student_id)}
```

For `asyncio.to_thread` and `run_in_executor` calls, pass `lang` explicitly:

```python
result = await asyncio.to_thread(process_image_batch, image_bytes, model, num_jitters, lang=lang)