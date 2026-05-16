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
MSG_INVALID_ROLE = _('Invalid role parameter.')
MSG_DASHBOARD_ERROR = _('Dashboard error: {error}')

# ──── Students ────
MSG_STUDENT_ID_GENERATED = _('Successfully generated IDs for {count} student(s).')
MSG_ALL_STUDENTS_HAVE_IDS = _('All students already have IDs. Nothing to update.')
MSG_NO_IMAGE_PROVIDED = _('No image file provided. Send the image as "photo" field.')
MSG_INVALID_FILE_TYPE = _('Invalid file type: {content_type}. Please upload a JPEG or PNG image.')
MSG_FACE_REGISTRATION_FAILED = _('Face registration failed.')
MSG_FACE_REGISTERED_SUCCESS = _('Face registered successfully.')
MSG_PHOTO_SAVED_NO_ID = _(
    'Photo saved. After the student has a Student ID, open Edit and save again '
    '(or re-upload the photo) to register the face for attendance.'
)
MSG_PHOTO_SAVED_SERVICE_UNAVAILABLE = _(
    'Photo saved but face recognition service is unavailable. '
    'Start the service and retry.'
)
MSG_INVALID_DATE_FORMAT = _('Invalid date format. Use YYYY-MM-DD.')

# ──── Attendance ────
MSG_INSTRUCTOR_ONLY = _('Only instructors can process classroom images.')
MSG_SESSION_ID_REQUIRED = _('session_id is required.')
MSG_IMAGE_FILE_REQUIRED = _('image file is required.')
MSG_ACTIVE_SESSION_NOT_FOUND = _('Active session {session_id} not found.')
MSG_ONLY_OWN_SESSIONS = _('You can only process your own sessions.')
MSG_FACE_DETECTION_FAILED = _('Face detection failed.')
MSG_PROCESSING_RESULT = _('Processed {faces} face(s), updated {records} attendance record(s).')
MSG_DUPLICATE_ACTIVE_SESSION = _(
    'An active session for "{class_name}" already exists today '
    '(ID: {session_id}). Complete or cancel it first.'
)
MSG_SESSION_NOT_ACTIVE = _('Session is not active ({status}).')
MSG_SESSION_COMPLETED = _('Session completed.')
MSG_SESSION_CANCELLED = _('Session cancelled.')
MSG_ATTENDANCE_DUPLICATE = _('Attendance record already exists for this student on {date}.')
MSG_ATTENDANCE_DUPLICATE_MODEL = _('Attendance record already exists for {student_id} on {date}.')
MSG_FACE_VERIFIED = _('Face verified successfully for student {student_id}.')
MSG_STUDENT_CLASS_MISMATCH = _(
    'Student {student_id} was recognised but belongs to class '
    '{matched_class}, not the session class {session_class}. '
    'Attendance not marked.'
)

# ──── Exams ────
MSG_OPTIONS_MUST_BE_LIST = _('Options must be a list/array.')
MSG_MIN_OPTIONS = _('At least 2 options are required for MCQ.')
MSG_CORRECT_ANSWER_INDEX = _('correct_answer index ({index}) must be less than number of options ({count}).')
MSG_GRADE_DUPLICATE = _('Grade already exists for this student and exam.')
MSG_SCORE_EXCEEDS_TOTAL = _('Score ({score}) cannot exceed total questions ({total_questions}).')

# ──── Classes ────
MSG_CLASS_NAME_REQUIRED = _('Class name is required.')
MSG_CLASS_ALREADY_EXISTS = _('A class "{label}" already exists.')

# ──── Chatbot ────
MSG_MESSAGE_REQUIRED = _('Message is required.')
MSG_MESSAGE_TOO_LONG = _('Message too long (max {max} characters).')

# ──── Notifications ────
# (add as needed)

# ──── Reports ────
MSG_NO_TEACHER_PROFILE = _('No teacher profile.')
MSG_ADMIN_ALL_TEACHERS_ONLY = _('Only administrators can set all_teachers.')
MSG_ADMIN_SCHOOL_REPORTS_ONLY = _('Only administrators can generate school-wide reports.')
MSG_TEACHER_PROFILE_REQUIRED = _('Teacher profile required.')
MSG_PDF_NOT_GENERATED = _('PDF not generated for this report.')
MSG_PDF_MISSING_ON_DISK = _('PDF file missing on disk.')
MSG_WEEK_PARAMS_BOTH_OR_NONE = _('Provide both week_start and week_end, or neither for default previous week.')
MSG_WEEK_END_AFTER_START = _('week_end must be on or after week_start.')

# ──── Videos ────
MSG_NO_FILE = _('No file.')
MSG_FILE_MISSING = _('File missing.')
MSG_EDIT_OWN_VIDEOS_ONLY = _('You can only edit your own videos.')
MSG_DELETE_OWN_VIDEOS_ONLY = _('You can only delete your own videos.')
MSG_STUDENT_SYNC_ONLY = _('Only students can sync watch progress.')

# ──── API Root ────
MSG_API_ROOT = _('Smart School Backend API')