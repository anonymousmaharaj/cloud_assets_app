"""Endpoints for Assets application."""

from assets.views import health_check, show_page, user_upload_file

from django.urls import path

urlpatterns = [
    path('api/health_check/', health_check),
    path('', show_page, name='root_page'),
    path('upload_file/', user_upload_file, name='upload_file')
]
