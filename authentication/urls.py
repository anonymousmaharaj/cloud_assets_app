"""Endpoints for Auth application."""

from authentication import views
from django.urls import path

# TODO: Fix upload_file path.
urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register')
]
