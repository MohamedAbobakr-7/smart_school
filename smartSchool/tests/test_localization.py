"""
Localization tests for the Smart School Backend.

Covers:
  - APILanguageMiddleware (header, query param, fallback)
  - API root endpoint translation
  - Model choice label translation
  - Centralized messages module translation
  - Translation file completeness (no missing msgstr)
  - Face recognition service translations module
"""

from django.test import TestCase, SimpleTestCase, RequestFactory
from django.utils import translation
from django.conf import settings

from users.models import User
from attendance.models import Attendance, AttendanceSession
from exams.models import Exam
from notifications.models import Notification
from reports.models import WeeklyReport
from videos.models import Video

from smartSchool.messages import (
    MSG_API_ROOT,
    MSG_NOT_FOUND,
    MSG_FORBIDDEN,
    MSG_INSTRUCTOR_ONLY,
    MSG_CLASS_NAME_REQUIRED,
    MSG_MESSAGE_REQUIRED,
    MSG_OPTIONS_MUST_BE_LIST,
    MSG_STUDENT_ID_GENERATED,
    MSG_ATTENDANCE_DUPLICATE,
)
from smartSchool.middleware import APILanguageMiddleware


def _get_choice_label(choices_list, value):
    """Helper: find the label for a given value in a list of (value, label) tuples."""
    for val, label in choices_list:
        if val == value:
            return str(label)
    return None


# ──────────────────────────────────────────────────────────────
#  Middleware & Language Detection Tests (no DB needed)
# ──────────────────────────────────────────────────────────────

class APILanguageMiddlewareTests(SimpleTestCase):
    """Test the custom APILanguageMiddleware language detection logic."""

    def setUp(self):
        self.factory = RequestFactory()

        def stub_response(request):
            return request.LANGUAGE_CODE

        self.middleware = APILanguageMiddleware(stub_response)

    def test_lang_query_param_ar(self):
        """?lang=ar should activate Arabic."""
        request = self.factory.get('/api/', data={'lang': 'ar'})
        result = self.middleware(request)
        self.assertEqual(result, 'ar')

    def test_lang_query_param_en(self):
        """?lang=en should activate English."""
        request = self.factory.get('/api/', data={'lang': 'en'})
        result = self.middleware(request)
        self.assertEqual(result, 'en')

    def test_accept_language_header_ar(self):
        """Accept-Language: ar header should activate Arabic."""
        request = self.factory.get('/api/', HTTP_ACCEPT_LANGUAGE='ar')
        result = self.middleware(request)
        self.assertEqual(result, 'ar')

    def test_accept_language_header_en(self):
        """Accept-Language: en header should activate English."""
        request = self.factory.get('/api/', HTTP_ACCEPT_LANGUAGE='en')
        result = self.middleware(request)
        self.assertEqual(result, 'en')

    def test_accept_language_header_complex(self):
        """Accept-Language: ar-EG,en;q=0.9 should resolve to 'ar' (first 2 chars)."""
        request = self.factory.get('/api/', HTTP_ACCEPT_LANGUAGE='ar-EG,en;q=0.9')
        result = self.middleware(request)
        self.assertEqual(result, 'ar')

    def test_unsupported_language_falls_back_to_default(self):
        """Unsupported language (e.g., 'fr') should fall back to LANGUAGE_CODE ('en')."""
        request = self.factory.get('/api/', HTTP_ACCEPT_LANGUAGE='fr')
        result = self.middleware(request)
        self.assertEqual(result, settings.LANGUAGE_CODE)

    def test_no_language_info_defaults_to_en(self):
        """No header or query param should default to English."""
        request = self.factory.get('/api/')
        result = self.middleware(request)
        self.assertEqual(result, settings.LANGUAGE_CODE)

    def test_query_param_takes_priority_over_header(self):
        """?lang=ar should take priority even if Accept-Language is 'en'."""
        request = self.factory.get('/api/', data={'lang': 'ar'}, HTTP_ACCEPT_LANGUAGE='en')
        result = self.middleware(request)
        self.assertEqual(result, 'ar')


# ──────────────────────────────────────────────────────────────
#  API Root Endpoint Tests (no DB needed)
# ──────────────────────────────────────────────────────────────

class APIRootLocalizationTests(SimpleTestCase):
    """Test that the API root endpoint returns localized messages."""

    def test_default_language_returns_english(self):
        """GET / with no language info should return English message."""
        response = self.client.get('/')
        data = response.json()
        self.assertEqual(data['message'], 'Smart School Backend API')

    def test_arabic_via_header(self):
        """GET / with Accept-Language: ar should return Arabic message."""
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='ar')
        data = response.json()
        self.assertEqual(data['message'], 'واجهة برمجة تطبيقات المدرسة الذكية')

    def test_arabic_via_query_param(self):
        """GET /?lang=ar should return Arabic message."""
        response = self.client.get('/?lang=ar')
        data = response.json()
        self.assertEqual(data['message'], 'واجهة برمجة تطبيقات المدرسة الذكية')

    def test_unsupported_language_falls_back_to_english(self):
        """GET / with Accept-Language: fr should return English message."""
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='fr')
        data = response.json()
        self.assertEqual(data['message'], 'Smart School Backend API')


# ──────────────────────────────────────────────────────────────
#  Centralized Messages Module Tests (no DB needed)
# ──────────────────────────────────────────────────────────────

class MessagesModuleTests(SimpleTestCase):
    """Test that message constants in smartSchool/messages.py translate correctly."""

    def test_msg_api_root_english(self):
        """MSG_API_ROOT should return English when 'en' is active."""
        translation.activate('en')
        self.assertEqual(str(MSG_API_ROOT), 'Smart School Backend API')
        translation.deactivate()

    def test_msg_api_root_arabic(self):
        """MSG_API_ROOT should return Arabic when 'ar' is active."""
        translation.activate('ar')
        self.assertEqual(str(MSG_API_ROOT), 'واجهة برمجة تطبيقات المدرسة الذكية')
        translation.deactivate()

    def test_msg_not_found_english(self):
        translation.activate('en')
        self.assertEqual(str(MSG_NOT_FOUND), 'Resource not found.')
        translation.deactivate()

    def test_msg_not_found_arabic(self):
        translation.activate('ar')
        self.assertEqual(str(MSG_NOT_FOUND), 'المورد غير موجود.')
        translation.deactivate()

    def test_msg_instructor_only_english(self):
        translation.activate('en')
        self.assertEqual(str(MSG_INSTRUCTOR_ONLY), 'Only instructors can process classroom images.')
        translation.deactivate()

    def test_msg_instructor_only_arabic(self):
        translation.activate('ar')
        self.assertEqual(str(MSG_INSTRUCTOR_ONLY), 'يمكن للمعلمين فقط معالجة صور الفصل.')
        translation.deactivate()

    def test_dynamic_format_string_english(self):
        """Dynamic format strings should work in English."""
        translation.activate('en')
        result = str(MSG_STUDENT_ID_GENERATED).format(count=5)
        self.assertEqual(result, 'Successfully generated IDs for 5 student(s).')
        translation.deactivate()

    def test_dynamic_format_string_arabic(self):
        """Dynamic format strings should work in Arabic."""
        translation.activate('ar')
        result = str(MSG_STUDENT_ID_GENERATED).format(count=5)
        self.assertIn('5', result)  # count value should be present
        self.assertNotIn('Successfully generated IDs', result)  # should not be English
        translation.deactivate()

    def test_msg_class_name_required_arabic(self):
        translation.activate('ar')
        self.assertEqual(str(MSG_CLASS_NAME_REQUIRED), 'اسم الفصل مطلوب.')
        translation.deactivate()

    def test_msg_message_required_arabic(self):
        translation.activate('ar')
        self.assertEqual(str(MSG_MESSAGE_REQUIRED), 'الرسالة مطلوبة.')
        translation.deactivate()


# ──────────────────────────────────────────────────────────────
#  Model Choice Label Tests (need DB for model access)
# ──────────────────────────────────────────────────────────────

class ModelChoiceTranslationTests(TestCase):
    """Test that model choice labels translate correctly."""

    # ── User.Role (TextChoices inner class) ──

    def test_user_role_admin_english(self):
        translation.activate('en')
        self.assertEqual(User.Role.ADMIN.label, 'Admin')
        translation.deactivate()

    def test_user_role_admin_arabic(self):
        translation.activate('ar')
        self.assertEqual(User.Role.ADMIN.label, 'مدير')
        translation.deactivate()

    def test_user_role_teacher_arabic(self):
        translation.activate('ar')
        self.assertEqual(User.Role.TEACHER.label, 'معلم')
        translation.deactivate()

    def test_user_role_student_arabic(self):
        translation.activate('ar')
        self.assertEqual(User.Role.STUDENT.label, 'طالب')
        translation.deactivate()

    def test_user_role_parent_arabic(self):
        translation.activate('ar')
        self.assertEqual(User.Role.PARENT.label, 'ولي أمر')
        translation.deactivate()

    # ── Attendance (plain choice tuples) ──

    def test_attendance_status_present_arabic(self):
        translation.activate('ar')
        label = _get_choice_label(Attendance.STATUS_CHOICES, Attendance.PRESENT)
        self.assertEqual(label, 'حاضر')
        translation.deactivate()

    def test_attendance_status_absent_arabic(self):
        translation.activate('ar')
        label = _get_choice_label(Attendance.STATUS_CHOICES, Attendance.ABSENT)
        self.assertEqual(label, 'غائب')
        translation.deactivate()

    def test_attendance_source_manual_arabic(self):
        translation.activate('ar')
        label = _get_choice_label(Attendance.SOURCE_CHOICES, Attendance.MANUAL)
        self.assertEqual(label, 'يدوي')
        translation.deactivate()

    def test_attendance_source_face_recognition_arabic(self):
        translation.activate('ar')
        label = _get_choice_label(Attendance.SOURCE_CHOICES, Attendance.FACE_RECOGNITION)
        self.assertEqual(label, 'التعرف على الوجه')
        translation.deactivate()

    # ── AttendanceSession (plain choice tuples) ──

    def test_session_status_active_arabic(self):
        translation.activate('ar')
        label = _get_choice_label(AttendanceSession.STATUS_CHOICES, AttendanceSession.ACTIVE)
        self.assertEqual(label, 'نشط')
        translation.deactivate()

    def test_session_status_completed_arabic(self):
        translation.activate('ar')
        label = _get_choice_label(AttendanceSession.STATUS_CHOICES, AttendanceSession.COMPLETED)
        self.assertEqual(label, 'مكتمل')
        translation.deactivate()

    def test_session_status_cancelled_arabic(self):
        translation.activate('ar')
        label = _get_choice_label(AttendanceSession.STATUS_CHOICES, AttendanceSession.CANCELLED)
        self.assertEqual(label, 'ملغي')
        translation.deactivate()

    # ── Exam (plain choice tuples) ──

    def test_exam_type_quiz_arabic(self):
        translation.activate('ar')
        label = _get_choice_label(Exam.EXAM_TYPE_CHOICES, Exam.QUIZ)
        self.assertEqual(label, 'اختبار قصير')
        translation.deactivate()

    # ── Notification.Type (TextChoices inner class) ──

    def test_notification_type_low_grade_arabic(self):
        translation.activate('ar')
        self.assertEqual(Notification.Type.LOW_GRADE.label, 'درجة متدنية')
        translation.deactivate()

    # ── WeeklyReport (TextChoices inner classes) ──

    def test_weekly_report_status_pending_arabic(self):
        translation.activate('ar')
        self.assertEqual(WeeklyReport.Status.PENDING.label, 'قيد الانتظار')
        translation.deactivate()

    # ── Video.Category (TextChoices inner class) ──

    def test_video_category_lecture_arabic(self):
        translation.activate('ar')
        self.assertEqual(Video.Category.LECTURE.label, 'محاضرة')
        translation.deactivate()

    # ── Choice values remain unchanged ──

    def test_choice_values_remain_english(self):
        """Choice VALUES (stored in DB) must always be English regardless of active language."""
        translation.activate('ar')
        # User.Role uses uppercase values
        self.assertEqual(User.Role.ADMIN.value, 'ADMIN')
        # Attendance uses lowercase values
        self.assertEqual(Attendance.PRESENT, 'present')
        # Exam uses lowercase values
        self.assertEqual(Exam.QUIZ, 'quiz')
        translation.deactivate()


# ──────────────────────────────────────────────────────────────
#  Translation File Completeness Tests (no DB needed)
# ──────────────────────────────────────────────────────────────

class TranslationCompletenessTests(SimpleTestCase):
    """Verify that the Arabic .po file has no missing (empty) translations."""

    def test_no_untranslated_strings_in_arabic_po(self):
        """
        Parse locale/ar/LC_MESSAGES/django.po and check that no msgstr is empty
        for non-fuzzy, non-obsolete entries.
        """
        import polib
        from pathlib import Path

        po_path = Path(settings.BASE_DIR) / 'locale' / 'ar' / 'LC_MESSAGES' / 'django.po'
        self.assertTrue(po_path.exists(), f'Arabic .po file not found at {po_path}')

        po = polib.pofile(str(po_path))
        untranslated = [
            entry for entry in po
            if not entry.fuzzy
            and not entry.obsolete
            and entry.msgid  # skip the empty header entry
            and not entry.msgstr  # empty translation
        ]

        if untranslated:
            missing_list = '\n  - '.join(e.msgid for e in untranslated)
            self.fail(
                f'{len(untranslated)} untranslated string(s) in Arabic .po file:\n  - {missing_list}'
            )

    def test_mo_file_exists_and_compiled(self):
        """Verify that the compiled .mo file exists for Arabic."""
        from pathlib import Path

        mo_path = Path(settings.BASE_DIR) / 'locale' / 'ar' / 'LC_MESSAGES' / 'django.mo'
        self.assertTrue(mo_path.exists(), f'Arabic .mo file not found at {mo_path}')
        self.assertGreater(mo_path.stat().st_size, 0, 'Arabic .mo file is empty')


# ──────────────────────────────────────────────────────────────
#  Face Recognition Service Translation Tests (no DB needed)
# ──────────────────────────────────────────────────────────────

class FaceRecognitionTranslationTests(SimpleTestCase):
    """Test the dictionary-based translation module for the face recognition service."""

    def test_get_message_english(self):
        from face_recognition_service.translations import get_message
        msg = get_message('student_not_found', 'en', student_id='STU001')
        self.assertEqual(msg, 'Student with ID STU001 not found')

    def test_get_message_arabic(self):
        from face_recognition_service.translations import get_message
        msg = get_message('student_not_found', 'ar', student_id='STU001')
        self.assertEqual(msg, 'الطالب برقم STU001 غير موجود')

    def test_get_message_no_face_detected_english(self):
        from face_recognition_service.translations import get_message
        msg = get_message('no_face_detected', 'en')
        self.assertEqual(msg, 'No face detected in the image. Please upload an image with a clear face.')

    def test_get_message_no_face_detected_arabic(self):
        from face_recognition_service.translations import get_message
        msg = get_message('no_face_detected', 'ar')
        self.assertEqual(msg, 'لم يتم اكتشاف وجه في الصورة. يرجى رفع صورة بوجه واضح.')

    def test_get_message_unsupported_lang_falls_back_to_en(self):
        from face_recognition_service.translations import get_message
        msg = get_message('student_not_found', 'fr', student_id='STU001')
        self.assertEqual(msg, 'Student with ID STU001 not found')

    def test_get_message_unknown_key_falls_back_to_en(self):
        from face_recognition_service.translations import get_message
        msg = get_message('nonexistent_key', 'ar')
        self.assertEqual(msg, 'nonexistent_key')  # falls back to key itself

    def test_resolve_lang_from_header(self):
        from face_recognition_service.translations import resolve_lang

        class FakeRequest:
            headers = {'accept-language': 'ar'}

        result = resolve_lang(FakeRequest())
        self.assertEqual(result, 'ar')

    def test_resolve_lang_default_en(self):
        from face_recognition_service.translations import resolve_lang

        class FakeRequest:
            headers = {}

        result = resolve_lang(FakeRequest())
        self.assertEqual(result, 'en')

    def test_all_translation_keys_have_arabic_entries(self):
        """Every English key should have a corresponding Arabic translation."""
        from face_recognition_service.translations import TRANSLATIONS
        en_keys = set(TRANSLATIONS['en'].keys())
        ar_keys = set(TRANSLATIONS['ar'].keys())
        missing = en_keys - ar_keys
        if missing:
            self.fail(f'Arabic translations missing for keys: {sorted(missing)}')

    def test_batch_detection_message_with_format_params(self):
        from face_recognition_service.translations import get_message
        msg = get_message('faces_detected_matched', 'ar', num_faces=3, num_matches=2)
        self.assertIn('3', msg)
        self.assertIn('2', msg)