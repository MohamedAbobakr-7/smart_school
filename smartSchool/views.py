"""
Root views for smartSchool project
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from smartSchool.messages import MSG_API_ROOT


@require_http_methods(["GET"])
def api_root(request):
    """
    API root endpoint that lists all available endpoints
    """
    base_url = request.build_absolute_uri('/api/')
    
    return JsonResponse({
        'message': str(MSG_API_ROOT),
        'version': '1.0.0',
        'endpoints': {
            'authentication': {
                'login': f'{base_url}auth/login/',
                'refresh': f'{base_url}auth/refresh/',
            },
            'users': f'{base_url}users/',
            'students': f'{base_url}students/',
            'teachers': f'{base_url}teachers/',
            'parents': f'{base_url}parents/',
            'subjects': f'{base_url}subjects/',
            'attendance': {
                'attendance': f'{base_url}attendance/',
                'sessions': f'{base_url}attendance-sessions/',
                'process_classroom_image': f'{base_url}attendance/process-classroom-image/',
            },
            'exams': {
                'exams': f'{base_url}exams/',
                'questions': f'{base_url}questions/',
                'grades': f'{base_url}grades/',
            },
            'reports': f'{base_url}reports/',
            'weekly_reports': {
                'list': f'{base_url}weekly-reports/',
                'dashboard': f'{base_url}weekly-reports/dashboard/',
                'generate': f'{base_url}weekly-reports/generate/',
            },
            'videos': {
                'videos': f'{base_url}videos/',
                'stream': f'{base_url}videos/{{id}}/stream/',
                'video_progress': f'{base_url}video-progress/',
                'video_progress_sync': f'{base_url}video-progress/sync/',
            },
            'notifications': {
                'list': f'{base_url}notifications/',
                'preferences': f'{base_url}notification-preferences/',
                'websocket': 'ws://<host>/ws/notifications/?access=<JWT>',
            },
            'admin': '/admin/',
        },
        'documentation': {
            'automated_attendance': '/TESTING_AUTOMATED_ATTENDANCE.md',
            'workflow': '/AUTOMATED_ATTENDANCE_WORKFLOW.md',
        }
    })





