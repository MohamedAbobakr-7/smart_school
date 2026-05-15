"""
URL configuration for smartSchool project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('students.urls')),
    path('api/', include('teachers.urls')),
    path('api/', include('parents.urls')),
    path('api/', include('subjects.urls')),
    path('api/', include('classes.urls')),
    path('api/', include('attendance.urls')),
    path('api/', include('exams.urls')),
    path('api/', include('reports.urls')),
    path('api/', include('videos.urls')),
    path('api/', include('notifications.urls')),
    path('api/', include('chatbot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
