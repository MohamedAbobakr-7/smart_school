"""
Lightweight dictionary-based translation module for the Face Recognition FastAPI service.

Since this is a standalone FastAPI app (not Django), we use a simple dict approach
instead of Django's gettext framework.

Usage:
    from translations import get_message

    lang = request.headers.get("accept-language", "en")[:2]
    msg = get_message("student_not_found", lang, student_id="STU001")
"""

TRANSLATIONS = {
    'en': {
        # ──── Student lookup ────
        'student_not_found': 'Student with ID {student_id} not found',

        # ──── Face detection ────
        'no_face_detected': 'No face detected in the image. Please upload an image with a clear face.',
        'no_face_registered': 'No face registered for student {student_id}. Please register face first.',
        'no_face_registered_short': 'No face registered',
        'face_registered_short': 'Face registered',

        # ──── Face verification ────
        'face_verified': 'Face verified successfully for student {student_id}',
        'face_not_matched': 'Face does not match registered face for student {student_id}',

        # ──── Face registration ────
        'face_registered': 'Face registered successfully for student {student_id}',
        'face_encoding_updated': 'Face encoding updated successfully for student {student_id}',
        'face_encoding_deleted': 'Face encoding deleted successfully for student {student_id}',
        'no_face_encoding_found': 'No face encoding found for student {student_id}',

        # ──── Batch detection ────
        'no_faces_detected_batch': 'No faces detected in the image',
        'faces_detected_matched': 'Detected {num_faces} face(s), matched {num_matches} student(s)',
        'no_faces_detected_try': 'No faces detected. Try: better lighting, higher resolution, or different angle.',
        'student_ids_filter_applied': 'Matching restricted to {num_students} student(s) in the target class',

        # ──── Database ────
        'db_connection_error': 'Database connection error: {error}',

        # ──── Encoding validation ────
        'encoding_file_not_exist': 'Encoding file does not exist',
        'encoding_load_failed': 'Failed to load encoding file',
        'no_encoding_in_file': 'No encoding found in file',
        'encoding_not_numpy': 'Encoding is not a numpy array',
        'invalid_encoding_shape': 'Invalid encoding shape: {shape}, expected (128,)',
        'validation_error': 'Validation error: {error}',
    },
    'ar': {
        # ──── Student lookup ────
        'student_not_found': 'الطالب برقم {student_id} غير موجود',

        # ──── Face detection ────
        'no_face_detected': 'لم يتم اكتشاف وجه في الصورة. يرجى رفع صورة بوجه واضح.',
        'no_face_registered': 'لا وجه مسجل للطالب {student_id}. يرجى تسجيل الوجه أولاً.',
        'no_face_registered_short': 'لا وجه مسجل',
        'face_registered_short': 'الوجه مسجل',

        # ──── Face verification ────
        'face_verified': 'تم التحقق من الوجه بنجاح للطالب {student_id}',
        'face_not_matched': 'الوجه لا يطابق الوجه المسجل للطالب {student_id}',

        # ──── Face registration ────
        'face_registered': 'تم تسجيل الوجه بنجاح للطالب {student_id}',
        'face_encoding_updated': 'تم تحديث ترميز الوجه بنجاح للطالب {student_id}',
        'face_encoding_deleted': 'تم حذف ترميز الوجه بنجاح للطالب {student_id}',
        'no_face_encoding_found': 'لم يتم العثور على ترميز وجه للطالب {student_id}',

        # ──── Batch detection ────
        'no_faces_detected_batch': 'لم يتم اكتشاف وجوه في الصورة',
        'faces_detected_matched': 'تم اكتشاف {num_faces} وجه(وجوه)، ومطابقة {num_matches} طالب(طلاب)',
        'no_faces_detected_try': 'لم يتم اكتشاف وجوه. حاول: إضاءة أفضل، دقة أعلى، أو زاوية مختلفة.',
        'student_ids_filter_applied': 'المطابقة مقتصرة على {num_students} طالب(طلاب) في الفصل المستهدف',

        # ──── Database ────
        'db_connection_error': 'خطأ في اتصال قاعدة البيانات: {error}',

        # ──── Encoding validation ────
        'encoding_file_not_exist': 'ملف الترميز غير موجود',
        'encoding_load_failed': 'فشل تحميل ملف الترميز',
        'no_encoding_in_file': 'لم يتم العثور على ترميز في الملف',
        'encoding_not_numpy': 'الترميز ليس مصفوفة numpy',
        'invalid_encoding_shape': 'شكل الترميز غير صالح: {shape}, المتوقع (128,)',
        'validation_error': 'خطأ في التحقق: {error}',
    }
}

# Supported language codes
SUPPORTED_LANGS = list(TRANSLATIONS.keys())


def get_message(key: str, lang: str = 'en', **kwargs) -> str:
    """
    Retrieve a localized message by key and language code.

    Args:
        key: Message key (e.g., 'student_not_found')
        lang: Language code ('en' or 'ar'). Falls back to 'en' if unsupported.
        **kwargs: Format parameters to inject into the message string
                  (e.g., student_id='STU001', error='timeout')

    Returns:
        Localized and formatted message string.
    """
    lang = lang if lang in SUPPORTED_LANGS else 'en'
    msg = TRANSLATIONS[lang].get(key, TRANSLATIONS['en'].get(key, key))
    return msg.format(**kwargs) if kwargs else msg


def resolve_lang(request) -> str:
    """
    Extract language code from a FastAPI Request object.

    Checks the Accept-Language header first, then falls back to 'en'.

    Args:
        request: FastAPI Request object

    Returns:
        Two-letter language code ('en' or 'ar')
    """
    accept = request.headers.get('accept-language', 'en')
    # Take the first language from the header, strip to 2 chars
    lang = accept.split(',')[0].strip()[:2]
    return lang if lang in SUPPORTED_LANGS else 'en'